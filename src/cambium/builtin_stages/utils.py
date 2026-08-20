"""Utility functions for builtin stages."""

import logging
import os
import re
import urllib
from collections import Counter
from pathlib import Path

from marko import Markdown, MarkoExtension
from marko.block import Document, Heading
from marko.element import Element
from marko.ext.gfm.elements import Table
from marko.ext.gfm.renderer import GFMRendererMixin
from marko.helpers import render_dispatch
from marko.html_renderer import HTMLRenderer
from marko.inline import Image, InlineHTML, Link, RawText
from slugify import slugify

from ..tree import TreeSpan

logger = logging.getLogger(__name__)


class CambiumHTMLRenderer(HTMLRenderer):
    """Custom renderer class to support Cambium-specific features."""

    def render_heading(self, element: Heading) -> str:
        """Adds anchor links from an `id` attribute."""
        heading_template = '<h{level} id="{id}">{children}</h{level}>\n'
        return heading_template.format(
            level=element.level, id=element.id, children=self.render_children(element)
        )


class WrappedBlocksMixin(GFMRendererMixin):
    """Wrap certain block elements in Cambium-specific divs."""

    class_template = "cambium-{tag}-holder"

    @classmethod
    def wrap_anything(cls, html_string: str, tag: str) -> str:
        """Wrap a string in a Cambium holder div."""
        css_class = cls.class_template.format(tag=tag)
        return f"<div class='{css_class}'>{html_string}</div>"

    @render_dispatch(HTMLRenderer)
    def render_table(self, element: Element) -> str:
        """Wraps `table` tags in a div."""
        rendered_table = super().render_table(element)
        return self.wrap_anything(rendered_table, "table")

    @render_dispatch(HTMLRenderer)
    def render_image(self, element: Image) -> str:
        """Wraps `img` tags in a div."""
        rendered_img = super().render_image(element)
        return self.wrap_anything(rendered_img, "img")


WrappedTables = MarkoExtension(elements=[Table], renderer_mixins=[WrappedBlocksMixin])


def is_external_link(dest: str) -> bool:
    """Check if a link points to an external URL."""
    return any(dest.startswith(prefix) for prefix in ["http:", "https:", "www."])


def resolve_internal_link(
    link: Path, parent_directory: Path, build_directory: Path
) -> Path:
    """Resolve internal paths as they may appear in user files.

    For "../a.html" located in "[root]/b/c.html", this returns "a.html"
    """
    full = (build_directory / parent_directory / link).resolve()
    build_abs = build_directory.resolve()
    try:
        return full.relative_to(build_abs)
    except ValueError:
        # definitionally both paths will be absolute
        # so the only option is full isn't within build
        raise ValueError(
            f"Error resolving internal link {link}, perhaps this file is outside the root directory?"
        )


def fetch_linked_leaf(
    link_element: Link, file_parent_directory: Path, tree: TreeSpan
) -> str | None:
    """Return the UUID of the leaf that a markdown link points to.

    Returns None if the link element does not point to a leaf (as identified
    by initial paths), or points to somewhere in the current document.
    """
    if is_external_link(link_element.dest):
        return
    if link_element.dest.startswith("#"):
        return

    # go from link contents to a Path
    resolved = resolve_internal_link(
        link_element.dest, file_parent_directory, tree.build_directory
    )
    if "#" in resolved.name:
        resolved = resolved.with_name(resolved.name[: resolved.name.index("#")])
    resolved = Path(urllib.parse.unquote_plus(str(resolved)))

    # skip links to static files
    if resolved.parts[0] == "static":
        return

    # skip links to directories
    # TODO: if you link to a directory, should we:
    # fail, warn, warn + return index.html
    # if resolved in tree.directories_in_build:
    #     return
    # breaks link resolution for previews

    try:
        return tree.get_leaf_from_path(resolved, "initial_path")
    except RuntimeError:
        # Previewer stages need to link to the downloadable file by the final path
        return


def get_raw_content(element: Element) -> str:
    """Get the pure text content of an element."""
    content = ""
    for child in element.children:
        if isinstance(child, RawText):
            content += child.children
        elif isinstance(child, InlineHTML):
            continue
        elif isinstance(child, str):  # link titles, etc.
            content += child
        else:
            content += get_raw_content(child)
    return content


def add_heading_anchors(document: Document, heading_id_prefix: str) -> Document:
    """Add GitHub-style slugs as `id` attributes on `Heading` elements.

    While Marko has a toc extension, it doesn't handle recurring heading anchors,
    or give much flexibility in what the rendered HTML looks like
    """
    anchor_counter = Counter()
    for child in document.children:
        if not isinstance(child, Heading):
            continue

        content = get_raw_content(child)
        default_anchor = slugify(content)
        if len(default_anchor) == 0:
            # entirely HTML headings will result in empty anchors...
            # if you're doing that you should probably just include an ID in your HTML
            logger.warning(f"Generated heading anchor for {child} is empty!")

        if anchor_counter[default_anchor] > 0:
            anchor = default_anchor + f"-{anchor_counter[default_anchor]}"
        else:
            anchor = default_anchor
        anchor_counter[default_anchor] += 1

        # prepend the id to reduce chance of collisions
        child.id = heading_id_prefix + anchor

    return document


def update_link_dests(element: Element, file: Path, tree: TreeSpan) -> Element:
    """Look for links in `element`, and ensure they point to the correct final path."""
    if isinstance(element, str):
        return element

    if isinstance(element, Link):
        linked_leaf = fetch_linked_leaf(element, file.parent, tree)
        if linked_leaf is not None:
            # would like to use dest_file.relative_to(parent_directory, walk_up=True)
            # but that's only available in 3.12+
            new_dest = os.path.relpath(
                tree.leaves["final_path"][linked_leaf],
                start=file.parent,
            )
            if "#" in element.dest:
                new_dest += element.dest[element.dest.index("#") :]

            logger.debug(f"Updating link in {file} from {element.dest} to {new_dest}")
            element.dest = new_dest

    for child in element.children:
        child = update_link_dests(child, file, tree)

    return element


def markdown_to_html(
    markdown: str,
    tree: TreeSpan | None = None,
    file: Path | None = None,
    heading_id_prefix: str | None = None,
) -> str:
    """Main function of the TransformMarkdown stage."""
    # WARNING: The Markdown class is not thread-safe.
    # Create a new instance for each thread.
    marko_object = Markdown(
        extensions=["gfm", WrappedTables], renderer=CambiumHTMLRenderer
    )

    document = marko_object.parse(markdown)

    if heading_id_prefix is not None:
        document = add_heading_anchors(document, heading_id_prefix)

    if file is not None:
        document = update_link_dests(document, file, tree)

    return marko_object.render(document)


def path_matches_patterns(path: Path, patterns: dict[str, list[str]]) -> bool:
    """Check if a path matches any item in `patterns`.

    Where `patterns` is formatted as the output from `config.sort_user_paths`.
    """
    if f"/{path}" in patterns["paths"]:
        return True

    if path.name in patterns["names"]:
        return True

    return any(re.match(regex, str(path)) for regex in patterns["globs"])


def get_relative_path_modifier(final_path: Path) -> str:
    """String to prepend to a path to get from the path up to build."""
    return "../" * len(final_path.parent.parents)
