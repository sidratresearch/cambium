"""Cambium Page Metadata Structure and Handlers"""

from __future__ import annotations

import logging
from collections import defaultdict
from typing import Any, Optional

from pydantic import BaseModel

logger = logging.getLogger(__name__)

StageMetadata = defaultdict(lambda: None)


class LeafMetadata(BaseModel):
    """Leaf Metadata Object

    Contains all Page Metadata for each Leaf

    """

    title: Optional[str] = None
    """Page Title"""

    initial_filesize: Optional[int] = None
    """Size of the original file in bytes"""

    modification_time: Optional[str] = None
    """Modification time of original file, as UTC ISO string"""

    table_of_contents: Optional[str] = None
    """HTML string with headings, only defined for markdown files"""

    # in addition to the "loose" default metadata items we provide, include a "stage"
    # or "extra" attribute here that maps stage name to a dict of that stage's custom
    # metadata items
    # that dict should be a defaultdict(lambda: None)
    # if a stage wants to rewrite one of the default items, it should instead create
    # its own copy within it's dictionary

    stage_metadata: dict[str, dict[str, Any]] = defaultdict(lambda: StageMetadata)
