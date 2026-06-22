"""Cambium stage to store metadata of leaves."""

import datetime
from html.parser import HTMLParser
from pathlib import Path

from marko import Markdown
from marko.block import BlankLine, Heading, HTMLBlock
from slugify import slugify

from ..stage import Stage
from ..tree import TreeSpan
from .utils import get_raw_content


# HTML Parser
class TitleParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.in_title = False
        self.title = None

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag.lower() == "title":
            self.in_title = True

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "title":
            self.in_title = False

    def handle_data(self, data: str) -> None:
        if self.in_title:
            self.title = data.strip()


class IdentifyMetadata(Stage):
    def tree_hook(self, tree: TreeSpan) -> None:

        # Get all pages that should have metadata extracted
        tree.apply_to_leaves(self._tree_hook_for_leaf)

    def pre_hook(self, leaf_uuid: str, tree: TreeSpan) -> None:
        self._extract_metadata(leaf_uuid=leaf_uuid, tree=tree)

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

        tree.leaves["hooks"][leaf_uuid]["pre_hooks"].append(self.__class__.__name__)

    def _extract_metadata(self, leaf_uuid: str, tree: TreeSpan) -> None:
        metadata_obj = tree.leaves["metadata"][leaf_uuid]

        # set a `page_id`
        # TODO: should `cambium-page-` be a stage option or moved into the jinja?
        metadata_obj.page_id = "cambium-page-" + slugify(
            str(tree.leaves["final_path"][leaf_uuid].with_suffix(""))
        )

        # set basic metadata items from `stat`
        stat_data = (
            tree.root_directory / tree.leaves["initial_path"][leaf_uuid]
        ).stat()
        metadata_obj.initial_filesize = stat_data.st_size
        metadata_obj.modification_time = datetime.datetime.fromtimestamp(
            stat_data.st_mtime, tz=datetime.UTC
        ).isoformat()

        input_path: Path = tree.abs_leaf_path(leaf_uuid)
        input_extension: str = input_path.suffix

        if input_extension in (".md"):
            self._get_metadata_from_md(input_path, leaf_uuid, tree)
        elif input_extension in (".html", ".htm"):
            self._get_metadata_from_html(input_path, leaf_uuid, tree)

    def _get_metadata_from_html(
        self, input_path: Path, leaf_uuid: str, tree: TreeSpan
    ) -> None:
        raw_data = input_path.read_text()

        html_parser = TitleParser()
        html_parser.feed(raw_data)

        if html_parser.title is not None:
            tree.leaves["metadata"][leaf_uuid].title = html_parser.title

    def _get_metadata_from_md(
        self, input_path: Path, leaf_uuid: str, tree: TreeSpan
    ) -> None:

        raw_data = input_path.read_text()
        md = Markdown()
        doc = md.parse(raw_data)

        if len(doc.children) == 0:
            return

        # extract title
        # skip over html comments and blank lines
        isComment = (
            lambda element: isinstance(element, HTMLBlock)
            and len(element.children) == 0
        )
        for element in doc.children:
            if isinstance(element, Heading) and (element.level == 1):
                tree.leaves["metadata"][leaf_uuid].title = get_raw_content(element)
                break
            elif not (isComment(element) or isinstance(element, BlankLine)):
                break
