"""Cambium stage to write site-level "reports".

e.g. index-style listings of all pages, lists of pages within a certain
category or with a certain tag

This stage would like to be run *before* TransformMarkdown, so that the
generated Markdown reports are then converted to HTML and templated. If
WriteReports is called after, or in the absence of TransformMarkdown, the
resulting report will remain Markdown.
"""

import logging
from pathlib import Path
from typing import Any

from ..stage import Stage
from ..tree import TreeSpan

logger = logging.getLogger(__name__)

# TODO: implement some stage config
# do/don't index reports with pagefind
# do/don't generate reports on dev server only
# which reports to generate
# content of page titles

# TODO: consider the fact that this listing isn't actually complete - it misses the pagefind playground


class _Report:
    """A helper class for WriteReports which aggregates some of the bookkeeping."""

    def __init__(self, filename: str, caller: "WriteReports", tree: TreeSpan) -> None:
        self.path_in_build = (caller.abs_report_directory / filename).relative_to(
            tree.build_directory
        )

        # NOTE: the number of segments in initial path and final path have to match
        # Because we set relative_path_modifier based on final path, but
        # TransformMarkdown will validate links based on initial_path
        initial_path = Path(".cambium/_cambium") / caller.__class__.__name__ / filename

        # NOTE: we are creating a leaf whose final path is in build/static
        # there's nothing *inherently* wrong with this, but it is sort of non-standard
        # in that user files in root/static *don't* get built into leaves
        # the difference is that we don't actually want this file to be
        # static, we *want* it to be touched by other stages
        self.leaf_uuid = tree.add_leaf(
            initial_path, latest_path=self.path_in_build, final_path=self.path_in_build
        )

        parent_folder = self.path_in_build.parent
        self.relative_path_modifier = "../" * len(parent_folder.parts)

        caller._register_hook(self.leaf_uuid, tree, "pre_hooks")

    def write(self, text: str, tree: TreeSpan) -> None:
        tree.abs_leaf_path(self.leaf_uuid).write_text(text)
        logger.debug(f"Wrote report {self.path_in_build}")


class WriteReports(Stage):
    def __init__(self, _: dict[str, Any]) -> None:
        self.requires = []
        # TODO: if link changing happens in transform hook, this shouldn't be needed
        self.runs_before = ["TransformMarkdown"]

        # At some point in the future we may use the metadata in generated reports
        # At the moment, linking directly to final paths breaks the
        # destination->leaf matching in IdentifyMetadata. And we should link
        # to final destination in case TransformMarkdown is not running
        self.runs_after = ["IdentifyMetadata"]

    def tree_hook(self, tree: TreeSpan) -> None:
        self.abs_report_directory = tree.abs_static_stage_path(self.__class__.__name__)

        self.html_pages_index = _Report("html_pages.md", self, tree)

    def pre_hook_initialize(self, tree: TreeSpan) -> None:
        if not self.abs_report_directory.exists():
            self.abs_report_directory.mkdir(parents=True)

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
        links = ["# Listing of HTML Pages"] + [
            f"- [{e}]({self.html_pages_index.relative_path_modifier}{e})"
            for e in html_links
        ]
        self.html_pages_index.write("\n".join(links), tree)

    def pre_hook(self, _: str, __: TreeSpan) -> None:
        """Dummy function as all work is done by initialize."""
        return
