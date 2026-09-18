"""Cambium stage to apply Jinja templates to transformed markdown files."""

import datetime
import logging
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from .. import __version__
from ..metadata import LeafMetadata
from ..stage import Stage, StageConfig
from ..tree import TreeSpan
from ..utils.md_html_utils import markdown_to_html
from ..utils.other_utils import apply_to_leaves, make_jinja_environment
from ..utils.path_utils import abs_leaf_path, get_relative_path_modifier, is_valid_index

logger = logging.getLogger(__name__)


class CambiumGlobalJinjaVariables(BaseModel, extra="forbid"):
    # sitewide items
    site_name: str
    cambium_version: str
    build_time_utc: datetime.datetime
    dev_server: bool
    auto_menu_contents: list[dict[str, str]]
    homepage_filename: str | None


class CambiumPageJinjaVariables(BaseModel, extra="forbid"):
    # page specific items
    relative_path_modifier: str
    initial_path: Path
    metadata: LeafMetadata
    main_content: str


class TemplateMarkdown(Stage):
    # Primary Hook Functions

    def __init__(self, config_dict: dict[str, Any]) -> None:
        self.config = StageConfig.model_validate(config_dict)
        self.requires = []
        self.runs_after = []
        self.runs_before = ["CheckLinks"]

    def tree_hook(self, tree: TreeSpan) -> None:

        # save a single build time for use in templates
        self.build_time_utc = datetime.datetime.now(tz=datetime.UTC)

        # Apply to Leaves
        apply_to_leaves(tree, self._tree_hook_for_leaf)

        # Read in special files as Jinja variables
        self.user_jinja_globals = self._get_user_jinja_globals(tree)

    def post_hook_initialize(self, tree: TreeSpan) -> None:
        # Initialize Jinja Environment
        logger.debug(
            f"Using Jinja template directories {[str(p) for p in tree.config.template_directories]}"
        )
        self.jinja_env = make_jinja_environment(tree)
        self.jinja_env.globals = {
            **self.user_jinja_globals,
            **self._get_cambium_jinja_globals(tree),
        }

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

    def _get_user_jinja_globals(self, tree: TreeSpan) -> dict[str, str]:
        """Get user-created variables to load into Jinja globals (apply sitewide)."""
        search_path = tree.root_directory / ".cambium/jinja_variables"
        variable_paths = search_path.glob("**/*")

        jinja_globals: dict[str, str] = {}
        for path in variable_paths:
            logger.debug(f"Reading Jinja variables from {path}")
            globals_key = path.name.removesuffix(path.suffix)

            if (
                globals_key in CambiumPageJinjaVariables.model_fields
                or globals_key in CambiumGlobalJinjaVariables.model_fields
            ):
                if globals_key != path.name:
                    msg = f"{globals_key} ({path.name})"
                else:
                    msg = path.name
                msg += f" is a reserved name and cannot be used in {search_path}."
                raise RuntimeError(msg)
            if globals_key in jinja_globals:
                raise RuntimeError(
                    f"Multiple files which resolve to {globals_key} in {search_path}."
                )

            variable = path.read_text()
            if path.suffix == ".md":
                # TODO: should this actually be a part of transform markdown somehow?
                variable = markdown_to_html(variable)
            jinja_globals[globals_key] = variable
        return jinja_globals

    def _get_cambium_jinja_globals(self, tree: TreeSpan) -> dict[str, Any]:
        """Get Cambium-created variables to load into Jinja globals (apply sitewide)."""
        jinja_globals = CambiumGlobalJinjaVariables(
            site_name=tree.config.site_name,
            cambium_version=__version__,
            build_time_utc=self.build_time_utc,
            dev_server=tree.config.dev_server,
            auto_menu_contents=[],
            homepage_filename=None,
        )

        # Autogenerate the menu contents, and check for a homepage
        auto_menu_contents = []
        for leaf_uuid in tree.leaves["uuids"]:
            title = self._get_leaf_metadata(
                "title", leaf_uuid, tree, metadata_provider="cambium"
            )
            path = tree.leaves["final_path"][leaf_uuid]
            is_top_level = len(path.parts) == 1 or (
                len(path.parts) == 2 and is_valid_index(path)
            )
            is_homepage = len(path.parts) == 1 and is_valid_index(path)
            if is_homepage:
                jinja_globals.homepage_filename = path.name
            elif is_top_level and title is not None:
                jinja_globals.auto_menu_contents.append(
                    {"name": title, "filename": str(path)}
                )
        jinja_globals.auto_menu_contents = auto_menu_contents

        return jinja_globals.model_dump()

    def _create_page(self, leaf_uuid: str, tree: TreeSpan) -> None:
        input_path = abs_leaf_path(tree, leaf_uuid)

        template_name = "base.html.jinja"
        logger.debug(
            f"Applying Jinja template {template_name} to {tree.leaves['latest_path'][leaf_uuid]}"
        )

        # Jinja does not complain in a variable is missing from the environment
        # Something to think about wrt potential stage-added items and custom themes

        cambium_jinja_variables = CambiumPageJinjaVariables(
            # general Cambium utility items
            relative_path_modifier=get_relative_path_modifier(
                tree.leaves["final_path"][leaf_uuid]
            ),
            metadata=tree.leaves["metadata"][leaf_uuid],
            initial_path=tree.leaves["initial_path"][leaf_uuid],
            # actual markdown content
            main_content=input_path.read_text(),
        )

        main_template = self.jinja_env.get_template(template_name)
        output_html = main_template.render(**cambium_jinja_variables.model_dump())
        input_path.write_text(output_html.strip())
