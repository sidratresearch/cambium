import logging
import textwrap
from pathlib import Path
from typing import Any

from pydantic import AnyUrl

from ..stage import Stage, StageConfig
from ..tree import TreeSpan

"""
This stage is NOT default because it requires a URL
"""

logger = logging.getLogger(__name__)


class AddSitemapConfig(StageConfig):
    url: AnyUrl


class AddSitemap(Stage):

    def __init__(self, config_dict: dict[str, Any]) -> None:
        self.config = AddSitemapConfig.model_validate(config_dict)
        self.requires = []
        self.entries = []

    def tree_hook(self, tree: TreeSpan) -> None:
        # always attempt to add a sitemap
        # if you want to disable it because you've got your own, edit config
        self._add_sitemap_leaf(tree)

        # register a prehook to run after the tree structure is finalized, when
        # we'll know all final paths
        for leaf_uuid in tree.leaves["uuids"]:
            tree.leaves["hooks"][leaf_uuid]["pre_hooks"].append(self.__class__.__name__)

    def _add_sitemap_leaf(self, tree: TreeSpan) -> None:
        logger.debug("Adding new leaf for sitemap.xml")
        uuid = tree.add_leaf(Path())

        # unclear what restrictions exist on the filename
        tree.leaves["final_path"][uuid] = Path("sitemap.xml")

        # need to create a latest_path so that it can get copied into the tempdir
        # This slightly weird hack is also used by AddPlaceholderIndex
        source_path = Path(f".cambium/{self.__class__.__name__}/sitemap.xml")

        # not using tree.update_leaf_path because it doesn't make sense here
        tree.leaves["latest_path"][uuid] = source_path
        tree.leaves["hooks"][uuid]["transforms"].append(self.__class__.__name__)
        tree.abs_write_path(uuid).write_text("")

        logger.debug("Added sitemap file")

    def pre_hook(self, leaf_uuid: str, tree: TreeSpan) -> None:
        final_path = tree.leaves["final_path"][leaf_uuid]
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
            entry_template.format(full_url=f"{self.config.url}/{path}")
            for path in self.entries
        ]

        # ensure sitemap doesn't change unecessarily
        xml_entries.sort()

        sitemap_contents = sitemap_template.format(entries="\n\t  ".join(xml_entries))
        tree.abs_write_path(leaf_uuid).write_text(sitemap_contents)
