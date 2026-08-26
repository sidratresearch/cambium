"""Cambium utility functions."""

import logging
import os
import re
from pathlib import Path

logger = logging.getLogger(__name__)


def convert_glob_string_to_regex(glob_string: str) -> str:
    """Convert glob string to regex string, escaping appropriate characters."""
    main_segment = re.escape(glob_string).replace(r"\*", ".*")

    return f"^{main_segment}$" + "|" + f"\\/{main_segment}$"


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
            result["globs"].append(convert_glob_string_to_regex(entry))
        elif entry[0] == "/":
            result["paths"].append(entry)
        elif "/" in entry:
            result["paths"].append("/" + entry)
        else:
            result["names"].append(entry)
    return result


def path_matches_patterns(
    path: Path, patterns: dict[str, list[str]], check_extensions: bool = True
) -> bool:
    """Check if a path matches any item in `patterns`.

    Where `patterns` is formatted as the output from `config.sort_user_paths`.
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
