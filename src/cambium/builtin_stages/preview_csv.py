"""Cambium stage to create preview pages for CSV data."""

import logging
from pathlib import Path
from typing import Any

from ..stage import Stage
from ..tree import TreeSpan

logger = logging.getLogger(__name__)


class PreviewCSV(Stage):
    def _csv_path_updater(self, csv_path: Path) -> Path:
        return csv_path / "index.md"

    def __init__(self, _: dict[str, Any]) -> None:
        self.requires = []
        self.runs_before = ["TransformMarkdown", "IdentifyMetadata"]
        self.runs_after = []

        # store mappings between the preview leaves and the data leaves
        self.csv_to_md = {}
        self.md_to_csv = {}

    def tree_hook(self, tree: TreeSpan) -> None:
        # cast the deque to a list so that we can add new leaves to the end
        # we don't want to re-visit the added leaves anyway
        for leaf_uuid in list(tree.leaves["uuids"]):
            initial_path = tree.leaves["initial_path"][leaf_uuid]
            if initial_path.suffix == ".csv":
                # HACK: technically we should only be doing all this for
                # CSV files *that are linked to by markdown documents*
                self._tree_hook_for_csv(leaf_uuid, initial_path, tree)

    def _tree_hook_for_csv(
        self, md_uuid: str, csv_initial_path: Path, tree: TreeSpan
    ) -> None:
        # change the final path for this leaf to be subfoldered and end in md
        tree.update_leaf_path(md_uuid, "final", self._csv_path_updater)
        tree.update_leaf_path(md_uuid, "latest", self._csv_path_updater)
        self._register_hook(md_uuid, tree, "pre_hooks")

        # create a companion leaf for the new data location
        source_path = Path(f".cambium/{self.__class__.__name__}/{csv_initial_path}")
        csv_uuid = tree.add_leaf(
            source_path, final_path=csv_initial_path / csv_initial_path.name
        )
        self._register_hook(csv_uuid, tree, "pre_hooks")

        self.md_to_csv[md_uuid] = csv_uuid
        self.csv_to_md[csv_uuid] = md_uuid

        logger.info(f"Creating preview page for {csv_initial_path}")

    def pre_hook(self, leaf_uuid: str, tree: TreeSpan) -> None:
        # figure out if this is the index.html
        if leaf_uuid in self.md_to_csv:
            self._pre_hook_md(leaf_uuid, tree)

        # or the csv itself
        else:
            self._pre_hook_csv(leaf_uuid, tree)

    def _pre_hook_md(self, md_uuid: str, tree: TreeSpan) -> None:
        csv_path = tree.leaves["initial_path"][self.md_to_csv[md_uuid]]
        data = self._get_csv_contents(tree, md_uuid=md_uuid)

        preview_content = f"[{csv_path.name}](./{csv_path.name})"
        preview_content += f"\n<table>{data}</table>"
        # Can't have a "go back" link since this file could be linked in multiple places

        tree.abs_leaf_path(md_uuid).write_text(preview_content)

    def _pre_hook_csv(self, csv_uuid: str, tree: TreeSpan) -> None:
        csv_content = self._get_csv_contents(tree, csv_uuid=csv_uuid)
        tree.abs_leaf_path(csv_uuid).write_text(csv_content)

    def _get_csv_contents(
        self, tree: TreeSpan, csv_uuid: str | None = None, md_uuid: str | None = None
    ) -> str:
        """Retrieve the comma-separated-content as a string.

        Note: there is currently no way for a stage to manipulate the content
        before it gets read in here, (e.g., round or sort the data), because
        we're reading from "initial_path" (i.e., from the root directory).
        """
        # the data is actually stored in md_uuid
        if md_uuid is None:
            md_uuid = self.csv_to_md[csv_uuid]
        return tree.leaves["initial_path"][md_uuid].read_text()
