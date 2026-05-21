import datetime
from html.parser import HTMLParser
from pathlib import Path

from marko import Markdown
from marko.block import Heading

from ..stage import Stage
from ..tree import TreeSpan
from .utils import (
    add_heading_anchors,
    get_raw_content,
)


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
        # set basic metadata items from `stat`
        stat_data = (
            tree.root_directory / tree.leaves["initial_path"][leaf_uuid]
        ).stat()
        tree.leaves["metadata"][leaf_uuid].initial_filesize = stat_data.st_size
        tree.leaves["metadata"][leaf_uuid].modification_time = (
            datetime.datetime.fromtimestamp(
                stat_data.st_mtime, tz=datetime.UTC
            ).isoformat()
        )

        input_path: Path = tree.abs_write_path(leaf_uuid)
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
        doc = add_heading_anchors(md.parse(raw_data))

        # extract title
        # Getting first element, and testing if it's a heading
        heading = doc.children[0]
        if isinstance(heading, Heading) and (heading.level == 1):
            tree.leaves["metadata"][leaf_uuid].title = heading.children[0].children

        # extract TOC
        flat_toc = [
            {"id": child.id, "text": get_raw_content(child), "level": child.level}
            for child in doc.children
            if isinstance(child, Heading)
        ]
        tree.leaves["metadata"][leaf_uuid].table_of_contents = render_toc(
            flat_toc, mindepth=2
        )


def render_toc(
    headings: list[dict[str, str | int]], mindepth: int = 1, maxdepth: int | None = None
) -> str:
    """Render a set of dictionaries as a nested <ul>

    Modification of marko's TocRenderMixin.render_toc
    """
    first_level = None
    last_level = None
    rv = []

    opening, closing = '<ul class="toc-level-{level}">\n', "</ul>\n"
    item_format = '<li><a href="#{slug}">{text}</a></li>'

    for heading in headings:
        level, slug, text = heading["level"], heading["id"], heading["text"]

        if level < mindepth or (maxdepth is not None and level > maxdepth):
            continue

        # initialize
        if first_level is None:
            first_level = mindepth
            last_level = level
            rv.append(opening.format(level=level))

        # step in
        if last_level == level - 1:
            rv.append("\t" * last_level + opening.format(level=level))
            last_level = level

        # step out
        while last_level > level:
            rv.append("\t" * level + closing)
            last_level -= 1
        rv.append("\t" * level + item_format.format(slug=slug, text=text) + "\n")

    if first_level is None or last_level is None:
        return ""

    for _ in range(first_level, last_level + 1):
        rv.append(closing)

    return "".join(rv).strip()
