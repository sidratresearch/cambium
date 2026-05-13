from marko import Markdown
from marko.html_renderer import HTMLRenderer
from marko.inline import Link


class CambiumHTMLRenderer(HTMLRenderer):
    def render_link(self, element: Link) -> str:
        if element.dest.endswith(".md"):
            element.dest = element.dest[: element.dest.rindex(".md")] + ".html"
        return super().render_link(element)


def markdown_to_html(markdown: str) -> str:
    # TODO: move the instance declaration out of this function so we don't create a new instance every file
    return Markdown(extensions=["gfm"], renderer=CambiumHTMLRenderer).convert(markdown)
