"""Utility functions for builtin stages."""

import logging
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
from marko.inline import Image, Link
from slugify import slugify

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

    @render_dispatch(HTMLRenderer)
    def render_table(self, element: Element) -> str:
        """Wraps `table` tags in a div."""
        rendered_table = super().render_table(element)
        css_class = self.class_template.format(tag="table")
        return f"<div class='{css_class}'>{rendered_table}</div>"

    @render_dispatch(HTMLRenderer)
    def render_image(self, element: Image) -> str:
        """Wraps `img` tags in a div."""
        rendered_img = super().render_image(element)
        css_class = self.class_template.format(tag="img")
        return f"<div class='{css_class}'>{rendered_img}</div>"


WrappedTables = MarkoExtension(elements=[Table], renderer_mixins=[WrappedBlocksMixin])


def is_external_link(dest: str) -> bool:
    """Check if a link points to an external URL."""
    return any(dest.startswith(prefix) for prefix in ["http:", "https:", "www."])


def rewrite_urlsafe_links(
    element: Element, parent_directory: Path, links_to_update: dict[Path, Path]
) -> Element:
    """Replace image and link destinations in a markdown element with versions that are
    both url and filesystem safe.
    """
    if isinstance(element, str):
        return element

    if isinstance(element, (Link, Image)):
        if is_external_link(element.dest):
            return Element

        dest_path = parent_directory / element.dest
        dest_path_urldecoded = Path(urllib.parse.unquote(str(dest_path)))

        new_dest = element.dest

        if dest_path in links_to_update:
            new_dest = links_to_update[dest_path]
        elif dest_path_urldecoded in links_to_update:
            # dest path was pre-url encoded
            new_dest = links_to_update[dest_path_urldecoded]

        element.dest = new_dest

        return element

    for child in element.children:
        child = rewrite_urlsafe_links(child, parent_directory, links_to_update)
    return element


def resolve_internal_link(
    link: Path, parent_directory: Path, build_directory: Path
) -> Path:
    """Resolve internal paths as they may appear in user files.

    For "../a.html" located in "[root]/b/c.html", this returns "a.html"
    """
    full = (build_directory / parent_directory / link).resolve()
    build_abs = build_directory.absolute()
    try:
        return full.relative_to(build_abs)
    except ValueError:
        # definitionally both paths will be absolute
        # so the only option is full isn't within build
        raise ValueError(
            f"Error resolving internal link {link}, perhaps this file is outside the root directory?"
        )


def rewrite_md_links(
    element: Element,
    parent_directory: Path,
    links_to_update: list[Path],
    build_directory: Path,
) -> Element:
    """Change links to markdown files point to their transformed HTML versions."""
    if isinstance(element, str):
        return element

    if isinstance(element, Link):
        if is_external_link(element.dest):
            return Element

        if element.dest.startswith("#"):
            return Element

        resolved = resolve_internal_link(
            element.dest, parent_directory, build_directory
        )
        if "#" in resolved.name:
            resolved = resolved.with_name(resolved.name[: resolved.name.index("#")])

        if resolved in links_to_update:
            # TODO: handle .MD etc
            # TODO: change this to use TransformMarkdown._update_path
            element.dest = element.dest.replace(".md", ".html")

        return element

    for child in element.children:
        child = rewrite_md_links(
            child, parent_directory, links_to_update, build_directory
        )
    return element


def get_raw_content(element: Element) -> str:
    """Get the pure text content of an element."""
    content = ""
    for child in element.children:
        if isinstance(child, str):
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

        if anchor_counter[default_anchor] > 0:
            anchor = default_anchor + f"-{anchor_counter[default_anchor]}"
        else:
            anchor = default_anchor
        anchor_counter[default_anchor] += 1

        # prepend the id to reduce chance of collisions
        child.id = heading_id_prefix + anchor

    return document


def markdown_to_html(markdown: str, heading_id_prefix: str | None) -> str:
    """Main function of the TransformMarkdown stage."""
    # WARNING: The Markdown class is not thread-safe.
    # Create a new instance for each thread.
    marko_object = Markdown(
        extensions=["gfm", WrappedTables], renderer=CambiumHTMLRenderer
    )

    document = marko_object.parse(markdown)
    if heading_id_prefix is not None:
        document = add_heading_anchors(document, heading_id_prefix)

    return marko_object.render(document)
