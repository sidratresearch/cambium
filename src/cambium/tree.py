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
from collections import deque
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
    directories_in_build: list[Path] = []

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
        self._walk_directory_tree()
        if len(self.leaves["uuids"]) == 0:
            logger.warning("Collected 0 files.")
        else:
            logger.info(f"Collected {len(self.leaves['uuids'])} files.")

        # TODO: error collection for leaf generation
        # if there are errors in initial leaf generation, raise them now

        self._check_disk_space()
        self._apply_tree_hooks()
        self._init_tmp_files()

    # ----------------------------------------------------------------#
    #                    __init__ helper functions                    #
    # ----------------------------------------------------------------#

    def _walk_directory_tree(self) -> None:
        """Find all files/directories in the root that Cambium cares about."""
        logger.debug("Discovering files to process")
        for current_root, directories, files in os.walk(
            self.root_directory, topdown=True
        ):
            # current_root: string starting w ./ (except on first loop, where it's ".")
            # directories: list of strings, not ending with /
            # files: list of strings

            if (current_root == ".") and ("static" in directories):
                logger.debug("Ignoring top level directory `static`")
                directories.remove("static")

            # filter by absolute path
            for absolute_ignore in self.config.ignore_lists["paths"]:
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
            for name in self.config.ignore_lists["names"]:
                if name in directories:
                    directories.remove(name)
                    logger.debug(f"Ignoring directory '{d}', removed by name")
                if name in files:
                    files.remove(name)
                    logger.debug(f"Ignoring file '{f}', removed by name")

            # filter by glob
            for pattern in self.config.ignore_lists["globs"]:
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
            for extension in self.config.ignore_lists["extensions"]:
                remove_files = [f for f in files if f.endswith(f".{extension}")]
                for f in remove_files:
                    files.remove(f)
                    logger.debug(f"Ignoring file '{f}', removed by extension")

            # save dirs to list
            for d in directories:
                self.directories_in_build.append(
                    Path(f"{current_root}/{d}".removeprefix("./"))
                )

            # assign UUIDs to files
            for f in files:
                path = Path(f"{current_root}/{f}".removeprefix("./"))
                self.add_leaf(path)

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
            leaf_bytes += self.leaves["initial_path"][uuid].stat().st_size
        for static_directory in [
            self.root_directory / "static",
            *self.config.ordered_theme_directories,
        ]:
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
            self._check_leaf_collisions()

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

    # ----------------------------------------------------------------#
    #                     stage helper functions                     #
    # ----------------------------------------------------------------#

    def add_leaf(
        self,
        initial_path: Path,
        final_path: Path | None = None,
        latest_path: Path | None = None,
    ) -> str:
        """Add a new leaf to the tree."""
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
        path_type: Literal["latest"] | Literal["final"],
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
        if path_type == "final":
            self._check_leaf_collisions()

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
        """Get the absolute path to a stage-specific directory in build/static."""
        path = self.build_directory / "static" / "_cambium" / stage_name
        path.mkdir(parents=True, exist_ok=True)
        return path.absolute()

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

        # create _build and subdirs - commented out because stages are writing to static
        # if self.build_directory.exists():
        #     shutil.rmtree(self.build_directory)
        self.build_directory.mkdir(exist_ok=True)
        for directory in self.directories_in_build:
            (self.build_directory / directory).mkdir(exist_ok=True)

        # move files from tmp to build
        for leaf_uuid in self.leaves["uuids"]:
            from_path = self.config.tmp_dir / self.leaves["latest_path"][leaf_uuid]
            to_path = self.build_directory / self.leaves["final_path"][leaf_uuid]
            logger.debug(f"Finalize: Copying {from_path}->{to_path}")
            shutil.copy(from_path, to_path)

        # copy static files over
        self._copy_static_files_no_overwrite(self.root_directory / "static")
        for directory in self.config.ordered_theme_directories:
            self._copy_static_files_no_overwrite(directory / "static")

    # ----------------------------------------------------------------#
    #                    other internal functions                    #
    # ----------------------------------------------------------------#

    def _check_leaf_collisions(self) -> None:
        """Check for collisions in the final paths of leaves."""
        # cast to string because it's possible to assign to the dict as a string
        # instead of a path, and Path("blah") != "blah"
        final_paths = [
            str(self.leaves["final_path"][uuid]) for uuid in self.leaves["uuids"]
        ]
        if len(final_paths) > len(set(final_paths)):
            raise ValueError("Collision in leaf output paths")

    def _validate_leaf_path(self, path: Any) -> None:
        """Ensure `path` can be assigned to a leaf initial/latest/final path."""
        if not isinstance(path, Path):
            raise ValueError("Use the Path object to set leaf paths")
        if path.is_absolute():
            raise ValueError("Use relative paths for leaves")

    def _copy_static_files_no_overwrite(self, static_directory: Path) -> None:
        """Copy files into _build/static, but don't overwrite existing files."""
        if not static_directory.exists():
            return
        logger.debug(
            f"Copying files from static directory {static_directory} to output. "
            "Existing files in output will not be overwritten."
        )
        for current_root, _, files in os.walk(static_directory):
            for file in files:
                path_from_root = Path(current_root) / file
                path_from_static = path_from_root.relative_to(static_directory)
                final_path = self.build_directory / "static" / path_from_static

                if final_path.exists():
                    logger.debug(
                        f"Skipping {static_directory/path_from_root} because it exists"
                    )
                    continue

                initial_path = static_directory / path_from_static
                final_path.parent.mkdir(parents=True, exist_ok=True)
                logger.debug(f"Copying static file {initial_path} to {final_path}")
                shutil.copy(initial_path, final_path)
