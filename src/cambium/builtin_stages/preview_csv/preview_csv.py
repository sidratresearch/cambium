"""Cambium stage to create preview pages for CSV data."""

import csv
import logging
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader
from pydantic import PositiveInt

from ...config import sort_user_paths
from ...stage import Stage, StageConfig
from ...tree import TreeSpan
from ..utils import (
    WrappedBlocksMixin,
    get_relative_path_modifier,
    path_matches_patterns,
)

logger = logging.getLogger(__name__)


class PreviewCSVConfig(StageConfig):
    enable_paths: list[str] = ["*.csv"]
    disable_paths: list[str] = []
    max_preview_rows: PositiveInt | None = None


class PreviewCSV(Stage):
    def _csv_path_updater(self, csv_path: Path) -> Path:
        return csv_path / "index.md"

    def __init__(self, config_dict: dict[str, Any]) -> None:
        self.config = PreviewCSVConfig.model_validate(config_dict)
        self.enable_patterns = sort_user_paths(self.config.enable_paths)
        self.disable_patterns = sort_user_paths(self.config.disable_paths)

        self.requires = []
        self.runs_before = ["TransformMarkdown", "IdentifyMetadata"]
        self.runs_after = []

        # store mappings between the preview leaves and the data leaves
        self.csv_to_md = {}
        self.md_to_csv = {}

        self.css_file = "css/preview_csv.css"
        # path from includes/static to the CSS file we want to import on preview pages

    def tree_hook(self, tree: TreeSpan) -> None:
        # get what the actual path of the CSS file will be in the build directory
        static_dir = tree.abs_static_stage_path(self.__class__.__name__).relative_to(
            tree.build_directory
        )
        self.css_link = static_dir / self.css_file

        # cast the deque to a list so that we can add new leaves to the end
        # we don't want to re-visit the added leaves anyway
        for leaf_uuid in list(tree.leaves["uuids"]):
            initial_path = tree.leaves["initial_path"][leaf_uuid]

            if path_matches_patterns(
                initial_path, self.enable_patterns
            ) and not path_matches_patterns(initial_path, self.disable_patterns):
                self._tree_hook_for_csv(leaf_uuid, initial_path, tree)

    def _tree_hook_for_csv(
        self, md_uuid: str, csv_initial_path: Path, tree: TreeSpan
    ) -> None:
        # change the final path for this leaf to be subfoldered and end in md
        tree.update_leaf_path(md_uuid, "final", self._csv_path_updater)
        tree.update_leaf_path(md_uuid, "latest", self._csv_path_updater)
        self._register_hook(md_uuid, tree, "pre_hooks")

        # create a companion leaf for the new data location
        source_path = Path(f".cambium/{self.__class__.__name__}/{csv_initial_path}")
        csv_uuid = tree.add_leaf(
            source_path, final_path=csv_initial_path / csv_initial_path.name
        )
        self._register_hook(csv_uuid, tree, "pre_hooks")

        self.md_to_csv[md_uuid] = csv_uuid
        self.csv_to_md[csv_uuid] = md_uuid

        logger.info(f"Creating preview page for {csv_initial_path}")

    def pre_hook(self, leaf_uuid: str, tree: TreeSpan) -> None:
        # figure out if this is the index.html
        if leaf_uuid in self.md_to_csv:
            self._pre_hook_md(leaf_uuid, tree)

        # or the csv itself
        else:
            self._pre_hook_csv(leaf_uuid, tree)

    def _pre_hook_md(self, md_uuid: str, tree: TreeSpan) -> None:
        preview_content = get_md_content(
            md_uuid,
            self.md_to_csv[md_uuid],
            tree,
            {
                "max_preview_rows": self.config.max_preview_rows,
                "css_link": self.css_link,
                "relative_path_modifier": get_relative_path_modifier(
                    tree.leaves["final_path"][md_uuid]
                ),
            },
        )
        tree.abs_leaf_path(md_uuid).write_text(preview_content)

    def _pre_hook_csv(self, csv_uuid: str, tree: TreeSpan) -> None:
        md_uuid = self.csv_to_md[csv_uuid]
        csv_content = tree.leaves["initial_path"][md_uuid].read_text()
        tree.abs_leaf_path(csv_uuid).write_text(csv_content)


def get_md_content(
    md_uuid: str, csv_uuid: str, tree: TreeSpan, jinja_variables: dict[str, Any]
) -> str:
    """Get the content for the Markdown preview page.

    This is done by using the native `csv` module, and rendering into an
    HTML table with Jinja, but this could be overriden.

    Note: there is currently no way for a stage to manipulate the csv
    content before it gets read in here, (e.g., round or sort the data),
    because we're reading from "initial_path" (i.e., from the root directory).
    """
    download_filename = tree.leaves["initial_path"][csv_uuid].name

    csv_data = []
    csv_path = tree.leaves["initial_path"][md_uuid]
    with csv_path.open() as csvfile:
        dialect = csv.Sniffer().sniff(csvfile.read(1024))
        csvfile.seek(0)
        reader = csv.reader(csvfile, dialect=dialect)
        for row in reader:
            csv_data.append(row)

    jinja_environment = Environment(
        loader=FileSystemLoader(tree.config.template_directories),
        lstrip_blocks=True,
        trim_blocks=True,  # stops Jinja lines from being replaced with newlines
        # if not enabled, Marko doesn't recognize the table as being a single HTMLBlock
    )

    template = jinja_environment.get_template("preview-csv.md.jinja")

    return template.render(
        download_filename=download_filename,
        csv_data=csv_data,
        cambium_wrap=WrappedBlocksMixin.wrap_anything,
        csv_filesize=csv_path.stat().st_size,
        **jinja_variables,
    )
