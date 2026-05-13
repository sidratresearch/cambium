from marko import Markdown
from marko.html_renderer import HTMLRenderer
from marko.inline import Link
from typing_extensions import override


class CambiumHTMLRenderer(HTMLRenderer):
    @override
    def render_link(self, element: Link) -> str:
        if element.dest.endswith(".md"):
            element.dest = element.dest[: element.dest.rindex(".md")] + ".html"
        return super().render_link(element)


def markdown_to_html(markdown: str) -> str:
    # WARNING: The Markdown class is not thread-safe. Create a new instance for each thread.
    return Markdown(extensions=["gfm"], renderer=CambiumHTMLRenderer).convert(markdown)
