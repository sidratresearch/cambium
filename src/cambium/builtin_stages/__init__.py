"""Built-in Stages Initialization."""

from .check_links import CheckLinks
from .ensure_index_pages import EnsureIndexPages
from .identify_metadata import IdentifyMetadata
from .pagefind_search.pagefind_search import PagefindSearch
from .preview_csv.preview_csv import PreviewCSV
from .sitemap import AddSitemap
from .template_markdown import TemplateMarkdown
from .transform_markdown import TransformMarkdown
from .url_encode_filenames import URLEncodeFilenames
from .write_reports.write_reports import WriteReports

__all__ = [
    "AddSitemap",
    "CheckLinks",
    "EnsureIndexPages",
    "IdentifyMetadata",
    "PagefindSearch",
    "PreviewCSV",
    "TemplateMarkdown",
    "TransformMarkdown",
    "URLEncodeFilenames",
    "WriteReports",
]
