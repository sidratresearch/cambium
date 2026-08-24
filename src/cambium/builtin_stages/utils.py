"""Utility functions for builtin stages."""

import copy
import html
import logging
import os
import re
import urllib
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

from marko import Markdown, MarkoExtension, block, inline
from marko.element import Element
from marko.ext import gfm
from marko.helpers import render_dispatch
from marko.html_renderer import HTMLRenderer
from slugify import slugify

from ..tree import TreeSpan

logger = logging.getLogger(__name__)


@dataclass()
class ElementAttributeSet:
    """Hold parsed contents from curly brackets.

    Using dataclass to make it simple to instantiate with defaults and check
    equality - mostly for ease of testing.
    """

    classes: list[str] = field(default_factory=list)
    id: str | None = None
    simple_attrs: list[str] = field(default_factory=list)
    keyval_attrs: list[tuple[str, str]] = field(default_factory=list)

    @classmethod
    def from_str(cls, string: str) -> "ElementAttributeSet":
        """Parse the contents of curly braces into an `AttributeSet`."""
        items = split_respecting_quotes(string, r"\s")
        ids, result = [], ElementAttributeSet()

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

            raise ValueError(f"Don't know what to do with {i}")

        if len(ids) > 1:
            raise ValueError(f"Can't have multiple IDs, found {ids}")

        if len(ids) == 1:
            result.id = ids[0]

        return result

    def apply_to_element(self, element: Element) -> None:
        """Attach attributes to an element for rendering."""
        if not hasattr(element, "classes"):
            element.classes = self.classes
        if not hasattr(element, "id"):
            element.id = self.id
        if not hasattr(element, "simple_attrs"):
            element.simple_attrs = self.simple_attrs
        if not hasattr(element, "keyval_attrs"):
            element.keyval_attrs = self.keyval_attrs


class CambiumHTMLMixin(gfm.renderer.GFMRendererMixin):
    """Custom renderer class to support Cambium-specific features."""

    # --------------------------------------------------------------------#
    #                        Custom functionality                         #
    # --------------------------------------------------------------------#
    wrapper_class_template = "cambium-{tag}-holder"

    @classmethod
    def wrap_anything(cls, html_string: str, tag: str) -> str:
        """Wrap a string in a Cambium holder div."""
        css_class = cls.wrapper_class_template.format(tag=tag)
        return f'<div class="{css_class}">{html_string}</div>'

    @staticmethod
    def wrap_as(tag_name: str) -> Callable[..., str]:
        """Decorator to call `wrap_anything` on the result of a function."""

        def decorator(render_fn: Callable[[Element], str]) -> str:
            def wrapper(renderer: HTMLRenderer, element: Element) -> str:
                result = render_fn(renderer, element)
                return CambiumHTMLMixin.wrap_anything(result, tag_name)

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
        ElementAttributeSet().apply_to_element(element)

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

    @render_dispatch(HTMLRenderer)
    @wrap_as("img")
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
        return self.render_self_closing(element, "img")

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


CambiumRenderingExtensions = MarkoExtension(renderer_mixins=[CambiumHTMLMixin])


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
    link_element: inline.Link, file_parent_directory: Path, tree: TreeSpan
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
        if isinstance(child, inline.RawText):
            content += child.children
        elif isinstance(child, inline.InlineHTML):
            continue
        elif isinstance(child, str):  # link titles, etc.
            content += child
        else:
            content += get_raw_content(child)
    return content


def is_attr_string(string: str) -> bool:
    """Check if a string should be parsed as a meta attribute string."""
    return re.fullmatch(r"\{.*\}", string) is not None


def parse_comment(comment: str) -> ElementAttributeSet | None:
    """Parse a comment as either attributes to apply or a macro command."""
    if not is_attr_string(comment):
        logger.debug(f"{comment} is not a parseable comment (no brackets)")
        return

    try:
        return ElementAttributeSet.from_str(comment[1:-1])
    except ValueError as e:
        raise ValueError(f"Error parsing comment {comment}: {e}")


def split_respecting_quotes(string: str, split_char: str) -> list[str]:
    """Split `string` on every `split_char`, unless double quotes are used.

    Double quotes can be escaped with a single backslash.
    https://stackoverflow.com/a/16710842
    """
    pattern = "(?:[^" + split_char + r'"]|"(?:\.|[^"])*")+'
    return re.findall(pattern, string)


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


def apply_inline_attributes(element: Element) -> Element:
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

        if attr_match is None:
            return element

        attributes = parse_comment(attr_match.group(1).strip())
        if attributes is not None:
            attributes.apply_to_element(element)

        return element

    # work with links/images, where the final element in the title is plain text
    if (
        isinstance(element, (inline.Image, inline.Link))
        and len(element.children) > 0
        and isinstance(element.children[-1], inline.RawText)
    ):
        final_text = get_raw_content(element.children[-1])

        title_pattern = "(.*?)"  # non-greedily match everything
        attributes_pattern = r"(\{.*\})"  # capture including curlies
        attr_match = re.fullmatch(
            f"{title_pattern}\\s*{attributes_pattern}", final_text
        )

        if attr_match is None:
            return element

        title, attributes = attr_match.group(1), parse_comment(
            attr_match.group(2).strip()
        )
        if attributes is not None:
            # update the attributes and excise the curly braces from the displayed title
            attributes.apply_to_element(element)
            element.children[-1].children = title

        return element

    for child in element.children:
        child = apply_inline_attributes(child)

    return element


def apply_attribute_comments(document: block.Document) -> block.Document:
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

        attributes = parse_comment(comment_contents.group(1).strip())

        # skip if the comment didn't parse into attributes
        if attributes is None:
            continue

        attributes.apply_to_element(next_el)

        # remove the meta-comment element
        new_document.children.pop()

    # push the final element over to the new document
    new_document.children.append(document.children[-1])

    return new_document


def update_link_dests(element: Element, file: Path, tree: TreeSpan) -> Element:
    """Look for links in `element`, and ensure they point to the correct final path."""
    if isinstance(element, str):
        return element

    if isinstance(element, inline.Link):
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
        extensions=["gfm", CambiumRenderingExtensions],
        renderer=HTMLRenderer,
    )

    document = marko_object.parse(markdown)

    document = apply_attribute_comments(document)
    document = apply_inline_attributes(document)

    if heading_id_prefix is not None:
        document = add_heading_anchors(document, heading_id_prefix)

    if file is not None:
        document = update_link_dests(document, file, tree)

    return marko_object.render(document)


def get_relative_path_modifier(final_path: Path) -> str:
    """String to prepend to a path to get from the path up to build."""
    return "../" * len(final_path.parent.parents)
