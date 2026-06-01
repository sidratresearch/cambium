"""Cambium stage to integrate the static search library Pagefind."""

import asyncio
import logging
from pathlib import Path
from typing import Any

from pagefind.index import IndexConfig, PagefindIndex

from ...stage import Stage, StageConfig
from ...tree import TreeSpan

logger = logging.getLogger(__name__)


class PagefindSearchConfig(StageConfig):
    root_selector: str = "<html>"
    """html selector that pagefind cares about, narrow with `data-pagefind-body`"""
    exclude_selectors: list[str] = []
    force_lanuage: str | None = None
    include_characters: str = "._"
    keep_index_url: bool = False  # ?
    write_playground: bool = True  # false for prod


class PagefindSearch(Stage):
    """
    Stage for Cambium integration with Pagefind.

    Pagefind needs to use an asynchronous context manager which stays alive while
    all of the leaves are individually added to the index. Because we want to open
    this once, and work with every leaf in the tree, we actually do that in the post
    hook finalize function.

    We do need to make sure that the post hook finalize actually runs, which means
    we need to register the post hook as running on at least one leaf.
    """

    def __init__(self, config_dict: dict[str, Any]) -> None:
        validated_config = PagefindSearchConfig.model_validate(config_dict)
        pagefind_config = IndexConfig(
            **validated_config.model_dump(),
        )

        self.pagefind_config = pagefind_config
        self.requires = ["TemplateMarkdown"]  # to have somewhere to put the search box
        self.pagefind_directory = "static/pagefind"

        self.context_function = None
        self.context_parameters = {}

    def tree_hook(self, tree: TreeSpan) -> None:
        tree.config.stage_jinja_template_directories.append(
            Path(__file__).parent / "includes/templates"
        )
        for uuid in tree.leaves["uuids"]:
            if tree.leaves["final_path"][uuid].suffix == ".html":
                tree.leaves["hooks"][uuid]["pre_hooks"].append(self.__class__.__name__)
                tree.leaves["hooks"][uuid]["post_hooks"].append(self.__class__.__name__)

        self.abs_pagefind_directory = tree.abs_static_stage_path(
            self.__class__.__name__
        )

    def pre_hook(self, leaf_uuid: str, tree: TreeSpan) -> None:
        self._set_leaf_metadata("show_searchbar_on_page", True, leaf_uuid, tree)
        self._set_leaf_metadata(
            "searchbar_component",
            "search-component.html.jinja",
            leaf_uuid,
            tree,
        )
        self._set_leaf_metadata(
            "head_links",
            "head.html.jinja",
            leaf_uuid,
            tree,
        )
        self._set_leaf_metadata(
            "pagefind_directory",
            self.abs_pagefind_directory.relative_to(tree.build_directory.absolute()),
            leaf_uuid,
            tree,
        )

    def post_hook(self, leaf_uuid: str, tree: TreeSpan) -> None:
        """Fake post hook function for Pagefind integration."""
        return

    def post_hook_finalize(self, tree: TreeSpan) -> None:
        """One-time call primary function for Cambium's Pagefind integration."""
        html_leaves = [
            uuid
            for uuid in tree.leaves["uuids"]
            if tree.leaves["final_path"][uuid].suffix == ".html"
        ]

        if len(html_leaves) == 0:
            logger.warning("No HTML files found for Pagefind to index.")
            return

        asyncio.run(self._post_tree_hook(tree, html_leaves))

    async def _post_tree_hook(self, tree: TreeSpan, html_leaves: list[str]) -> None:
        """Read all HTML pages into the Pagefind index."""
        logger.info("Building Pagefind index")

        async with PagefindIndex(config=self.pagefind_config) as index:
            for uuid in html_leaves:
                final_path = tree.leaves["final_path"][uuid]
                content = tree.abs_leaf_path(uuid).read_text()
                await index.add_html_file(content=content, source_path=str(final_path))

            pf_dir_print = (
                tree.build_directory
                / self.abs_pagefind_directory.relative_to(
                    tree.build_directory.absolute()
                )
            )
            logger.info(f"Writing pagefind files to {pf_dir_print}")
            await index.write_files(str(self.abs_pagefind_directory))
            await index.delete_index()  # don't write files to default location
