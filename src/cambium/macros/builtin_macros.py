"""Macro functions built into Cambium."""

from logging import getLogger

from ..metadata import TableOfContentsEntry
from ..tree import TreeSpan
from .macro_utils import Macro, MacroArgs, MacroKwargs

logger = getLogger(__name__)


class CambiumLink(Macro):
    """Return a link to Cambium."""

    @classmethod
    def apply(cls, *args, **kwargs) -> str:
        return '<a href="https://buildwithcambium.org">Cambium</a>'


class CaptionedImage(Macro):
    """Show an image as a <figure> with a caption."""

    @classmethod
    def apply(
        cls,
        leaf_uuid: str,
        tree: TreeSpan,
        content: str | None = None,
        args: MacroArgs = [],
        kwargs: MacroKwargs = {},
    ) -> str:
        if len(args) != 1:
            raise RuntimeError("need image as only arg")
        src = args[0]
        if not isinstance(src, str):
            raise RuntimeError("image should be string")

        attrs = {"src": f'"{src}"'}

        alt = kwargs.get("alt", "").strip()
        if len(alt) == 0:
            logger.warning("no alt")
        else:
            attrs["alt"] = f'"{alt}"'

        if content is None or len(content.strip()) == 0:
            logger.warning("no caption")

        attrs = " ".join([f"{key}={value}" for key, value in attrs.items()])

        from ..utils.md_html_utils import wrap_with_div

        string = wrap_with_div(
            f"<figure>\n<img {attrs}/>\n<figcaption>{content.strip()}</figcaption>\n</figure>",
            "img",
        )

        return string


class TableOfContents(Macro):
    """Output a table of contents for this page."""

    @classmethod
    def apply(
        cls, leaf_uuid: str, tree: TreeSpan, kwargs: MacroKwargs, **_kwargs
    ) -> str:
        # fetch TOC from metadata
        toc_entries = tree.leaves["metadata"][leaf_uuid].table_of_contents

        # fetch and validate arguments
        inline = kwargs.get("inline", False)
        mindepth = kwargs.get("mindepth", 2)
        maxdepth = kwargs.get("maxdepth", 6)
        if (
            not isinstance(mindepth, int)
            or not isinstance(maxdepth, int)
            or mindepth > maxdepth
            or not (1 <= mindepth <= 6)
            or not (1 <= maxdepth <= 6)
        ):
            raise RuntimeError(
                "mindepth and maxdepth must be integers [1,6] with mindepth <= maxdepth"
            )

        toc_string = ""
        if toc_entries is not None:
            toc_string = _render_toc(toc_entries, mindepth=mindepth, maxdepth=maxdepth)

        classes = ["cambium-table-of-contents"]
        if inline:
            classes.append("cambium-inline-table-of-contents")
        classes_string = " ".join(classes)
        return f'<nav class="{classes_string}">\n{toc_string}\n</nav>'


def _render_toc(
    headings: list[TableOfContentsEntry], mindepth: int = 1, maxdepth: int | None = None
) -> str:
    """Render a set of dictionaries as a nested <ul>.

    `mindepth = X` means "Only show items with heading level >= X"

    In future may want to port this whole thing to Jinja, but currently we
    don't need that level of customizability.
    Modification of marko's TocRenderMixin.render_toc
    """
    first_level = None
    last_level = None
    rv = []

    opening, closing = '<ul class="toc-level-{level}">\n', "</ul>\n"
    item_format = '<li><a href="#{slug}">{text}</a></li>'

    for heading in headings:
        level, slug, text = heading["level"], heading["id"], heading["text"]

        if level < mindepth or (maxdepth is not None and level > maxdepth):
            continue

        # initialize
        if first_level is None:
            first_level = mindepth
            last_level = level
            rv.append(opening.format(level=level))

        # step in
        if last_level == level - 1:
            rv.append("\t" * last_level + opening.format(level=level))
            last_level = level

        # step out
        while last_level > level:
            rv.append("\t" * level + closing)
            last_level -= 1
        rv.append("\t" * level + item_format.format(slug=slug, text=text) + "\n")

    if first_level is None or last_level is None:
        return ""

    for _ in range(first_level, last_level + 1):
        rv.append(closing)

    return "".join(rv).strip()
