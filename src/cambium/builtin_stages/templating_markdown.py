from ..stage import Stage
from ..tree import TreeSpan

import importlib
from jinja2 import Environment, FileSystemLoader
from pathlib import Path

import logging

logger = logging.getLogger(__name__)

PACKAGE_FOLDER = Path(__file__).parent / ".."


class TemplateMarkdown(Stage):

    jinja_template_paths = [
        Path(PACKAGE_FOLDER) / "themes/default/templates",
    ]

    def tree_hook(self, tree: TreeSpan) -> None:

        # Initialize Jinja Environment
        self._initialize_jinja()

        # Apply to Leaves
        tree.apply_to_leaves(self._tree_hook_for_leaf)

    def _tree_hook_for_leaf(self, leaf_uuid: str, tree: TreeSpan) -> None:
        """
        Adds TemplatingMarkdown to markdown files not in static
        """
        if tree.leaves["initial_path"][leaf_uuid].parts[0] == "static":
            return
        if tree.leaves["latest_path"][leaf_uuid].suffix.lower() != ".md":
            return

        tree.leaves["hooks"][leaf_uuid]["post_hooks"].append(self.__class__.__name__)

    def post_hook(self, leaf_uuid: str, tree: TreeSpan) -> None:
        self._create_page(leaf_uuid, tree)

    def _initialize_jinja(self) -> None:
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

        input_path: Path = tree.config.tmp_dir / tree.leaves["latest_path"][leaf_uuid]
        output_path: Path = tree.config.tmp_dir / tree.leaves["final_path"][leaf_uuid]
        number_of_parents: int = len(
            output_path.parent.relative_to(tree.config.tmp_dir.absolute()).parents
        )

        main_template = self.jinja_env.get_template("base.html.jinja")
        main_content = input_path.read_text()

        output_html = main_template.render(
            page_title=tree.config.site_name,
            main_content=main_content,
            relative_path_modifier="../" * number_of_parents,
        )

        output_path.write_text(output_html)
        tree.leaves["latest_path"][leaf_uuid] = output_path
