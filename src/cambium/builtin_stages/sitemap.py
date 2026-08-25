"""Cambium stage to create a `sitemap.xml`."""

import logging
import textwrap
from pathlib import Path

from ..stage import Stage
from ..tree import TreeSpan

"""
This stage is NOT default because it requires a URL
"""

logger = logging.getLogger(__name__)


class AddSitemap(Stage):

    def tree_hook(self, tree: TreeSpan) -> None:
        if tree.config.hosting["url"] is None:
            raise ValueError(
                "Cannot create a sitemap.xml without `domain_name` set in the config."
            )
        self.url = tree.config.hosting["url"]
        self.entries = []

        # if this stage is enabled, always attempt to add a sitemap
        # if you want to disable it because you've got your own, edit config
        self._add_sitemap_leaf(tree)

    def _add_sitemap_leaf(self, tree: TreeSpan) -> None:
        logger.debug("Adding new leaf for sitemap.xml")

        source_path = Path(f".cambium/{self.__class__.__name__}/sitemap.xml")
        uuid = tree.add_leaf(source_path, final_path=Path("sitemap.xml"))
        tree.leaves["hooks"][uuid]["transforms"].append(self.__class__.__name__)
        logger.debug("Added sitemap file")

    def transform_initialize(self, tree: TreeSpan) -> None:
        """Populate the list of all HTML final paths.

        We could put this in the tree hook and just assume that all html-creating
        stages are already run, but that's not necessary.
        """
        for final_path in tree.leaf_final_paths():
            if final_path.suffix in (".html", ".htm"):
                self.entries.append(final_path)

    def transform(self, leaf_uuid: str, tree: TreeSpan) -> None:
        entry_template = "<url><loc>{full_url}</loc></url>"
        sitemap_template = """
            <?xml version="1.0" encoding="UTF-8"?>
                <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
                  {entries}
            </urlset>"""

        # handle whitespace from multiline string, since XML seems to be finicky
        sitemap_template = textwrap.dedent(sitemap_template).strip()

        xml_entries = [
            entry_template.format(full_url=f"{self.url}/{path}")
            for path in self.entries
        ]

        # ensure sitemap doesn't change unecessarily
        xml_entries.sort()

        sitemap_contents = sitemap_template.format(entries="\n\t  ".join(xml_entries))
        tree.abs_leaf_path(leaf_uuid).write_text(sitemap_contents)
