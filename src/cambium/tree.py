"""Cambium structure for tracking and acting on files."""

from __future__ import annotations

import logging
import re
import typing
from uuid import uuid4

if typing.TYPE_CHECKING:
    from .config import WorkingConfiguration

import os
import shutil
from collections import Counter, defaultdict, deque
from collections.abc import Callable
from pathlib import Path
from typing import Any, Literal, TypedDict

from .metadata import LeafMetadata


class LeafHooks(TypedDict):
    pre_hooks: list[str]
    transforms: list[str]
    post_hooks: list[str]


class Leaves(TypedDict):
    uuids: deque[str]
    initial_path: dict[str, Path]
    latest_path: dict[str, Path]
    final_path: dict[str, Path]
    hooks: LeafHooks
    metadata: dict[str, LeafMetadata]
    failed: dict[str, bool]


logger = logging.getLogger(__name__)


class TreeSpan:
    """
    Primary tracking and controlling class for Cambium.

    `TreeSpan` holds the directory tree and the actions that need to be perfomed,
    and provides the functions to apply those actions.
    """

    # These work as class attr so long as we never have multiple instances of TreeSpan
    root_directory: Path
    build_directory: Path

    def __init__(self, working_config: WorkingConfiguration) -> None:
        self.config: WorkingConfiguration = working_config

        self.root_directory = self.config.root_dir
        self.build_directory = self.config.build_dir

        # TODO: there's not currently anything stopping a stage from setting a leaf path to something that isn't a Path, then when another stage tries to acces .suffix, it breaks
        # maybe using a pydantic model would help?
        self.leaves: Leaves = {
            "uuids": deque(maxlen=self.config.max_leaves),
            # non-uuid dicts don't need to shrink, so long as uuids are up-to-date
            # therefore: never iterate over these
            "initial_path": {},
            "latest_path": {},
            "final_path": {},
            "metadata": {},
            "hooks": {"pre_hooks": [], "transforms": [], "post_hooks": []},
            "failed": {},
        }

        directories_in_build, leaf_paths = walk_directory_tree(
            self.root_directory, self.config.ignore_lists
        )
        self.directories_in_build = directories_in_build

        for path in leaf_paths:
            self.add_leaf(path)

        if len(self.leaves["uuids"]) == 0:
            logger.warning("Collected 0 files.")
        else:
            logger.info(f"Collected {len(self.leaves['uuids'])} files.")

        # TODO: error collection for leaf generation
        # if there are errors in initial leaf generation, raise them now

        self._apply_tree_hooks()
        self._build_final_tree()
        self._check_protected_static_paths()

    # ----------------------------------------------------------------#
    #                    __init__ helper functions                    #
    # ----------------------------------------------------------------#

    def _apply_tree_hooks(self) -> None:
        """Run all tree hooks, passing them the entire tree structure to modify."""
        # initial leaves have input file = output file
        for stage in self.config.stages:
            try:
                logger.debug(f"Running tree_hook for stage {stage}")
                self.config.stage_dict[stage].tree_hook(self)
                # TODO: decide if exception should be raised on first treehook failure (current) or wait
            except Exception as e:
                errormsg = f"Error running tree hook for stage {stage}. "
                logger.error(errormsg + f"Error message: {e}")
                raise e
            self._check_leaf_collisions("final")

    def _build_final_tree(self) -> None:
        """Generate a nested human-readable file structure for the entire output dir."""
        # generate a list of all paths
        all_files = self.leaf_final_paths()
        all_directories = self.directories_in_build.copy()

        for static_source_dir, static_dest_dir in [
            *self.config.static_directories["stage"],
            *self.config.static_directories["user"],
            *self.config.static_directories["theme"],
        ]:
            static_directory = (static_source_dir).absolute()
            directories, files = self._get_static_paths(
                static_directory, static_dest_dir
            )
            all_files += [f[1] for f in files]
            all_directories += directories

        self.filestructure_in_build = make_nested_filetree(all_directories, all_files)

        self._check_protected_build_paths(all_directories, all_files)

    def _check_protected_build_paths(
        self, directories: list[Path], files: list[Path]
    ) -> None:
        """Check expected tree structure against any user-provided protected paths."""
        bad_generated_paths = []

        combined = [
            item
            for sublist in self.config.protected_build_paths.values()
            for item in sublist
        ]
        if len(combined) > 0:
            logger.warning(
                f"Protected build paths do not apply within {self.build_directory}/static/_cambium."
            )

        # filter by absolute path
        for absolute_ignore in self.config.protected_build_paths["paths"]:
            matcher = f".{absolute_ignore}"
            bad_generated_paths += [f"{d}/" for d in directories if f"./{d}" == matcher]
            bad_generated_paths += [f for f in files if f"./{f}" == matcher]

        # filter by name
        for name in self.config.protected_build_paths["names"]:
            bad_generated_paths += [f"{d}/" for d in directories if name in d.parts]
            bad_generated_paths += [f for f in files if name in f.parts]

        # filter by glob
        for pattern in self.config.protected_build_paths["globs"]:
            bad_generated_paths += [
                f"{d}/"
                for d in directories
                if re.match(pattern, f"./{d}".removeprefix("./"))
            ]
            bad_generated_paths += [
                f"{f}/" for f in files if re.match(pattern, f"./{f}".removeprefix("./"))
            ]

        if len(bad_generated_paths) > 0:
            bad_paths_str = ", ".join([str(p) for p in bad_generated_paths])
            logger.error(
                f"Protected build paths prevent the following files/directories from being created in {self.build_directory}: {bad_paths_str}"
            )
            raise RuntimeError

    def _check_protected_static_paths(self) -> None:
        """Enforce that themes can't provide certain files."""
        for source_dir, dest_dir in self.config.static_directories["theme"]:
            theme_static_paths = [
                p[1] for p in self._get_static_paths(source_dir, dest_dir)[1]
            ]
            for path in self.config.user_theme_files:
                if path in theme_static_paths:
                    raise RuntimeError(
                        f"A theme is attempting to write the user-only file {path.name}"
                    )

    # ----------------------------------------------------------------#
    #                     stage helper functions                      #
    # ----------------------------------------------------------------#

    def add_leaf(
        self,
        initial_path: Path,
        final_path: Path | None = None,
        latest_path: Path | None = None,
    ) -> str:
        """Add a new leaf to the tree.

        Note that if you're doing this while iterating through
        tree.leaves["uuids"] you will likely encounter "RuntimeError: deque
        mutated during iteration". If you *don't* want to iterate over
        the new leaves, you can freeze the deque before iteration by doing
        `for leaf_uuid in list(tree.leaves["uuids"])`. If you *do* want to
        include the new leaves, use a while loop instead.
        """
        if len(self.leaves["uuids"]) == self.leaves["uuids"].maxlen:
            raise ValueError("self.leaves will drop items")

        # Validate paths
        self._validate_leaf_path(initial_path)
        if latest_path is None:
            latest_path = initial_path
        else:
            self._validate_leaf_path(latest_path)
        if final_path is None:
            final_path = initial_path
        else:
            self._validate_leaf_path(final_path)

        # create the new leaf
        uuid = str(uuid4())
        self.leaves["uuids"].append(uuid)
        self.leaves["initial_path"][uuid] = initial_path
        self.leaves["latest_path"][uuid] = latest_path
        self.leaves["final_path"][uuid] = final_path
        self.leaves["hooks"][uuid] = {
            "pre_hooks": [],
            "transforms": [],
            "post_hooks": [],
        }
        self.leaves["metadata"][uuid] = LeafMetadata()

        self._check_leaf_collisions("initial")

        self._update_directories_in_build(final_path.parent)

        return uuid

    def apply_to_leaves(self, function: Callable[[str, TreeSpan], None]) -> None:
        """Generic method to apply some function across all leaves.

        If we support multithreading for some operations, this is where it will happen
        Which means `function` should be thread-safe
        """
        for leaf_uuid in self.leaves["uuids"]:
            function(leaf_uuid, self)

    def update_leaf_path(
        self,
        leaf_uuid: str,
        path_type: Literal["latest", "final"],
        updater: Callable[[Path], Path],
    ) -> None:
        """Update the latest or final path of a leaf in a functional manner.

        In some cases it would be useful to return the path, but then it's unclear
        whether we're returning an absolute writable path or something else. So if
        you need to update latest path and then write to it, make two function calls.
        """
        updated = updater(self.leaves[f"{path_type}_path"][leaf_uuid])
        self._validate_leaf_path(updated)
        self.leaves[f"{path_type}_path"][leaf_uuid] = updated
        self._check_leaf_collisions(path_type)

        if path_type == "final":
            self._update_directories_in_build(updated.parent)

    def abs_leaf_path(self, leaf_uuid: str) -> Path:
        """Get the absolute path to a safe writeable location for a leaf.

        Ensures that the directory exists to be written to, which is mostly required
        for "ghost" leaves (e.g., generated index.html files) where the relevant folder
        in the temporary directory may not have been created on tree initialization
        """
        path = self.config.tmp_dir / self.leaves["latest_path"][leaf_uuid]
        path.parent.mkdir(parents=True, exist_ok=True)
        return path

    def abs_static_stage_path(self, stage_name: str) -> Path:
        """Get the absolute path to a stage-specific directory in build/static.

        This directory is *not* guaranteed to exist, and should be created
        *by the requesting stage* at some point after the tree hooks.
        """
        path = self.build_directory / "static" / "_cambium" / stage_name

        return path.absolute()

    def get_leaf_from_path(
        self, path: Path, path_type: Literal["initial_path", "final_path"]
    ) -> str:
        """Fetch the leaf UUID associated with a certain path."""
        self._validate_leaf_path(path)
        uuids = [u for u in self.leaves["uuids"] if self.leaves[path_type][u] == path]

        if len(uuids) == 0:
            raise RuntimeError(
                f"No leaves found with {path_type.replace('_',' ')}={path}."
            )
        if len(uuids) > 1:
            raise RuntimeError(
                f"Multiple leaves found with {path_type.replace('_',' ')}={path}."
            )

        return uuids[0]

    def leaf_final_paths(self) -> list[Path]:
        """Up-to-date listing of the final paths for all leaves."""
        return [self.leaves["final_path"][uuid] for uuid in self.leaves["uuids"]]

    # ----------------------------------------------------------------#
    #                     Main Cambium functions                      #
    # ----------------------------------------------------------------#

    def _apply_hook(
        self,
        hook_type: Literal["pre_hooks"] | Literal["transforms"] | Literal["post_hooks"],
    ) -> None:
        """Apply `hook_type` hooks for all leaves.

        This function has multiple levels of iteration.
        - We work through stages, in the order they appear in the configuration
        - For each stage we:
            - Identify the leaves to run it on
            - Run a hook initialization function
            - Loop through the leaves, running the main hook function on each leaf
            - Run a hook finalization function

        The purpose of the init and final is to support hooks which require a
        long-running context manager.

        If a hook function fails, the remaining hook functions for that Leaf are not
        be run, and an error is raised after all stages have had a chance to run on
        the other leaves.

        Currently error handling is only managed for the main hook function. Errors
        that occur in the initialization/finalization functions, or in the context
        manager itself, are unhandled.
        """
        logger.info(f"Running {hook_type}")
        self.leaves["failed"] = dict.fromkeys(self.leaves["uuids"], False)

        for stage_name, stage_instance in self.config.stage_dict.items():

            # check which leaves we want to run on
            uuids_to_run = self._get_leaves_for_stage_hook(stage_name, hook_type)

            if len(uuids_to_run) == 0:
                continue

            # get the hook functions from the stage
            hook_init = getattr(stage_instance, f"{hook_type[:-1]}_initialize")
            hook_main = getattr(stage_instance, f"{hook_type[:-1]}")
            hook_finalize = getattr(stage_instance, f"{hook_type[:-1]}_finalize")

            logger.debug(f"Running {stage_name} {hook_type[:-1]}_initalize.")
            hook_init(self)

            # run hook for all leaves
            logger.debug(f"Running {stage_name} {hook_type[:-1]}.")
            for uuid in uuids_to_run:
                try:
                    hook_main(uuid, self)
                except Exception as e:
                    if self.config.fail_fast:
                        raise e
                    self._handle_hook_exception(e, uuid, stage_name, hook_type)

            logger.debug(f"Running {stage_name} {hook_type[:-1]}_finalize.")
            hook_finalize(self)

        if any(self.leaves["failed"].values()):
            raise Exception

    def _handle_hook_exception(
        self, exception: Exception, leaf_uuid: str, stage_name: str, hook_type: str
    ) -> None:
        initial_path = self.leaves["initial_path"][leaf_uuid]
        errormsg = (
            f"Error running {hook_type} for stage {stage_name} on file {initial_path}. "
        )
        logger.error(errormsg + f"Error message: {exception}")
        self.leaves["failed"][leaf_uuid] = True

    def _get_leaves_for_stage_hook(self, stage_name: str, hook_type: str) -> list[str]:
        uuids_to_run = []
        for uuid in self.leaves["uuids"]:
            # skip leaves that aren't relevant to this stage
            if stage_name not in self.leaves["hooks"][uuid][hook_type]:
                continue

            # skip failed leaves
            if self.leaves["failed"][uuid]:
                initial_path = self.leaves["initial_path"][uuid]
                warning = f"Skipping stage {stage_name} for file {initial_path} due to previous failure"
                logger.warning(warning)
                continue

            uuids_to_run.append(uuid)

        return uuids_to_run

    def prepare_tree(self) -> None:
        """Preparation steps not taken during dry run."""
        self._check_disk_space()
        self._init_tmp_files()
        self._init_build_directory()

    def apply_pre_hooks(self) -> None:
        """Run pre-hooks for all leaves."""
        self._apply_hook("pre_hooks")

    def transform(self) -> None:
        """Run transform hooks for all leaves."""
        self._apply_hook("transforms")

    def apply_post_hooks(self) -> None:
        """Run post-hooks for all leaves."""
        self._apply_hook("post_hooks")

    def finalize(self) -> None:
        """Copy final leaf versions to build, and do any other cleanup."""
        logger.info("Finalizing output")

        # move files from tmp to build
        for leaf_uuid in self.leaves["uuids"]:
            from_path = self.config.tmp_dir / self.leaves["latest_path"][leaf_uuid]
            to_path = self.build_directory / self.leaves["final_path"][leaf_uuid]
            logger.debug(f"Copying {from_path}->{to_path}")
            shutil.copy(from_path, to_path)

        # copy static files over
        for static_type in ["stage", "theme", "user"]:
            for source_dir, dest_dir in self.config.static_directories[static_type]:
                self._copy_static_files(source_dir, dest_dir)

        # populate "required" static files
        for path in [
            self.build_directory / file for file in self.config.user_theme_files
        ]:
            if not path.exists():
                path.parent.mkdir(exist_ok=True)
                path.write_text("")

    # ----------------------------------------------------------------#
    #                    other internal functions                    #
    # ----------------------------------------------------------------#

    def _check_leaf_collisions(
        self, path_type: Literal["initial", "latest", "final"]
    ) -> None:
        """Check for collisions in the paths of leaves."""
        # cast to string because it's possible to assign to the dict as a string
        # instead of a path, and Path("blah") != "blah"
        paths = [
            str(self.leaves[f"{path_type}_path"][uuid]) for uuid in self.leaves["uuids"]
        ]
        if len(paths) > len(set(paths)):
            counts = Counter(paths)
            multiples = [p for p, c in counts.items() if c > 1]
            raise ValueError(
                f"Collision in leaf {path_type} paths - the following appear multiple times: {multiples}"
            )

    def _validate_leaf_path(self, path: Any) -> None:
        """Ensure `path` can be assigned to a leaf initial/latest/final path."""
        if not isinstance(path, Path):
            raise ValueError("Use the Path object to work with leaf paths")
        if path.is_absolute():
            raise ValueError("Use relative paths for leaves")

    def _update_directories_in_build(self, directory: Path) -> None:
        if directory.is_absolute():
            return

        while directory not in self.directories_in_build and directory != Path():
            self.directories_in_build.append(directory)
            directory = directory.parent

    def _check_disk_space(self) -> None:
        """Check that there is enough free space for both the temp and build dirs."""
        logger.debug("Checking disk space")
        build_location = (
            self.build_directory.absolute().parent
        )  # if build doesn't exist yet, we can't stat it
        build_device = build_location.stat().st_dev
        tmp_device = self.config.tmp_dir.stat().st_dev

        leaf_bytes, static_bytes = 0, 0
        for uuid in self.leaves["uuids"]:
            initial_path = self.root_directory / self.leaves["initial_path"][uuid]
            if not initial_path.exists():
                continue
            leaf_bytes += initial_path.stat().st_size
        for static_in_out_dirs in self.config.static_directories.values():
            for static_directory, _ in static_in_out_dirs:
                for static_file in static_directory.glob("**/*"):
                    static_bytes += static_file.stat().st_size

        safety_factor = 1.5  # require this much extra space for theme, md->HTML, etc.

        if build_device == tmp_device:
            required_bytes = 2 * safety_factor * (leaf_bytes + static_bytes)
            free_bytes = shutil.disk_usage(build_location).free
            logger.debug(f"Requiring {required_bytes/1000} kb of free space")
            if free_bytes < required_bytes:
                logger.error(
                    f"Not enough free space on disk. {required_bytes/1000} kb needed."
                )
                raise RuntimeError
        else:
            # TODO: handle checks for tmp being on a different drive
            # tmp should have safety*leaf bytes
            # build should have safety * (leaf_bytes + static_bytes)
            logger.warning(
                "Temporary storage is located on a different drive from build directory"
            )

    def _init_tmp_files(self) -> None:
        """Copy all leaves into temporary storage at their initial paths.

        Between tree hooks and pre hooks we need to copy all files into a tempdir
        so that pre-hooks and transformers can use latest_path as relative to temp dir.
        """
        logger.info(
            f"Copying {len(self.leaves['uuids'])} source files to temporary storage"
        )
        for directory in self.directories_in_build:
            (self.config.tmp_dir / directory).mkdir()
        for leaf_uuid in self.leaves["uuids"]:
            initial_path = self.leaves["initial_path"][leaf_uuid]
            if not (self.root_directory / initial_path).is_file():
                continue
            shutil.copy(
                self.root_directory / initial_path,
                self.config.tmp_dir / initial_path,
            )

    def _init_build_directory(self) -> None:
        # create _build and subdirs
        if self.build_directory.exists():
            shutil.rmtree(self.build_directory)
        self.build_directory.mkdir()
        for directory in self.directories_in_build:
            (self.build_directory / directory).mkdir()
        (self.build_directory / "static").mkdir()

    def _get_static_paths(
        self, search_directory: Path, output_directory: Path
    ) -> tuple[list[Path], list[tuple[Path, Path]]]:
        """Get a list of files to be copied into build/static.

        Accepts only absolute paths for safety, given that we expect:
        - top-level directories in root
        - sub directories in root/.cambium
        - directories from the installed cambium package
        """
        if not search_directory.is_absolute():
            logger.error(
                f"Only use absolute paths when listing static files. Recieved relative path {search_directory}."
            )
            raise RuntimeError

        static_files, static_subdirectories = [], []

        for current_root, directories, files in os.walk(search_directory):
            for file in files:
                path_from_root = Path(current_root) / file
                path_from_static = path_from_root.relative_to(search_directory)

                initial_path = search_directory / path_from_static
                static_files.append((initial_path, output_directory / path_from_static))

            for directory in directories:
                directory_full = search_directory / current_root / directory
                directory_build = directory_full.relative_to(search_directory)
                static_subdirectories.append(output_directory / directory_build)

        return static_subdirectories, static_files

    def _copy_static_files(self, source_dir: Path, dest_dir: Path) -> None:
        """Copy files into _build/static, and overwrite existing files."""
        logger.debug(
            f"Copying files from `{source_dir}` to output. "
            f"Existing files in {dest_dir} will be overwritten."
        )
        dest_dir = self.build_directory / dest_dir
        source_dir, dest_dir = source_dir.absolute(), dest_dir.absolute()
        if not dest_dir.exists():
            dest_dir.mkdir()

        directories, files = self._get_static_paths(source_dir, dest_dir)

        for directory in directories:
            directory.mkdir(exist_ok=True, parents=True)

        for initial_path, final_path in files:
            logger.debug(f"Copying static file {initial_path} to {final_path}")
            shutil.copy(initial_path, final_path)


def nested_dict_set(
    dictionary: dict[Any, Any], keys: list[Any], value: Any, intermediate: Any
) -> None:
    """Recurse down a dictionary to set a new value."""
    if len(keys) == 1:
        dictionary[keys[0]] = value
        return
    if not dictionary[keys[0]]:
        dictionary[keys[0]] = intermediate
    nested_dict_set(dictionary[keys[0]], keys[1:], value, intermediate)


def make_nested_filetree(
    directories: list[Path], files: list[Path]
) -> defaultdict[str, Any]:
    """Create a nested tree structure from a list of files and directories.

    Explicitly filters out anything in static/_cambium - stages can add leaves
    into that directory which show up in `files`, but not in `directories`.
    """
    node = lambda: defaultdict(node)
    tree = node()

    check_string = str(Path("static/_cambium"))
    skip = lambda path: str(path).startswith(check_string)
    directories = [d for d in directories if not skip(d)]
    files = [f for f in files if not skip(f)]

    for d in sorted(directories):
        keys = [p + "/" for p in d.parts]
        nested_dict_set(tree, keys, node(), node())

    for f in sorted(files):
        keys = [p + "/" for p in f.parts[:-1]] + [f.name]
        nested_dict_set(tree, keys, None, {})

    return tree


def walk_directory_tree(
    root_directory: Path, ignore_lists: dict[str, list[str]] | None
) -> tuple[list[Path], list[Path]]:
    """Find all files/directories in the root that Cambium cares about."""
    logger.debug("Discovering files to process")

    directories_in_build, leaf_paths = [], []
    if ignore_lists is None:
        ignore_lists = {"paths": [], "names": [], "globs": [], "extensions": []}

    for current_root, directories, files in os.walk(root_directory, topdown=True):
        # current_root: string starting w ./ (except on first loop, where it's ".")
        # directories: list of strings, not ending with /
        # files: list of strings

        # handle root_directory not being cwd
        current_root = current_root.replace(str(root_directory), ".")

        if (current_root == ".") and ("static" in directories):
            logger.debug("Ignoring top level directory `static`")
            directories.remove("static")

        # filter by absolute path
        for absolute_ignore in ignore_lists["paths"]:
            matcher = f".{absolute_ignore}"  # add the leading dot
            remove_directories = [
                d for d in directories if f"{current_root}/{d}" == matcher
            ]
            remove_files = [f for f in files if f"{current_root}/{f}" == matcher]
            for d in remove_directories:
                directories.remove(d)
                logger.debug(f"Ignoring directory '{d}', removed by path")
            for f in remove_files:
                files.remove(f)
                logger.debug(f"Ignoring file '{f}', removed by path")

        # filter by name
        for name in ignore_lists["names"]:
            if name in directories:
                directories.remove(name)
                logger.debug(f"Ignoring directory '{d}', removed by name")
            if name in files:
                files.remove(name)
                logger.debug(f"Ignoring file '{f}', removed by name")

        # filter by glob
        for pattern in ignore_lists["globs"]:
            remove_directories = [
                d
                for d in directories
                if re.match(pattern, f"{current_root}/{d}".removeprefix("./"))
            ]
            remove_files = [
                f
                for f in files
                if re.match(pattern, f"{current_root}/{f}".removeprefix("./"))
            ]
            for d in remove_directories:
                directories.remove(d)
                logger.debug(f"Ignoring directory '{d}', removed by glob")

            for f in remove_files:
                files.remove(f)
                logger.debug(f"Ignoring file '{f}', removed by glob")

        # filter files by ext
        for extension in ignore_lists["extensions"]:
            remove_files = [f for f in files if f.endswith(f".{extension}")]
            for f in remove_files:
                files.remove(f)
                logger.debug(f"Ignoring file '{f}', removed by extension")

        # save dirs to list
        for d in directories:
            directories_in_build.append(Path(f"{current_root}/{d}".removeprefix("./")))

        # assign UUIDs to files
        for f in files:
            path = Path(f"{current_root}/{f}".removeprefix("./"))
            leaf_paths.append(path)

    return directories_in_build, leaf_paths
