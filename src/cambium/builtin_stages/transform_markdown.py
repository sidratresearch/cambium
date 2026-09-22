"""Cambium stage to convert markdown files to HTML."""

import logging
from pathlib import Path
from typing import Any

from ..stage import Stage
from ..tree import TreeSpan
from ..utils.md_html_utils import markdown_to_html
from ..utils.other_utils import apply_to_leaves
from ..utils.path_utils import abs_leaf_path

logger = logging.getLogger(__name__)


class TransformMarkdown(Stage):

    def __init__(self, config_dict: dict[str, Any]) -> None:
        super().__init__(config_dict)
        self.requires = ["IdentifyMetadata"]
        self.runs_after = ["IdentifyMetadata"]

    def tree_hook(self, tree: TreeSpan) -> None:
        """Update final path and list of transforms for markdown leaves."""
        apply_to_leaves(tree, self._tree_hook_for_leaf)

    def _update_path(self, path: Path) -> Path:
        """Function-ize the path change."""
        return path.with_suffix(".html")

    def _tree_hook_for_leaf(self, leaf_uuid: str, tree: TreeSpan) -> None:
        """Update final path and list of transforms for a single leaf, if applicable.

        Filter on final path suffix to:
        - catch preview leaves that started as csv and end as md
        - skip anything that starts as md but some other stage has control over
        """
        if tree.leaves["final_path"][leaf_uuid].suffix.lower() != ".md":
            return

        tree.update_leaf_path(leaf_uuid, "final", self._update_path)
        self._register_hook(leaf_uuid, tree, "transforms")

    def transform(self, leaf_uuid: str, tree: TreeSpan) -> None:
        """Use Marko to write an HTML version of a markdown leaf."""
        markdown_path = abs_leaf_path(tree, leaf_uuid)
        tree.update_leaf_path(leaf_uuid, "latest", self._update_path)
        html_path = abs_leaf_path(tree, leaf_uuid)

        final_path = tree.leaves["final_path"][leaf_uuid]
        markdown = (markdown_path).read_text()
        html = markdown_to_html(
            markdown,
            tree=tree,
            leaf_uuid=leaf_uuid,
        )
        html_path.write_text(html)
