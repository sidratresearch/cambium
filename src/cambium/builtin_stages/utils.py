from marko import Markdown
from marko.block import Heading
from marko.html_renderer import HTMLRenderer
from marko.inline import Link


class CambiumHTMLRenderer(HTMLRenderer):
    """Custom renderer class to support Cambium-specific features"""

    def render_link(self, element: Link) -> str:
        """Rewrites `.md` links to `.HTML`"""
        if element.dest.endswith(".md"):
            element.dest = element.dest[: element.dest.rindex(".md")] + ".html"
        return super().render_link(element)

    def render_heading(self, element: Heading) -> str:
        """Adds anchor links from an `id` attribute"""
        heading_template = '<h{level} id="{id}">{children}</h{level}>\n'
        return heading_template.format(
            level=element.level, id=element.id, children=self.render_children(element)
        )


def markdown_to_html(markdown: str) -> str:
    """Main function of the TransformMarkdown stage"""
    # WARNING: The Markdown class is not thread-safe.
    # Create a new instance for each thread.
    marko_object = Markdown(extensions=["gfm"], renderer=CambiumHTMLRenderer)

    document = marko_object.parse(markdown)
    document = add_heading_anchors(document)

    return marko_object.render(document)
