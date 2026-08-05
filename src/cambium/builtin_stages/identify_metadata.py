"""Cambium stage to store metadata of leaves."""

import datetime
import urllib
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

from marko import Markdown
from marko.block import BlankLine, Heading, HTMLBlock
from marko.element import Element
from marko.inline import Link
from slugify import slugify

from ..stage import Stage
from ..tree import TreeSpan
from .utils import (
    fetch_linked_leaf,
    get_raw_content,
)


# HTML Parser
class TitleParser(HTMLParser):
    """Parser to extract the <title> tag."""

    def __init__(self) -> None:
        super().__init__()
        self.in_title = False
        self.title = None

    def handle_starttag(self, tag: str, _) -> None:
        if tag.lower() == "title":
            self.in_title = True

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "title":
            self.in_title = False

    def handle_data(self, data: str) -> None:
        if self.in_title:
            self.title = data.strip()


class IdentifyMetadata(Stage):
    def __init__(self, _: dict[str, Any]) -> None:
        self.requires = []
        self.runs_after = []
        self.runs_before = []

    def tree_hook(self, tree: TreeSpan) -> None:

        # Get all pages that should have metadata extracted
        tree.apply_to_leaves(self._tree_hook_for_leaf)

    def pre_hook(self, leaf_uuid: str, tree: TreeSpan) -> None:
        extract_generic_metadata(leaf_uuid, tree)

        input_path: Path = tree.abs_leaf_path(leaf_uuid)
        input_extension: str = input_path.suffix

        if input_extension in (".md"):
            extract_md_metadata(input_path, leaf_uuid, tree)
        elif input_extension in (".html", ".htm"):
            extract_html_metadata(input_path, leaf_uuid, tree)

    # Utility Functions

    def _tree_hook_for_leaf(self, leaf_uuid: str, tree: TreeSpan) -> None:
        # this tree hook operates on initial paths
        # because those are the files that are read for the actual scraping
        if tree.leaves["initial_path"][leaf_uuid].suffix.lower() not in (
            ".md",
            ".html",
            ".htm",
        ):
            return

        self._register_hook(leaf_uuid, tree, "pre_hooks")


def extract_generic_metadata(leaf_uuid: str, tree: TreeSpan) -> None:
    """Set leaf metadata for anything that applies to all leaves."""
    metadata_obj = tree.leaves["metadata"][leaf_uuid]

    # set a `page_id`
    # TODO: should `cambium-page-` be a stage option or moved into the jinja?
    metadata_obj.page_id = "cambium-page-" + slugify(
        str(tree.leaves["final_path"][leaf_uuid].with_suffix(""))
    )

    # set basic metadata items from `stat`
    initial_path = tree.root_directory / tree.leaves["initial_path"][leaf_uuid]
    if initial_path.exists():
        stat_data = initial_path.stat()
        metadata_obj.initial_filesize = stat_data.st_size
        metadata_obj.modification_time = datetime.datetime.fromtimestamp(
            stat_data.st_mtime, tz=datetime.UTC
        ).isoformat()


def extract_html_metadata(input_path: Path, leaf_uuid: str, tree: TreeSpan) -> None:
    """Set leaf metadata that can be extracted from HTML files."""
    raw_data = input_path.read_text()

    html_parser = TitleParser()
    html_parser.feed(raw_data)

    if html_parser.title is not None:
        tree.leaves["metadata"][leaf_uuid].title = html_parser.title


def extract_md_metadata(input_path: Path, leaf_uuid: str, tree: TreeSpan) -> None:
    """Set leaf metadata that can be extracted from markdown files."""
    raw_data = input_path.read_text()
    md = Markdown()
    doc = md.parse(raw_data)

    if len(doc.children) == 0:
        return

    # extract title
    # skip over html comments and blank lines
    is_comment = (
        lambda element: isinstance(element, HTMLBlock) and len(element.children) == 0
    )
    for element in doc.children:
        if isinstance(element, Heading) and (element.level == 1):
            tree.leaves["metadata"][leaf_uuid].title = get_raw_content(element)
            break
        elif not (is_comment(element) or isinstance(element, BlankLine)):
            break

    # extract links
    parent_directory = tree.leaves["final_path"][leaf_uuid].parent
    linked_leaves = fetch_all_links(doc, parent_directory, tree)
    linked_leaves = list(set(linked_leaves))
    tree.leaves["metadata"][leaf_uuid].links_to = linked_leaves
    for uuid in linked_leaves:
        tree.leaves["metadata"][uuid].linked_from.append(leaf_uuid)


def fetch_all_links(
    element: Element, file_parent_directory: Path, tree: TreeSpan
) -> list[str]:
    """Get the UUIDs for all leaves that this element links to.

    List is not deduplicated.
    """
    linked_leaves: list[str] = []

    if isinstance(element, str):
        return linked_leaves

    if isinstance(element, Link):
        linked = fetch_linked_leaf(element, file_parent_directory, tree)
        if linked is not None:
            linked_leaves.append(linked)

    for child in element.children:
        linked_leaves += fetch_all_links(child, file_parent_directory, tree)

    return linked_leaves
