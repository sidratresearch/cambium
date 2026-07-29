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
from .utils import markdown_to_html

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
    jinja_template_paths: list[Path] = []

    # Primary Hook Functions

    def tree_hook(self, tree: TreeSpan) -> None:

        # save a single build time for use in templates
        self.build_time_utc = datetime.datetime.now(tz=datetime.UTC)

        # Apply to Leaves
        tree.apply_to_leaves(self._tree_hook_for_leaf)

    def post_hook_initialize(self, tree: TreeSpan) -> None:
        # load in templates registered by other stages
        for stage_templates in tree.config.stage_theme_directories["templates"]:
            if stage_templates.exists():
                self.jinja_template_paths.append(stage_templates)
            else:
                logger.warning(f"""{stage_templates} was registered as a stage template
                    path, but doesn't exist.""")

        # Initialize Jinja Environment
        self._initialize_jinja(tree)

    def post_hook(self, leaf_uuid: str, tree: TreeSpan) -> None:
        self._create_page(leaf_uuid, tree)

    # Utility Functions

    def _tree_hook_for_leaf(self, leaf_uuid: str, tree: TreeSpan) -> None:
        """Adds TemplatingMarkdown to markdown files not in static."""
        if tree.leaves["initial_path"][leaf_uuid].suffix.lower() != ".md":
            return

        tree.leaves["hooks"][leaf_uuid]["post_hooks"].append(self.__class__.__name__)

    def _populate_jinja_template_paths(self, tree: TreeSpan) -> None:
        for tmp_theme_path in tree.config.ordered_theme_directories:
            if (tmp_theme_path / "templates").exists():
                self.jinja_template_paths.append(tmp_theme_path / "templates")

        if len(self.jinja_template_paths) == 0:
            raise RuntimeError("No theme template libraries were found.")

        logger.debug(f"Found Jinja templates {self.jinja_template_paths}")

    def _read_jinja_globals(self, tree: TreeSpan) -> dict[str, str]:
        search_path = tree.root_directory / ".cambium/jinja_variables"
        variable_paths = search_path.glob("**/*")

        jinja_globals: dict[str, str] = {}
        for path in variable_paths:
            logger.debug(f"Reading Jinja variables from {path}")
            globals_key = path.name.removesuffix(path.suffix)

            if globals_key in CambiumJinjaVariables.model_fields:
                # TODO: move this check into a tree hook so it gets caught on dry run
                raise ValueError(f"""{globals_key} ({path.name}) is a reserved name and
                    cannot be used in {search_path}.""")
            if path.name in jinja_globals:
                raise ValueError(f"Multiple files {path.name} in {search_path}.")

            variable = path.read_text()
            if path.suffix == ".md":
                # TODO: should this actually be a part of transform markdown somehow?
                variable = markdown_to_html(variable, None)
            jinja_globals[globals_key] = variable
        return jinja_globals

    def _initialize_jinja(self, tree: TreeSpan) -> None:
        """Initializing Jinja Templating Environment."""
        self._populate_jinja_template_paths(tree)
        self.jinja_env = Environment(
            loader=FileSystemLoader(self.jinja_template_paths),
        )
        self.jinja_env.globals = self._read_jinja_globals(tree)

    def _create_page(self, leaf_uuid: str, tree: TreeSpan) -> None:
        input_path = tree.abs_leaf_path(leaf_uuid)
        number_of_parents: int = len(
            input_path.parent.relative_to(tree.config.tmp_dir.absolute()).parents
        )
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
            relative_path_modifier="../" * number_of_parents,
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
