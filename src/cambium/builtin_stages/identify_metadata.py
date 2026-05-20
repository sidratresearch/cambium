from html.parser import HTMLParser
from pathlib import Path

from marko import Markdown

from ..stage import Stage
from ..tree import TreeSpan


# HTML Parser
class TitleParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_title = False
        self.title = None

    def handle_starttag(self, tag, attrs):
        if tag.lower() == "title":
            self.in_title = True

    def handle_endtag(self, tag):
        if tag.lower() == "title":
            self.in_title = False

    def handle_data(self, data):
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
        if tree.leaves["latest_path"][leaf_uuid].suffix.lower() not in (
            ".md",
            ".html",
            ".htm",
        ):
            return

        tree.leaves["hooks"][leaf_uuid]["pre_hooks"].append(self.__class__.__name__)

    def _extract_metadata(self, leaf_uuid: str, tree: TreeSpan) -> None:

        input_path: Path = tree.config.tmp_dir / tree.leaves["latest_path"][leaf_uuid]
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

        # Getting first element, and testing if it's a heading
        heading = doc.children[0]
        if heading.level == 1:
            tree.leaves["metadata"][leaf_uuid].title = heading.children[0].children
