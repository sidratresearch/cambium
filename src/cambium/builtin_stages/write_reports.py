"""Cambium stage to write site-level "reports".

e.g. index-style listings of all pages, lists of pages within a certain
category or with a certain tag

By default these reports are written to _build/_cambium-reports/. The
directory name is configurable, and if a given report would conflict with
a pre-existing file, an error would be raised at `Stage.add_leaf()`.
"""

import logging
from pathlib import Path
from typing import Any, Literal

from ..stage import Stage, StageConfig
from ..tree import TreeSpan
from .utils import get_relative_path_modifier

logger = logging.getLogger(__name__)


class WriteReportsConfig(StageConfig):
    report_directory: Path = Path("_cambium-reports/")
    """Location in the build directory where reports will be placed."""

    reports: list[Literal["html_pages"]] | None = ["html_pages"]
    """List of reports to create."""

    dev_only: bool = False
    """Only create report pages when running the development server."""


class _Report:
    """A helper class for WriteReports which aggregates some of the bookkeeping."""

    def __init__(self, filename: str, caller: "WriteReports", tree: TreeSpan) -> None:
        self.path_in_build = caller.config.report_directory / filename

        # NOTE: the number of segments in initial path and final path have to match
        # Because we set relative_path_modifier based on final path, but
        # TransformMarkdown will validate links based on initial_path
        # Something to think about if we update the path later...
        self.leaf_uuid = caller.add_leaf(self.path_in_build, tree)

        self.relative_path_modifier = get_relative_path_modifier(self.path_in_build)

        caller._register_hook(self.leaf_uuid, tree, "pre_hooks")

    def write(self, text: str, tree: TreeSpan) -> None:
        tree.abs_leaf_path(self.leaf_uuid).write_text(text)
        logger.info(f"Wrote report {self.path_in_build}")


class WriteReports(Stage):
    def __init__(self, config_dict: dict[str, Any]) -> None:
        self.config = WriteReportsConfig.model_validate(config_dict)
        self.requires = []
        self.runs_before = []

        if self.config.reports is None:
            self.config.reports = []
        if len(self.config.reports) == 0:
            logger.warning("No reports are requested")

        # At some point in the future we may use the metadata in generated reports
        # At the moment, linking directly to final paths breaks the
        # destination->leaf matching in IdentifyMetadata. And we should link
        # to final destination in case TransformMarkdown is not running
        self.runs_after = ["IdentifyMetadata"]

    def tree_hook(self, tree: TreeSpan) -> None:
        if self.config.dev_only and not tree.config.dev_server:
            logger.info(f"{self.__class__.__name__} is disabled on build")
            return

        if "html_pages" in self.config.reports:
            self.html_pages_index = _Report("html_pages.md", self, tree)

    def pre_hook_initialize(self, tree: TreeSpan) -> None:
        # Generate the report for listing all HTML pages

        html_leaves = []
        for leaf_uuid in tree.leaves["uuids"]:
            final_path = tree.leaves["final_path"][leaf_uuid]
            if final_path.suffix in (".html", ".html"):
                html_leaves.append(leaf_uuid)

        links = []
        for uuid in html_leaves:
            title, path = self._get_htmlpage_link(uuid, tree)
            path = self.html_pages_index.relative_path_modifier + str(path)
            links.append(f"- [{title}]({path})")
        links.sort()

        links = [
            "# Listing of HTML Pages",
            "",
            f"Does not include pages in [`static`]({self.html_pages_index.relative_path_modifier}static).",
            "",
            *links,
        ]
        self.html_pages_index.write("\n".join(links), tree)

    def _get_htmlpage_link(self, leaf_uuid: str, tree: TreeSpan) -> tuple[str, str]:
        initial_path, final_path = (
            tree.leaves["initial_path"][leaf_uuid],
            tree.leaves["final_path"][leaf_uuid],
        )
        title, path = final_path, final_path
        # HACK? If TransformMarkdown is active we need to put down initial
        # paths so that link change attempts have parseable links
        # If it's not active, we need to point to the final location
        if "TransformMarkdown" in tree.config.stages:
            title, path = initial_path, initial_path

        if str(initial_path).startswith(str(tree.config.stage_leaf_prefix)):
            stage_name = initial_path.parts[len(tree.config.stage_leaf_prefix.parts)]
            title = f"{final_path} ({stage_name})"

        return title, path

    def pre_hook(self, _: str, __: TreeSpan) -> None:
        """Dummy function as all work is done by initialize."""
        return
