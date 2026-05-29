"""Cambium stage to ensure all directories contain index.html files."""

import logging
from pathlib import Path

from ..stage import Stage
from ..tree import TreeSpan

logger = logging.getLogger(__name__)


class AddPlaceholderIndex(Stage):

    def tree_hook(self, tree: TreeSpan) -> None:
        final_paths = [tree.leaves["final_path"][uuid] for uuid in tree.leaves["uuids"]]

        for directory in [Path(), *tree.directories_in_build]:
            index_file = directory / "index.html"
            if index_file not in final_paths:
                self._create_index_leaf(directory, tree)
                logger.debug(f"Added index file for directory {directory}")

    def _create_index_leaf(self, directory: Path, tree: TreeSpan) -> None:
        # TODO: figure out what to do about this
        source_path = Path(".cambium/AddPlaceholderIndex/index.html")

        uuid = tree.add_leaf(
            directory, latest_path=source_path, final_path=directory / "index.html"
        )

        tree.abs_leaf_path(uuid).write_text("")
