"""Cambium stage to write site-level "reports".

e.g. index-style listings of all pages, lists of pages within a certain
category or with a certain tag

By default these reports are written to _build/_cambium-reports/. The
directory name is configurable, and if a given report would conflict with
a pre-existing file, an error would be raised at `Stage.add_leaf()`.
"""

import logging
from pathlib import Path
from typing import Any

from ..stage import Stage, StageConfig
from ..tree import TreeSpan
from .utils import get_relative_path_modifier

logger = logging.getLogger(__name__)

# TODO: implement some stage config
# do/don't index reports with pagefind
# do/don't generate reports on dev server only
# which reports to generate
# content of page titles

# TODO: consider the fact that this listing isn't actually complete - it misses the pagefind playground


class WriteReportsConfig(StageConfig):
    report_directory: Path = Path("_cambium-reports/")


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

        # At some point in the future we may use the metadata in generated reports
        # At the moment, linking directly to final paths breaks the
        # destination->leaf matching in IdentifyMetadata. And we should link
        # to final destination in case TransformMarkdown is not running
        self.runs_after = ["IdentifyMetadata"]

    def tree_hook(self, tree: TreeSpan) -> None:
        self.html_pages_index = _Report("html_pages.md", self, tree)

    def pre_hook_initialize(self, tree: TreeSpan) -> None:
        # Generate the report for listing all HTML pages

        html_leaves = []
        for leaf_uuid in tree.leaves["uuids"]:
            final_path = tree.leaves["final_path"][leaf_uuid]
            if final_path.suffix in (".html", ".html"):
                html_leaves.append(leaf_uuid)

        # HACK? If TransformMarkdown is active we need to put down initial
        # paths so that link change attempts have parseable links
        # If it's not active, we need to point to the final location
        if "TransformMarkdown" in tree.config.stages:
            html_links = [
                tree.leaves["initial_path"][leaf_uuid] for leaf_uuid in html_leaves
            ]
        else:
            html_links = [
                tree.leaves["final_path"][leaf_uuid] for leaf_uuid in html_leaves
            ]

        html_links.sort()
        links = [
            "# Listing of HTML Pages",
            "",
            f"Does not include pages in [`static`]({self.html_pages_index.relative_path_modifier}/static).",
            "",
        ] + [
            f"- [{e}]({self.html_pages_index.relative_path_modifier}{e})"
            for e in html_links
        ]
        self.html_pages_index.write("\n".join(links), tree)

    def pre_hook(self, _: str, __: TreeSpan) -> None:
        """Dummy function as all work is done by initialize."""
        return
