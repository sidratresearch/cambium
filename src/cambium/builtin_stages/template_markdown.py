"""Cambium stage to apply Jinja templates to transformed markdown files."""

import datetime
import logging
from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from pydantic import BaseModel

from .. import __version__
from ..metadata import LeafMetadata
from ..stage import Stage
from ..tree import TreeSpan
from .utils import get_relative_path_modifier, markdown_to_html

logger = logging.getLogger(__name__)


class CambiumJinjaVariables(BaseModel, extra="forbid"):
    site_name: str
    relative_path_modifier: str
    cambium_version: str
    initial_path: Path
    metadata: LeafMetadata
    build_time_utc: datetime.datetime
    main_content: str
    dev_server: bool


class TemplateMarkdown(Stage):
    # Primary Hook Functions

    def tree_hook(self, tree: TreeSpan) -> None:

        # save a single build time for use in templates
        self.build_time_utc = datetime.datetime.now(tz=datetime.UTC)

        # Apply to Leaves
        tree.apply_to_leaves(self._tree_hook_for_leaf)

        # Read in special files as Jinja variables
        self.jinja_globals = self._read_jinja_globals(tree)

    def post_hook_initialize(self, tree: TreeSpan) -> None:
        # Initialize Jinja Environment
        self._initialize_jinja(tree)

    def post_hook(self, leaf_uuid: str, tree: TreeSpan) -> None:
        self._create_page(leaf_uuid, tree)

    # Utility Functions

    def _tree_hook_for_leaf(self, leaf_uuid: str, tree: TreeSpan) -> None:
        """Adds TemplatingMarkdown to markdown files not in static.

        We can't filter on final path since markdown files (yes template)
        and html files (no template) both have .html

        We can't filter on initial path since preview pages start with
        non-markdown suffixes.
        """
        if tree.leaves["latest_path"][leaf_uuid].suffix.lower() != ".md":
            return

        self._register_hook(leaf_uuid, tree, "post_hooks")

    def _read_jinja_globals(self, tree: TreeSpan) -> dict[str, str]:
        search_path = tree.root_directory / ".cambium/jinja_variables"
        variable_paths = search_path.glob("**/*")

        jinja_globals: dict[str, str] = {}
        for path in variable_paths:
            logger.debug(f"Reading Jinja variables from {path}")
            globals_key = path.name.removesuffix(path.suffix)

            if globals_key in CambiumJinjaVariables.model_fields:
                raise ValueError(f"""{globals_key} ({path.name}) is a reserved name and
                    cannot be used in {search_path}.""")
            if path.name in jinja_globals:
                raise ValueError(f"Multiple files {path.name} in {search_path}.")

            variable = path.read_text()
            if path.suffix == ".md":
                # TODO: should this actually be a part of transform markdown somehow?
                variable = markdown_to_html(variable)
            jinja_globals[globals_key] = variable
        return jinja_globals

    def _initialize_jinja(self, tree: TreeSpan) -> None:
        """Initializing Jinja Templating Environment."""
        logger.debug(
            f"Using Jinja template directories {[str(p) for p in tree.config.template_directories]}"
        )
        self.jinja_env = Environment(
            loader=FileSystemLoader(tree.config.template_directories),
            trim_blocks=True,
            lstrip_blocks=True,
        )
        self.jinja_env.globals = self.jinja_globals

    def _create_page(self, leaf_uuid: str, tree: TreeSpan) -> None:
        input_path = tree.abs_leaf_path(leaf_uuid)

        template_name = "base.html.jinja"
        logger.debug(
            f"Applying Jinja template {template_name} to {tree.leaves['latest_path'][leaf_uuid]}"
        )

        # Jinja does not complain in a variable is missing from the environment
        # Something to think about wrt potential stage-added items and custom themes

        cambium_jinja_variables = CambiumJinjaVariables(
            # general Cambium utility items
            cambium_version=__version__,
            site_name=tree.config.site_name,
            relative_path_modifier=get_relative_path_modifier(
                tree.leaves["final_path"][leaf_uuid]
            ),
            metadata=tree.leaves["metadata"][leaf_uuid],
            initial_path=tree.leaves["initial_path"][leaf_uuid],
            dev_server=tree.config.dev_server,
            # specialist variables created by this stage
            build_time_utc=self.build_time_utc,
            # actual markdown content
            main_content=input_path.read_text(),
        )

        main_template = self.jinja_env.get_template(template_name)
        output_html = main_template.render(**cambium_jinja_variables.model_dump())
        input_path.write_text(output_html)
