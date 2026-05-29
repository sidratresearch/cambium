"""Cambium stage to apply Jinja templates to transformed markdown files."""

import logging
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader

from ..stage import Stage
from ..tree import TreeSpan

logger = logging.getLogger(__name__)


class TemplateMarkdown(Stage):

    jinja_template_paths: list[Path] = []

    # Primary Hook Functions

    def tree_hook(self, tree: TreeSpan) -> None:

        # Initialize Jinja Environment
        self._initialize_jinja(tree)

        # Apply to Leaves
        tree.apply_to_leaves(self._tree_hook_for_leaf)

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

    def _initialize_jinja(self, tree: TreeSpan) -> None:
        """Initializing Jinja Templating Environment."""
        self._populate_jinja_template_paths(tree)
        self.jinja_env = Environment(loader=FileSystemLoader(self.jinja_template_paths))

    def _create_sidebar(self) -> None:
        pass

    def _create_footer(self) -> None:
        pass

    def _create_header(self) -> None:
        pass

    def _create_menu(self) -> None:
        pass

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
            page_title=f"{tree.leaves['metadata'][leaf_uuid].title} - {tree.config.site_name}",
            main_content=main_content,
            relative_path_modifier="../" * number_of_parents,
            footer_left=tree.config.site_name,
            header_left=f"<a href='{'../'*number_of_parents}index.html' class='header-link'>{tree.config.site_name}</a>",
            table_of_contents=tree.leaves["metadata"][leaf_uuid].table_of_contents,
        )

        input_path.write_text(output_html)
