"""Built-in Stages Initialization"""

from . import (
    ensure_index_pages,
    identify_metadata,
    sitemap,
    templating_markdown,
    transform_markdown,
    url_encode_filenames,
)
from .pagefind_search import pagefind_search

__all__ = [
    "ensure_index_pages",
    "identify_metadata",
    "pagefind_search",
    "sitemap",
    "templating_markdown",
    "transform_markdown",
    "url_encode_filenames",
]
