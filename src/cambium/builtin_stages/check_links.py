"""Cambium stage to verify the integrity of links.

Currently only checks internal links, discarding anchors.
"""

import logging
from collections import defaultdict
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

from cambium.builtin_stages.utils import is_external_link, resolve_internal_link

from ..stage import Stage, StageConfig
from ..tree import TreeSpan

logger = logging.getLogger(__name__)


class LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.in_link = False
        self.links = []
        self.anchor_ids = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        for name, value in attrs:
            if name in ["href", "src"]:
                # <link> href
                # <script> src
                # <img> src
                # <a> href
                # add srcset stuff
                self.links.append((tag.lower(), name, value))
            if name == "id":
                self.anchor_ids.append(value)


class CheckLinksConfig(StageConfig):
    links_to_ignore: list[str] = []
    """Link destinations that should not be checked"""
    # TODO: use path/glob/name options like other path config items


class CheckLinks(Stage):
    def __init__(self, config_dict: dict[str, Any]) -> None:
        self.config = CheckLinksConfig.model_validate(config_dict)
        self.requires = []

    def tree_hook(self, tree: TreeSpan) -> None:
        tree.apply_to_leaves(self._tree_hook_for_leaf)

    def _tree_hook_for_leaf(self, leaf_uuid: str, tree: TreeSpan) -> None:
        final_path = tree.leaves["final_path"][leaf_uuid]
        if final_path.suffix in (".md", ".html"):
            tree.leaves["hooks"][leaf_uuid]["post_hooks"].append(
                self.__class__.__name__
            )

    def post_hook_initialize(self, tree: TreeSpan) -> None:
        """Traverse all HTML files to compile lists of source/destination links.

        We want to crawl *all* HTML files to build the list of valid anchors, so we
        may as well grab all of the places linked *to* at the same time.
        """
        self.all_anchors = defaultdict(list)
        self.all_links = defaultdict(list)

        for uuid in tree.leaves["uuids"]:
            latest_path = tree.abs_leaf_path(uuid)
            if latest_path.suffix not in (".html", ".htm"):
                continue

            html_parser = LinkParser()
            html_parser.feed(latest_path.read_text())

            self.all_links[uuid] = html_parser.links
            self.all_anchors[uuid] = html_parser.anchor_ids

        self.leaf_final_paths = tree.leaf_final_paths()

    def post_hook(self, leaf_uuid: str, tree: TreeSpan) -> None:
        links = self.all_links[leaf_uuid]
        internal_links = [i for i in links if not is_external_link(i[2])]

        directory = tree.leaves["final_path"][leaf_uuid].parent

        for tag, attr, original_dest in internal_links:
            self._check_internal_link(original_dest, directory, leaf_uuid, tree)

    def _check_internal_link(
        self,
        destination: str,
        file_directory: Path,
        leaf_uuid: str,
        tree: TreeSpan,
    ) -> None:
        # split anchor from page
        if "#" in destination:
            page_destination, anchor = destination.split("#")
        else:
            page_destination, anchor = destination, ""

        # validate the page existence
        if len(page_destination) == 0 or page_destination == "/":
            destination_uuid = leaf_uuid
        else:
            destination_uuid = self._check_internal_link_no_anchor(
                page_destination, file_directory, leaf_uuid, tree
            )

        # don't check anchor if page failed, or there is no anchor
        if destination_uuid is None or len(anchor) == 0:
            return

        self._check_anchor_link(destination_uuid, anchor, leaf_uuid, tree)

    def _check_anchor_link(
        self, destination_uuid: str, anchor: str, leaf_uuid: str, tree: TreeSpan
    ) -> None:
        """Check that an internal anchor link points to an HTML id that exists."""
        if anchor not in self.all_anchors[destination_uuid]:
            initial_path = tree.leaves["initial_path"][leaf_uuid]
            destination_path = tree.leaves["final_path"][destination_uuid]
            logger.warning(
                f"{initial_path} contains a link to #{anchor} which can't be found on page {destination_path}."
            )

    def _check_internal_link_no_anchor(
        self,
        destination: str,
        file_directory: Path,
        leaf_uuid: str,
        tree: TreeSpan,
    ) -> str | None:
        """Verify that an internal link points to a location in final paths."""

        # TODO: hack for current issue w/ menu
        if destination.startswith("/"):
            return

        dest_full = resolve_internal_link(
            destination, file_directory, tree.build_directory
        )

        if str(dest_full) in self.config.links_to_ignore:
            return

        initial_path = tree.leaves["initial_path"][leaf_uuid]
        if dest_full.parts[0] == "static":
            logger.debug(
                f"Not checking link to static file {dest_full} in {initial_path}"
            )
            return
        if (
            dest_full not in self.leaf_final_paths
            and dest_full not in tree.directories_in_build
        ):
            logger.warning(
                f"{initial_path} contains a link to {dest_full} which is not a known file."
            )
            return

        # check if linking to a directory
        # TODO: if you link to a directory, should the checker:
        # fail, warn, warn + return index.htm
        if dest_full in tree.directories_in_build:
            return

        return tree.get_leaf_from_path(dest_full, "final_path")
