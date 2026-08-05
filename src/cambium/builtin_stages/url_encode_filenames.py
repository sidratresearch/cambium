"""Cambium stage to ensure filenames are URL safe."""

import logging
import urllib
from pathlib import Path

from marko import Markdown
from marko.element import Element
from marko.inline import Image, Link
from marko.md_renderer import MarkdownRenderer
from slugify import slugify

from ..stage import Stage
from ..tree import TreeSpan
from .utils import is_external_link

logger = logging.getLogger(__name__)

slugify_options = {"lowercase": False, "regex_pattern": r"[^-a-zA-Z0-9_./]+"}

"""
If there is a file called "ruddy duck.jpg", to properly solve this we would need to:
- Output the file as "ruddy-duck.jpg"
- Check for markdown links to "ruddy duck.jpg" and fix them
    - These don't actually get recognized by marko (or GitHub) as valid links,
      but the same principle should apply to other non-ASCII characters
- Check for markdown links to "ruddy%20duck.jpg" and fix them
    - can use `urllib.parse.quote` for this
- Check for HTML links to both of the above and fix them too - this is much harder
"""


class URLEncodeFilenames(Stage):
    """Use `slugify` to generate filenames that are both url and filesystem safe."""

    changes = {}

    # need to rewrite links in both HTML and markdown files
    def tree_hook(self, tree: TreeSpan) -> None:
        for leaf_uuid in tree.leaves["uuids"]:
            prev = tree.leaves["final_path"][leaf_uuid]
            tree.update_leaf_path(leaf_uuid, "final", self._url_encode_path)
            post = tree.leaves["final_path"][leaf_uuid]

            if prev != post:
                self.changes[prev] = post

            if tree.leaves["initial_path"][leaf_uuid].suffix not in (".md", ".html"):
                continue

            self._register_hook(leaf_uuid, tree, "pre_hooks")

    def _url_encode_path(self, path: Path) -> Path:
        return Path(slugify(str(path), **slugify_options))

    def pre_hook(self, leaf_uuid: str, tree: TreeSpan) -> None:
        leaf_path = tree.abs_leaf_path(leaf_uuid)

        if leaf_path.suffix != ".md":
            # maybe want to handle HTML
            logger.warning(
                f"Running `{self.__class__.__name__}` on {leaf_path.suffix[1:]} files is not yet supported"
            )
            return  # TODO

        marko_object = Markdown(renderer=MarkdownRenderer)
        document = marko_object.parse(leaf_path.read_text())

        # if leaf_path.stem == "index":
        #     print(document)
        document = rewrite_urlsafe_links(
            document, tree.leaves["initial_path"][leaf_uuid].parent, self.changes
        )

        leaf_path.write_text(marko_object.render(document))


def rewrite_urlsafe_links(
    element: Element, parent_directory: Path, links_to_update: dict[Path, Path]
) -> Element:
    """Replace image and link destinations in a markdown element with versions that are
    both url and filesystem safe.
    """
    if isinstance(element, str):
        return element

    if isinstance(element, (Link, Image)):
        if is_external_link(element.dest):
            return Element

        dest_path = parent_directory / element.dest
        dest_path_urldecoded = Path(urllib.parse.unquote(str(dest_path)))

        new_dest = element.dest

        if dest_path in links_to_update:
            new_dest = links_to_update[dest_path]
        elif dest_path_urldecoded in links_to_update:
            # dest path was pre-url encoded
            new_dest = links_to_update[dest_path_urldecoded]

        element.dest = new_dest

        return element

    for child in element.children:
        child = rewrite_urlsafe_links(child, parent_directory, links_to_update)
    return element
