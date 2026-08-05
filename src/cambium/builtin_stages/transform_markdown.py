"""Cambium stage to convert markdown files to HTML."""

import logging
from pathlib import Path
from typing import Any

from marko import Markdown
from marko.block import Heading
from marko.md_renderer import MarkdownRenderer

from ..stage import Stage, StageConfig
from ..tree import TreeSpan
from .utils import (
    add_heading_anchors,
    get_raw_content,
    markdown_to_html,
    rewrite_md_links,
)

logger = logging.getLogger(__name__)


class TransformMarkdownConfig(StageConfig):
    heading_id_prefix: str = ""


class TransformMarkdown(Stage):
    changed_links: list[str] = []

    def __init__(self, config_dict: dict[str, Any]) -> None:
        self.config = TransformMarkdownConfig.model_validate(config_dict)
        self.requires = []
        self.runs_before = []
        self.runs_after = ["IdentifyMetadata"]

    def tree_hook(self, tree: TreeSpan) -> None:
        """Update final path and list of transforms for markdown leaves."""
        tree.apply_to_leaves(self._tree_hook_for_leaf)

    def _update_path(self, path: Path) -> Path:
        """Function-ize the path change."""
        return path.with_suffix(".html")

    def _tree_hook_for_leaf(self, leaf_uuid: str, tree: TreeSpan) -> None:
        """Update final path and list of transforms for a single leaf, if applicable."""
        if tree.leaves["initial_path"][leaf_uuid].suffix.lower() != ".md":
            return

        tree.update_leaf_path(leaf_uuid, "final", self._update_path)
        self._register_hook(leaf_uuid, tree, "pre_hooks")
        self._register_hook(leaf_uuid, tree, "transforms")
        self.changed_links.append(tree.leaves["initial_path"][leaf_uuid])

    def pre_hook(self, leaf_uuid: str, tree: TreeSpan) -> None:
        """Rewrite links to markdown files that will get transformed."""
        self._rewrite_links(leaf_uuid, tree)
        self._extract_table_of_contents(leaf_uuid, tree)

    def _rewrite_links(self, leaf_uuid: str, tree: TreeSpan) -> None:
        latest_path = tree.abs_leaf_path(leaf_uuid)
        marko_object = Markdown(renderer=MarkdownRenderer)
        document = marko_object.parse(latest_path.read_text())

        document = rewrite_md_links(
            document,
            tree.leaves["initial_path"][leaf_uuid].parent,
            self.changed_links,
            tree.build_directory,
        )
        latest_path.write_text(marko_object.render(document))

    def _extract_table_of_contents(self, leaf_uuid: str, tree: TreeSpan) -> None:
        raw_data = tree.abs_leaf_path(leaf_uuid).read_text()
        md = Markdown()
        doc = add_heading_anchors(md.parse(raw_data), self.config.heading_id_prefix)

        flat_toc = [
            {"id": child.id, "text": get_raw_content(child), "level": child.level}
            for child in doc.children
            if isinstance(child, Heading)
        ]
        tree.leaves["metadata"][leaf_uuid].table_of_contents = render_toc(
            flat_toc, mindepth=2
        )

    def transform(self, leaf_uuid: str, tree: TreeSpan) -> None:
        """Use Marko to write an HTML version of a markdown leaf."""
        markdown_path = tree.abs_leaf_path(leaf_uuid)
        tree.update_leaf_path(leaf_uuid, "latest", self._update_path)
        html_path = tree.abs_leaf_path(leaf_uuid)

        markdown = (markdown_path).read_text()
        html = markdown_to_html(markdown, self.config.heading_id_prefix)
        html_path.write_text(html)


def render_toc(
    headings: list[dict[str, str | int]], mindepth: int = 1, maxdepth: int | None = None
) -> str:
    """Render a set of dictionaries as a nested <ul>.

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
