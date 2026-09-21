"""Non-specific utility functions."""

from __future__ import annotations

import logging
import re
import urllib
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING, Literal, TypeVar

from jinja2 import Environment, FileSystemLoader

from .path_utils import (
    absolute_to_relative_path,
    get_leaf_from_path,
    resolve_internal_path,
)

if TYPE_CHECKING:
    from ..tree import TreeSpan

logger = logging.getLogger(__name__)

T = TypeVar("T")
"""Generic class type, can be removed for Python 3.12."""


def apply_to_leaves(tree: TreeSpan, function: Callable[[str, TreeSpan], None]) -> None:
    """Generic method to apply some function across all leaves.

    If we support multithreading for some operations, this is where it will happen
    Which means `function` should be thread-safe
    """
    for leaf_uuid in tree.leaves["uuids"]:
        function(leaf_uuid, tree)


def is_external_link(dest: str) -> bool:
    """Check if a link points to an external URL."""
    return any(dest.startswith(prefix) for prefix in ["http:", "https:", "www."])


def split_respecting_quotes(string: str, split_char: str) -> list[str]:
    """Split `string` on every `split_char`, unless double quotes are used.

    Double quotes can be escaped with a single backslash.
    https://stackoverflow.com/a/16710842
    """
    pattern = "(?:[^" + split_char + r'"]|"(?:\.|[^"])*")+'
    return re.findall(pattern, string)


def make_jinja_environment(tree: TreeSpan) -> Environment:
    """Create a new Jinja Environment with access to the loaded template directories.

    Template directories include
    - .cambium/theme/templates
    - [user-selected theme]/templates
    - root theme templates
    - [stage directory]/includes/templates

    See config.py for details
    """
    return Environment(
        loader=FileSystemLoader(tree.config.template_directories),
        lstrip_blocks=True,
        trim_blocks=True,  # stops Jinja lines from being replaced with newlines
        # if not enabled, Marko doesn't recognize the table as being a single HTMLBlock
    )


def get_all_subclasses(cls: T) -> set[T]:
    """Fetch all subclasses of `cls` (not just immediate subclasses)."""
    result = set()
    for subclass in cls.__subclasses__():
        result.add(subclass)
        result.update(get_all_subclasses(subclass))
    return result


def _get_path_from_href(
    destination: str, file_parent_directory: Path, tree: TreeSpan
) -> Path:
    """Convert a string which references another file into a root-relative Path."""
    # HACK? "../index.html" and "..\index.html" become "..%5Cindex.html" when
    # parsing UTF-8 files on Windows. So just convert all of them to "/"
    destination = destination.replace("%5C", "/")
    resolved = resolve_internal_path(
        destination, file_parent_directory, tree.build_directory
    )
    if "#" in resolved.name:
        resolved = resolved.with_name(resolved.name[: resolved.name.index("#")])
    return Path(urllib.parse.unquote_plus(str(resolved)))


def get_href_destination(
    href: str,
    href_type: Literal["initial_path", "final_path"],
    source_uuid: str,
    tree: TreeSpan,
) -> tuple[Literal["external", "static", "unknown absolute", "internal"], str | None]:
    """Identify where a given href-like string leads."""
    href = href.split("#", maxsplit=1)[0]

    if href == "":
        return "internal", source_uuid

    if is_external_link(href):
        return "external", None

    destination = href
    if destination.startswith("/"):
        destination = absolute_to_relative_path(destination, tree)
        if destination is None:
            return "unknown absolute", None

    # go from link contents to a Path
    source_directory = tree.leaves["final_path"][source_uuid].parent
    resolved = _get_path_from_href(destination, source_directory, tree)

    # skip links to static files
    if len(resolved.parts) > 0 and resolved.parts[0] == "static":
        return "static", None

    try:
        uuid = get_leaf_from_path(tree, resolved, href_type)
    except RuntimeError as e:
        logger.debug(
            f"Resolved path {resolved} could not be identified as a path of type {href_type}. Error: {e}"
        )
        uuid = None
    return "internal", uuid
