"""Built-in Stages Initialization"""

from . import (
    add_placeholder_index,
    identify_metadata,
    sitemap,
    templating_markdown,
    transform_markdown,
    url_encode_filenames,
)
from .pagefind_search import pagefind_search

__all__ = [
    "pagefind_search",
    "add_placeholder_index",
    "identify_metadata",
    "sitemap",
    "templating_markdown",
    "transform_markdown",
    "url_encode_filenames",
]
