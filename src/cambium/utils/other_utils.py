"""Non-specific utility functions."""

from __future__ import annotations

import logging
import re
import urllib
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING, TypeVar

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


def fetch_leaf_from_href(
    destination: str, file_parent_directory: Path, tree: TreeSpan
) -> str | None:
    """Return the UUID of the leaf that a link points to.

    Returns None if the link does not point to a leaf (as identified by initial
    paths), or points to somewhere in the current document.
    """
    if is_external_link(destination):
        return
    if destination.startswith("#"):
        return

    if destination.startswith("/"):
        destination = absolute_to_relative_path(destination, tree)
        if destination is None:
            return

    # go from link contents to a Path
    resolved = resolve_internal_path(
        destination, file_parent_directory, tree.build_directory
    )
    if "#" in resolved.name:
        resolved = resolved.with_name(resolved.name[: resolved.name.index("#")])
    resolved = Path(urllib.parse.unquote_plus(str(resolved)))

    # skip links to static files
    if resolved.parts[0] == "static":
        return

    # skip links to directories
    # TODO: if you link to a directory, should we:
    # fail, warn, warn + return index.html
    # if resolved in tree.directories_in_build:
    #     return
    # breaks link resolution for previews

    try:
        return get_leaf_from_path(tree, resolved, "initial_path")
    except RuntimeError:
        # Previewer stages need to link to the downloadable file by the final path
        return


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
