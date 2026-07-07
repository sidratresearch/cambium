"""Cambium stage to ensure all directories contain index.html files."""

import logging
import sys
from pathlib import Path
from typing import Any

from ..stage import Stage, StageConfig
from ..tree import TreeSpan

logger = logging.getLogger(__name__)


class EnsureIndexPagesConfig(StageConfig):
    useable_as_index: list[str] = [
        "README.html",
        "readme.html",
    ]  # need this to be yaml-able, so avoid complex regex
    """Priority-ordered list of HTML filenames that can be moved to index.html"""


class EnsureIndexPages(Stage):

    def __init__(self, config_dict: dict[str, Any]) -> None:
        self.requires = []
        # TODO: doesn't technically *require* TransformMarkdown, but if both are enabled, this should be after
        self.config = EnsureIndexPagesConfig.model_validate(config_dict)

        if sys.platform == "win32":
            casefolded = [f.casefold() for f in self.config.useable_as_index]
            casefolded = list(set(casefolded))
            if len(casefolded) < len(self.config.useable_as_index):
                self.config.useable_as_index = casefolded

    def tree_hook(self, tree: TreeSpan) -> None:
        self.directories_added = []
        for directory in [Path(), *tree.directories_in_build]:
            self._get_index_for_dir(directory, tree)
        if len(self.directories_added) > 0:
            dirs = ", ".join([str(p) for p in self.directories_added])
            logger.info(f"Added index files to directories: {dirs}")

    def _get_index_for_dir(self, directory: Path, tree: TreeSpan) -> None:
        """Ensure directory contains a leaf that will be built to index.html."""
        final_paths = tree.leaf_final_paths()
        directory_has_index = directory / "index.html" in final_paths
        index_path_options = [directory / p for p in self.config.useable_as_index]
        option_existence = [p in final_paths for p in index_path_options]

        # cases where no readme files exist
        if not any(option_existence):
            if not directory_has_index:
                self._create_index_leaf(directory, tree)
                logger.debug(f"Added index file for directory {directory}")
                self.directories_added.append(directory)
            return

        # cases where one readme file exists
        if sum(option_existence) == 1:
            use_as_index = index_path_options[option_existence.index(True)]
            uuid = tree.get_leaf_from_path(use_as_index, "final_path")
            if not directory_has_index:
                self._use_as_index(uuid, tree)
            else:
                self._warn_extra_index_options(directory, [uuid], tree)
            return

        # cases where multiple readme files exist
        # use the first one (which is index.html if it's already there)
        if not directory_has_index:
            use_as_index = index_path_options.pop(option_existence.index(True))
            use_uuid = tree.get_leaf_from_path(use_as_index, "final_path")
            self._use_as_index(use_uuid, tree)

        extra_paths = [p for p, e in zip(index_path_options, option_existence) if e]
        extra_uuids = [tree.get_leaf_from_path(p, "final_path") for p in extra_paths]
        self._warn_extra_index_options(directory, extra_uuids, tree)

    def _create_index_leaf(self, directory: Path, tree: TreeSpan) -> None:
        """Add a blank index.html file."""
        source_path = Path(".cambium/AddPlaceholderIndex/index.html")
        uuid = tree.add_leaf(
            directory, latest_path=source_path, final_path=directory / "index.html"
        )
        tree.abs_leaf_path(uuid).write_text("")

    def _path_updater(self, path: Path) -> Path:
        return path.with_name("index.html")

    def _use_as_index(self, leaf_uuid: str, tree: TreeSpan) -> None:
        """Move an existing leaf to have final path index.html."""
        tree.update_leaf_path(leaf_uuid, "final", self._path_updater)
        initial = tree.leaves["initial_path"][leaf_uuid]
        final = tree.leaves["final_path"][leaf_uuid]
        logger.info(f"Changing output path of {initial} to {final}")

    def _warn_extra_index_options(
        self, directory: Path, extra_uuids: list[str], tree: TreeSpan
    ) -> None:
        extra_str = ", ".join(
            [str(tree.leaves["initial_path"][uuid]) for uuid in extra_uuids]
        )
        logger.warning(
            f"{directory} already has an index.html, so additional option(s) will be built to their original location: {extra_str}."
        )
