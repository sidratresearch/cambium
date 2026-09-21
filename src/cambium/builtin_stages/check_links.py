"""Cambium stage to verify the integrity of links.

Currently only checks internal links, discarding anchors.
"""

import logging
from collections import defaultdict
from html.parser import HTMLParser
from typing import Any

from ..stage import Stage, StageConfig
from ..tree import TreeSpan
from ..utils.other_utils import apply_to_leaves, get_href_destination, is_external_link
from ..utils.path_utils import abs_leaf_path, leaf_final_paths

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
        self.runs_after = []
        self.runs_before = []

    def tree_hook(self, tree: TreeSpan) -> None:
        apply_to_leaves(tree, self._tree_hook_for_leaf)

    def _tree_hook_for_leaf(self, leaf_uuid: str, tree: TreeSpan) -> None:
        final_path = tree.leaves["final_path"][leaf_uuid]
        if final_path.suffix in (".md", ".html"):
            self._register_hook(leaf_uuid, tree, "post_hooks")

    def post_hook_initialize(self, tree: TreeSpan) -> None:
        """Traverse all HTML files to compile lists of source/destination links.

        We want to crawl *all* HTML files to build the list of valid anchors, so we
        may as well grab all of the places linked *to* at the same time.
        """
        self.all_anchors = defaultdict(list)
        self.all_links = defaultdict(list)

        for uuid in tree.leaves["uuids"]:
            latest_path = abs_leaf_path(tree, uuid)
            if latest_path.suffix not in (".html", ".htm"):
                continue

            html_parser = LinkParser()
            html_parser.feed(latest_path.read_text())

            self.all_links[uuid] = html_parser.links
            self.all_anchors[uuid] = html_parser.anchor_ids

        self.leaf_final_paths = leaf_final_paths(tree)

    def post_hook(self, leaf_uuid: str, tree: TreeSpan) -> None:
        links = self.all_links[leaf_uuid]
        internal_links = [i for i in links if not is_external_link(i[2])]

        source_file = tree.leaves["initial_path"][leaf_uuid]

        for tag, attr, original_dest in internal_links:
            if original_dest in self.config.links_to_ignore:
                continue

            # for each link, get its type (and which file it points to, if relevant)
            href_type, linked_uuid = get_href_destination(
                original_dest, "final_path", leaf_uuid, tree
            )

            if href_type in ["external", "static"]:
                continue
            if href_type == "unknown absolute":
                logger.warning(
                    f"Could not verify absolute link {original_dest} in {source_file}"
                )
                continue

            # only remaining option is internal link
            if linked_uuid is None:
                logger.warning(
                    f"{source_file} contains a link to {original_dest} which is not a known file"
                )
                continue
            if "#" in original_dest:
                anchor = original_dest.split("#", maxsplit=1)[-1]
                self._check_anchor_link(linked_uuid, anchor, leaf_uuid, tree)

    def _check_anchor_link(
        self, destination_uuid: str, anchor: str, leaf_uuid: str, tree: TreeSpan
    ) -> None:
        """Check that an internal anchor link points to an HTML id that exists."""
        if anchor == "":
            return
        if anchor not in self.all_anchors[destination_uuid]:
            initial_path = tree.leaves["initial_path"][leaf_uuid]
            destination_path = tree.leaves["final_path"][destination_uuid]
            logger.warning(
                f"{initial_path} contains a link to #{anchor} which can't be found on page {destination_path}"
            )
