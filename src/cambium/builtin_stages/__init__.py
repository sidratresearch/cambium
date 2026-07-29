"""Built-in Stages Initialization"""

from . import (
    check_links,
    ensure_index_pages,
    identify_metadata,
    sitemap,
    templating_markdown,
    transform_markdown,
    url_encode_filenames,
    write_reports,
)
from .pagefind_search import pagefind_search

__all__ = [
    "check_links",
    "ensure_index_pages",
    "identify_metadata",
    "pagefind_search",
    "sitemap",
    "templating_markdown",
    "transform_markdown",
    "url_encode_filenames",
    "write_reports",
]
