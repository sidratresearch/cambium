"""Utility functions working with markdown and HTML text."""

from __future__ import annotations

import copy
import html
import logging
import os
import re
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

from marko import Markdown, MarkoExtension, block, inline
from marko.element import Element
from marko.ext import gfm
from marko.helpers import render_dispatch
from marko.html_renderer import HTMLRenderer
from slugify import slugify

from .other_utils import fetch_leaf_from_href, split_respecting_quotes

if TYPE_CHECKING:
    from ..tree import TreeSpan

logger = logging.getLogger(__name__)


@dataclass()
class _ElementAttributeSet:
    """Hold parsed contents from curly brackets.

    Using dataclass to make it simple to instantiate with defaults and check
    equality - mostly for ease of testing.
    """

    classes: list[str] = field(default_factory=list)
    id: str | None = None
    simple_attrs: list[str] = field(default_factory=list)
    keyval_attrs: list[tuple[str, str]] = field(default_factory=list)

    @classmethod
    def from_str(cls, string: str) -> "_ElementAttributeSet":
        """Parse the contents of curly braces into an `ElementAttributeSet`."""
        items = split_respecting_quotes(string, r"\s")
        ids, result = [], _ElementAttributeSet()

        # regex for how a class or id can be named
        class_or_id_name = r"(\S*)"

        for i in items:
            if re.fullmatch(r"\." + class_or_id_name, i) is not None:
                result.classes.append(i[1:])
                continue
            if re.fullmatch("#" + class_or_id_name, i) is not None:
                ids.append(i[1:])
                continue

            attr_parts = split_respecting_quotes(i, "=")
            if len(attr_parts) == 1:
                result.simple_attrs.append(i)
                continue
            if len(attr_parts) == 2:
                result.keyval_attrs.append(tuple(attr_parts))
                continue

            raise RuntimeError(f"Don't know what to do with {i}")

        if len(ids) > 1:
            raise RuntimeError(f"Can't have multiple IDs, found {ids}")

        if len(ids) == 1:
            result.id = ids[0]

        return result

    @classmethod
    def from_element(cls, element: Element) -> "_ElementAttributeSet":
        result = _ElementAttributeSet()

        if hasattr(element, "classes"):
            result.classes = element.classes
        if hasattr(element, "id"):
            result.id = element.id
        if hasattr(element, "simple_attrs"):
            result.simple_attrs = element.simple_attrs
        if hasattr(element, "keyval_attrs"):
            result.keyval_attrs = element.keyval_attrs

        return result

    def apply_to_element(self, element: Element) -> None:
        """Attach attributes to an element for rendering."""
        if not hasattr(element, "classes"):
            element.classes = self.classes.copy()
        if not hasattr(element, "id"):
            element.id = self.id
        if not hasattr(element, "simple_attrs"):
            element.simple_attrs = self.simple_attrs.copy()
        if not hasattr(element, "keyval_attrs"):
            element.keyval_attrs = self.keyval_attrs.copy()


class _CambiumHTMLMixin(gfm.renderer.GFMRendererMixin):
    """Custom renderer class to support Cambium-specific features."""

    # --------------------------------------------------------------------#
    #                        Custom functionality                         #
    # --------------------------------------------------------------------#
    wrapper_class_template = "cambium-{tag}-holder"

    @classmethod
    def wrap_anything(cls, html_string: str, tag: str) -> str:
        """Wrap a string in a Cambium holder div."""
        css_class = cls.wrapper_class_template.format(tag=tag)
        return f'<div class="{css_class}">{html_string}</div>\n'

    @staticmethod
    def wrap_as(tag_name: str) -> Callable[..., str]:
        """Decorator to call `wrap_anything` on the result of a function."""

        def decorator(render_fn: Callable[[Element], str]) -> str:
            def wrapper(renderer: HTMLRenderer, element: Element) -> str:
                result = render_fn(renderer, element)
                return _CambiumHTMLMixin.wrap_anything(result, tag_name)

            return wrapper

        return decorator

    def build_attr_string(self, element: Element) -> str:
        """Build an attribute string (id, classes, etc.) for an HTML tag."""
        self.ensure_attributes(element)
        string = ""
        if element.id is not None:
            string += f' id="{element.id}"'
        if len(element.classes) > 0:
            # using dict.fromkeys to deduplicate while maintaining order
            class_string = " ".join(dict.fromkeys(element.classes))
            string += f' class="{class_string}"'
        if len(element.simple_attrs) > 0:
            for attr in element.simple_attrs:
                string += f" {attr}"
        if len(element.keyval_attrs) > 0:
            for key, value in element.keyval_attrs:
                string += f" {key}={value}"

        return string

    def render_with_closing(
        self,
        element: Element,
        tag_name: str,
        newline_after_opening: bool = False,
        contents: str | None = None,
    ) -> str:
        """Render an arbitrary non-self-closing HTML tag."""
        attrs = self.build_attr_string(element)
        spacing = "\n" if newline_after_opening else ""
        if contents is None:
            contents = self.render_children(element)

        return f"<{tag_name}{attrs}>{spacing}{contents}</{tag_name}>"

    def render_self_closing(self, element: Element, tag_name: str) -> str:
        """Render an arbitrary self-closing HTML tag."""
        attrs = self.build_attr_string(element)
        return f"<{tag_name}{attrs} />"

    def ensure_attributes(self, element: Element) -> None:
        """Create an empty set of attributes on `element`."""
        _ElementAttributeSet().apply_to_element(element)

    # --------------------------------------------------------------------#
    #            Simple overrides to use custom functionality             #
    # --------------------------------------------------------------------#

    # NOTE: skipping paragraphs, list items, code blocks, and inline elements

    @render_dispatch(HTMLRenderer)
    def render_list(self, element: block.List) -> str:
        """Use custom system for applying attributes to render lists."""
        tag = "ul"
        if element.ordered:
            tag = "ol"
            if element.start != 1:
                self.ensure_attributes(element)
                element.keyval_attrs.append(("start", f'"{element.start}"'))

        return self.render_with_closing(element, tag, newline_after_opening=True) + "\n"

    @render_dispatch(HTMLRenderer)
    def render_quote(self, element: block.Quote) -> str:
        """Use custom system for applying attributes to render headings."""
        return (
            self.render_with_closing(element, "blockquote", newline_after_opening=True)
            + "\n"
        )

    @render_dispatch(HTMLRenderer)
    def render_fenced_code(self, element: block.FencedCode) -> str:
        """Use custom system for applying attributes to render code blocks.

        Indented code blocks call this function as well.
        """
        self.ensure_attributes(element)
        if element.lang:
            element.classes.append(f"language-{self.escape_html(element.lang)}")
        return (
            "<pre>"
            + self.render_with_closing(
                element, "code", contents=html.escape(element.children[0].children)
            )
            + "</pre>\n"
        )

    @render_dispatch(HTMLRenderer)
    def render_heading(self, element: block.Heading) -> str:
        """Use custom system for applying attributes to render headings."""
        return self.render_with_closing(element, f"h{element.level}") + "\n"

    @render_dispatch(HTMLRenderer)
    def render_link(self, element: inline.Link) -> str:
        """Use custom system for applying attributes to render links."""
        self.ensure_attributes(element)
        if element.title:  # TODO: check where a link might get a title from...
            element.keyval_attrs.append(("title", self.escape_html(element.title)))
        element.keyval_attrs.append(("href", f'"{self.escape_url(element.dest)}"'))
        return self.render_with_closing(element, "a")

    # no wrap_as decorator as the use of a wrapping div is conditional
    @render_dispatch(HTMLRenderer)
    def render_image(self, element: inline.Image) -> str:
        """Use custom system for applying attributes to render images."""
        self.ensure_attributes(element)
        if element.title:  # TODO: check where a link might get a title from...
            element.keyval_attrs.append(("title", self.escape_html(element.title)))
        element.keyval_attrs.append(("src", f'"{self.escape_url(element.dest)}"'))

        # use the plain text renderer to extract the alt text
        original_renderer = self.render
        self.render = self.render_plain_text
        alt = self.render_children(element)
        self.render = original_renderer

        element.keyval_attrs.append(("alt", f'"{alt}"'))

        img = self.render_self_closing(element, "img")

        if hasattr(element, "no_cambium_wrap") and element.no_cambium_wrap:
            return img
        return wrap_with_div(img, "img")

    @render_dispatch(HTMLRenderer)
    @wrap_as("table")
    def render_table(self, element: gfm.elements.Table) -> str:
        """Use custom system for applying attributes to render tables."""
        head, *body = element.children
        theader = f"<thead>\n{self.render(head)}</thead>"
        tbody = ""
        if body:
            tbody = "\n<tbody>\n{}</tbody>".format(
                "".join(self.render(row) for row in body)
            )

        return self.render_with_closing(
            element, "table", newline_after_opening=True, contents=theader + tbody
        )


def wrap_with_div(html_string: str, tag_being_wrapped: str) -> str:
    """Add a `div` around an HTML string with a Cambium-specific class.

    Utility function to be imported and used by stages.
    """
    return _CambiumHTMLMixin.wrap_anything(html_string, tag_being_wrapped)


def get_element_text(element: Element) -> str:
    """Get the pure text content of an element."""
    content = ""
    for child in element.children:
        if isinstance(child, inline.RawText):
            content += child.children
        elif isinstance(child, inline.InlineHTML):
            continue
        elif isinstance(child, str):  # link titles, etc.
            content += child
        else:
            content += get_element_text(child)
    return content


def add_heading_anchors(
    document: block.Document, heading_id_prefix: str
) -> block.Document:
    """Add GitHub-style slugs as `id` attributes on `Heading` elements.

    While Marko has a toc extension, it doesn't handle recurring heading anchors,
    or give much flexibility in what the rendered HTML looks like
    """
    anchor_counter = Counter()
    for child in document.children:
        if not isinstance(child, block.Heading):
            continue

        if hasattr(child, "id") and child.id is not None:
            continue

        content = get_element_text(child)
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
        extensions=["gfm", MarkoExtension(renderer_mixins=[_CambiumHTMLMixin])],
        renderer=HTMLRenderer,
    )

    document = marko_object.parse(markdown)

    # a macro that happens here should give back an HTML string that we can maybe
    # wrap into a Marko HTML block
    # to prevent macros from calling other macros we could have a sentinel value

    document = _apply_comment_attributes(document)
    document = _apply_inline_attributes(document)

    document.children = _unwrap_images(document.children)

    if heading_id_prefix is not None:
        document = add_heading_anchors(document, heading_id_prefix)

    if file is not None:
        document = _update_link_dests(document, file, tree)

    return marko_object.render(document)


def _parse_str_as_attrs(string: str) -> _ElementAttributeSet | None:
    """Parse a string as a set of attributes to apply - or return None."""
    is_attr_string = re.fullmatch(r"\{.*\}", string) is not None
    if not is_attr_string:
        logger.debug(f"{string} is not a parseable comment (no brackets)")
        return

    try:
        return _ElementAttributeSet.from_str(string[1:-1])
    except ValueError as e:
        raise RuntimeError(f"Error parsing comment {string}: {e}")


def _apply_inline_attributes(element: Element) -> Element:
    """Parse curly braces in certain element types as HTML attributes."""
    if isinstance(element, str):
        return element

    # work with fenced code blocks
    if isinstance(element, block.FencedCode):
        # in the info string, the first text is taken as the language,
        # and anything following a space is put in "extra", so if no language
        # was given, the attribute string will be in element.lang
        if element.extra:
            attr_match = re.fullmatch(r"(\{.*\})", element.extra)
        elif element.lang:
            attr_match = re.fullmatch(r"(\{.*\})", element.lang)
            if attr_match is not None:
                element.lang = ""
        else:  # no lang or attrs
            return element

        if attr_match is None:
            return element

        attributes = _parse_str_as_attrs(attr_match.group(1).strip())
        if attributes is not None:
            attributes.apply_to_element(element)

        return element

    # work with links/images, where the final element in the title is plain text
    if (
        isinstance(element, (inline.Image, inline.Link))
        and len(element.children) > 0
        and isinstance(element.children[-1], inline.RawText)
    ):
        final_text = get_element_text(element.children[-1])

        title_pattern = "(.*?)"  # non-greedily match everything
        attributes_pattern = r"(\{.*\})"  # capture including curlies
        attr_match = re.fullmatch(
            f"{title_pattern}\\s*{attributes_pattern}", final_text
        )

        if attr_match is None:
            return element

        title, attributes = attr_match.group(1), _parse_str_as_attrs(
            attr_match.group(2).strip()
        )
        if attributes is not None:
            # update the attributes and excise the curly braces from the displayed title
            attributes.apply_to_element(element)
            element.children[-1].children = title

        return element

    for child in element.children:
        child = _apply_inline_attributes(child)

    return element


def _apply_comment_attributes(document: block.Document) -> block.Document:
    """Parse HTML comments into attributes applied to the next block-level item."""
    new_document = copy.deepcopy(document)
    new_document.children = []

    for i in range(len(document.children) - 1):
        # current_el is an element which might be a parseable comment
        # next_el is an element which might be modified
        current_el, next_el = document.children[i], document.children[i + 1]

        # default to retaining the element that might be a meta-comment
        new_document.children.append(current_el)

        # skip if this isn't a one-line HTML block followed by a non-HTML element
        if isinstance(next_el, (block.HTMLBlock, block.BlankLine)):
            continue
        if (not isinstance(current_el, block.HTMLBlock)) or (
            len(current_el.body.splitlines()) > 1
        ):
            continue

        start, end = "<!--+", "-+->"
        comment_contents = re.fullmatch(f"{start}(.*?){end}", current_el.body.strip())

        # skip if the current element isn't a comment
        if comment_contents is None:
            continue

        attributes = _parse_str_as_attrs(comment_contents.group(1).strip())

        # skip if the comment didn't parse into attributes
        if attributes is None:
            continue

        attributes.apply_to_element(next_el)

        # remove the meta-comment element
        new_document.children.pop()

    # push the final element over to the new document
    new_document.children.append(document.children[-1])

    return new_document


def _add_no_wrap(element: Element) -> Element:
    """Add `no_cambium_wrap` attributes to all Image elements.

    Indicates to the HTMLRenderer not to include a wrapping `div`
    """
    if isinstance(element, (str, inline.RawText)) or not hasattr(element, "children"):
        return element

    if isinstance(element, inline.Image):
        element.no_cambium_wrap = True
        return element

    for child in element.children:
        child = _add_no_wrap(child)

    return element


def _unwrap_images(elements: list[Element]) -> list[Element]:
    """Check for paragraphs that contain only images and remove the outer paragraph."""
    new_list = []

    for element in elements:
        if (
            isinstance(element, (str, inline.RawText))
            or not hasattr(element, "children")
            or isinstance(element.children, str)  # children of codespans are str
        ):
            new_list.append(element)

        elif isinstance(element, block.Paragraph):
            if all(
                isinstance(child, (inline.Image, inline.LineBreak))
                for child in element.children
            ):
                # do the unwrapping for an image-only paragraph
                attrs = _ElementAttributeSet.from_element(element)
                for child in element.children:
                    if isinstance(child, inline.Image):
                        attrs.apply_to_element(child)
                    new_list.append(child)
            else:
                # not an image-only paragraph - add the no-wrap tag to any images
                new_list.append(_add_no_wrap(element))

        else:
            element.children = _unwrap_images(element.children)
            new_list.append(element)

    return new_list


def _update_link_dests(element: Element, file: Path, tree: TreeSpan) -> Element:
    """Look for links in `element`, and ensure they point to the correct final path."""
    if isinstance(element, str):
        return element

    if isinstance(element, inline.Link):
        linked_leaf = fetch_leaf_from_href(element.dest, file.parent, tree)
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
        child = _update_link_dests(child, file, tree)

    return element
