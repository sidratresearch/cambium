"""Cambium stage to apply Jinja templates to transformed markdown files."""

import datetime
import logging
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from cambium.builtin_stages.utils import markdown_to_html

from ..stage import Stage
from ..tree import TreeSpan

logger = logging.getLogger(__name__)


class TemplateMarkdown(Stage):

    jinja_template_paths: list[Path] = []

    # Primary Hook Functions

    def tree_hook(self, tree: TreeSpan) -> None:

        # save a single build time for use in templates
        self.build_time_utc = datetime.datetime.now(tz=datetime.UTC)

        # Apply to Leaves
        tree.apply_to_leaves(self._tree_hook_for_leaf)

    def post_hook_initialize(self, tree: TreeSpan) -> None:
        for stage_templates_path in tree.config.stage_jinja_template_directories:
            if stage_templates_path.exists():
                self.jinja_template_paths.append(stage_templates_path)
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
        variable_paths = tree.root_directory.glob(".cambium/jinja_variables/**/*")

        jinja_globals: dict[str, str] = {}
        for path in variable_paths:
            print(f"Reading Jinja variables from {path}")
            if path.name in jinja_globals:
                raise ValueError("Multiple files {path.name} in jinja_variables")

            variable = path.read_text()
            if path.suffix == ".md":
                variable = markdown_to_html(variable, None)
            jinja_globals[path.name.removesuffix(path.suffix)] = variable
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

        main_template = self.jinja_env.get_template(template_name)
        main_content = input_path.read_text()

        # Jinja does not complain in a variable is missing from the environment
        # Something to think about wrt potential stage-added items and custom themes

        output_html = main_template.render(
            # general Cambium utility items
            site_name=tree.config.site_name,
            relative_path_modifier="../" * number_of_parents,
            metadata=tree.leaves["metadata"][leaf_uuid],
            # specialist variables created by this stage
            page_title=f"{tree.leaves['metadata'][leaf_uuid].title} - {tree.config.site_name}",
            build_time_utc=self.build_time_utc,
            # actual markdown content
            main_content=main_content,
        )

        input_path.write_text(output_html)
