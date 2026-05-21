from collections import Counter
from pathlib import Path

from marko import Markdown
from marko.block import Document, Heading
from marko.element import Element
from marko.html_renderer import HTMLRenderer
from marko.inline import Link
from slugify import slugify


class CambiumHTMLRenderer(HTMLRenderer):
    """Custom renderer class to support Cambium-specific features"""

    def render_heading(self, element: Heading) -> str:
        """Adds anchor links from an `id` attribute"""
        heading_template = '<h{level} id="{id}">{children}</h{level}>\n'
        return heading_template.format(
            level=element.level, id=element.id, children=self.render_children(element)
        )


def is_external_link(dest: str) -> bool:
    return any(dest.startswith(prefix) for prefix in ["http:", "https:", "www."])


def rewrite_md_links(
    element: Element, parent_directory: Path, links_to_update: list[Path]
) -> Element:
    """Change links to markdown files point to their transformed HTML versions"""
    if isinstance(element, str):
        return element

    if isinstance(element, Link):
        if is_external_link(element.dest):
            return Element

        if (parent_directory / element.dest) in links_to_update:
            # TODO: handle .MD etc
            element.dest = element.dest.removesuffix(".md") + ".html"
        return element

    for child in element.children:
        child = rewrite_md_links(child, parent_directory, links_to_update)
    return element


def get_raw_content(element: Element) -> str:
    """Get the pure text content of an element"""
    content = ""
    for child in element.children:
        if isinstance(child, str):
            content += child
        else:
            content += get_raw_content(child)
    return content


def add_heading_anchors(document: Document) -> Document:
    """Add GitHub-style slugs as `id` attributes on `Heading` elements

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
        child.id = "cambium-header-anchor-" + anchor

    return document


def markdown_to_html(markdown: str) -> str:
    """Main function of the TransformMarkdown stage"""
    # WARNING: The Markdown class is not thread-safe.
    # Create a new instance for each thread.
    marko_object = Markdown(extensions=["gfm"], renderer=CambiumHTMLRenderer)

    document = marko_object.parse(markdown)
    document = add_heading_anchors(document)

    return marko_object.render(document)
