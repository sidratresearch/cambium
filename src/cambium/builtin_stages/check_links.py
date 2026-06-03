"""Cambium stage to verify the integrity of links.

Currently only checks internal links, discarding anchors.
"""

import logging
from html.parser import HTMLParser
from pathlib import Path

from cambium.builtin_stages.utils import is_external_link, resolve_internal_link

from ..stage import Stage
from ..tree import TreeSpan

logger = logging.getLogger(__name__)


class LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.in_link = False
        self.links = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        for name, value in attrs:
            if name in ["href", "src"]:
                self.links.append((tag.lower(), name, value))


class CheckLinks(Stage):
    def tree_hook(self, tree: TreeSpan) -> None:
        tree.apply_to_leaves(self._tree_hook_for_leaf)

    def _tree_hook_for_leaf(self, leaf_uuid: str, tree: TreeSpan) -> None:
        final_path = tree.leaves["final_path"][leaf_uuid]

        if final_path.suffix in (".md", ".html"):
            tree.leaves["hooks"][leaf_uuid]["post_hooks"].append(
                self.__class__.__name__
            )

    def post_hook(self, leaf_uuid: str, tree: TreeSpan) -> None:
        leaf_path = tree.abs_leaf_path(leaf_uuid)

        if leaf_path.suffix == ".html":
            self._check_links_in_html(leaf_uuid, leaf_path, tree)

    def _check_links_in_html(self, leaf_uuid: str, path: Path, tree: TreeSpan) -> None:
        html_parser = LinkParser()
        html_parser.feed(path.read_text())

        links = html_parser.links

        internal_links = [i for i in links if not is_external_link(i[2])]
        directory = tree.leaves["final_path"][leaf_uuid].parent
        valid_dests = [tree.leaves["final_path"][uuid] for uuid in tree.leaves["uuids"]]

        for tag, attr, original_dest in internal_links:
            self._check_internal_link(
                original_dest, directory, valid_dests, leaf_uuid, tree
            )

    def _check_internal_link(
        self,
        destination: str,
        file_directory: Path,
        final_paths: list[Path],
        leaf_uuid: str,
        tree: TreeSpan,
    ) -> None:
        """Verify that an internal link points to a location in final paths."""
        # TODO: implement anchor links, or a warning
        if "#" in destination:
            destination = destination[: destination.index("#")]
            if len(destination) == 0:
                return

        dest_full = resolve_internal_link(
            destination, file_directory, tree.build_directory
        )

        if dest_full not in final_paths and dest_full not in tree.directories_in_build:
            initial_path = tree.leaves["initial_path"][leaf_uuid]
            logger.warning(
                f"{initial_path} contains a link to {dest_full} which is not a known file."
            )
