"""Path-related Cambium utility functions."""

from __future__ import annotations

import logging
import os
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal

if TYPE_CHECKING:
    from ..tree import TreeSpan

logger = logging.getLogger(__name__)


def abs_leaf_path(tree: TreeSpan, leaf_uuid: str) -> Path:
    """Get the absolute path to a safe writeable location for a leaf.

    If called during the tree hooks, this will *not* create that path, as the
    filesystem is not considered writeable at that time.
    """
    path = tree.config.tmp_dir / tree.leaves["latest_path"][leaf_uuid]
    if tree.filesystem_writeable:
        path.parent.mkdir(parents=True, exist_ok=True)
    return path


def abs_static_stage_path(tree: TreeSpan, stage_name: str) -> Path:
    """Get the absolute path to a stage-specific directory in build/static.

    If called during the tree hooks, this will *not* create that directory, as the
    filesystem is not considered writeable at that time.
    """
    path = tree.build_directory / "static" / "_cambium" / stage_name
    if tree.filesystem_writeable:
        path.mkdir(parents=True, exist_ok=True)
    return path.absolute()


def leaf_final_paths(tree: TreeSpan) -> list[Path]:
    """Up-to-date listing of the final paths for all leaves."""
    return [tree.leaves["final_path"][uuid] for uuid in tree.leaves["uuids"]]


def get_leaf_from_path(
    tree: TreeSpan, path: Path, path_type: Literal["initial_path", "final_path"]
) -> str:
    """Fetch the leaf UUID associated with a certain path."""
    tree._validate_leaf_path(path)
    uuids = [u for u in tree.leaves["uuids"] if tree.leaves[path_type][u] == path]

    if len(uuids) == 0:
        raise RuntimeError(f"No leaves found with {path_type.replace('_',' ')}={path}.")
    if len(uuids) > 1:
        raise RuntimeError(
            f"Multiple leaves found with {path_type.replace('_',' ')}={path}."
        )

    return uuids[0]


def resolve_internal_path(
    link: Path, parent_directory: Path, build_directory: Path
) -> Path:
    """Resolve internal paths as they may appear in user files.

    For "../a.html" located in "[root]/b/c.html", this returns "a.html"
    """
    full = (build_directory / parent_directory / link).resolve()
    build_abs = build_directory.resolve()
    try:
        return full.relative_to(build_abs)
    except ValueError:
        # definitionally both paths will be absolute
        # so the only option is full isn't within build
        raise RuntimeError(
            f"Error resolving internal link `{link}`, perhaps this file is outside the root directory?"
        )


def get_relative_path_modifier(final_path: Path) -> str:
    """String to prepend to a path to get from the path up to build."""
    modifier = "../" * len(final_path.parent.parents)
    if sys.platform == "win32":
        return modifier.replace("/", "\\")
    return modifier


def path_matches_patterns(
    path: Path, patterns: dict[str, list[str]], check_extensions: bool = True
) -> bool:
    """Check if a path matches any item in `patterns`.

    Where `patterns` is formatted as the output from `sort_user_paths()`.
    """
    if f"/{path}" in patterns["paths"]:
        return True

    if path.name in patterns["names"]:
        return True

    if (
        check_extensions
        and "extensions" in patterns
        and path.suffix[1:].lower() in patterns["extensions"]
    ):
        return True

    return any(re.match(regex, str(path)) for regex in patterns["globs"])


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

        # filter out `static`
        if (current_root == ".") and ("static" in directories):
            logger.debug("Ignoring top level directory `static`")
            directories.remove("static")

        remove_directories, remove_files = [], []

        # run user filters
        root_path = Path(current_root)
        for d in directories:
            if path_matches_patterns(root_path / d, ignore_lists):
                remove_directories.append(d)
                logger.debug(f"Ignoring directory '{root_path/d}'")
        for f in files:
            if path_matches_patterns(root_path / f, ignore_lists):
                remove_files.append(f)
                logger.debug(f"Ignoring file '{root_path/f}'")

        # apply user filters
        for d in remove_directories:
            directories.remove(d)
        for f in remove_files:
            files.remove(f)

        # save dirs to list
        for d in directories:
            directories_in_build.append(Path(f"{current_root}/{d}".removeprefix("./")))

        # store files to make leaves from
        for f in files:
            path = Path(f"{current_root}/{f}".removeprefix("./"))
            leaf_paths.append(path)

    return directories_in_build, leaf_paths


def sort_user_paths(path_strings: list[str]) -> dict[str, list[str]]:
    """Sort user-provided path strings into globs/paths/names.

    `bar.txt` should be considered a name and match both `/bar.txt` and `/foo/bar.txt`

    `/bar.txt` should be considered a path, and *only* match against `/bar.txt`

    `foo/bar.txt` should be considered a path and *only* match against `/foo/bar.txt`,
    *not* `/baz/foo/bar.txt`
    """
    result = {"globs": [], "paths": [], "names": []}
    for entry in path_strings:

        if entry[-1] == "/":
            entry = entry[:-1]

        if "*" in entry:
            result["globs"].append(_convert_glob_string_to_regex(entry))
        elif entry[0] == "/":
            result["paths"].append(entry)
        elif "/" in entry:
            result["paths"].append("/" + entry)
        else:
            result["names"].append(entry)
    return result


def _convert_glob_string_to_regex(glob_string: str) -> str:
    """Convert glob string to regex string, escaping appropriate characters."""
    main_segment = re.escape(glob_string).replace(r"\*", ".*")

    return f"^{main_segment}$" + "|" + f"\\/{main_segment}$"


def _nested_dict_set(
    dictionary: dict[Any, Any], keys: list[Any], value: Any, intermediate: Any
) -> None:
    """Recurse down a dictionary to set a new value."""
    if len(keys) == 1:
        dictionary[keys[0]] = value
        return
    if not dictionary[keys[0]]:
        dictionary[keys[0]] = intermediate
    _nested_dict_set(dictionary[keys[0]], keys[1:], value, intermediate)


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
        _nested_dict_set(tree, keys, node(), node())

    for f in sorted(files):
        keys = [p + "/" for p in f.parts[:-1]] + [f.name]
        _nested_dict_set(tree, keys, None, {})

    return tree


def is_valid_index_html(path: Path) -> bool:
    """Check if a path matches `index.html` or `index.htm` (case-sensitive)."""
    return path.name in ("index.html", "index.htm")


def absolute_to_relative_path(destination: str, tree: TreeSpan) -> str | None:
    """Convert an absolute path `/blah/index.html` to one relative to the root dir."""
    subpath = tree.config.hosting["subpath"]

    # explicit no subpath
    if subpath == "":
        return destination[1:]

    # subpath undefined
    if subpath is None:
        logger.debug(
            f"Not resolving absolute link to {destination} because `subpath` is not set in config."
        )
        return

    # subpath is defined
    if destination.startswith(f"/{subpath}/"):
        return destination.removeprefix(f"/{subpath}/")
