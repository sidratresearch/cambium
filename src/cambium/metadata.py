"""Cambium Page Metadata Structure and Handlers"""

from __future__ import annotations

import logging
from typing import Optional

from pydantic import BaseModel

logger = logging.getLogger(__name__)


class LeafMetadata(BaseModel):
    """Leaf Metadata Object

    Contains all Page Metadata for each Leaf

    """

    title: Optional[str] = None
    """Page Title"""

    # add: filesize, original filename, modification time, etc.

    # in addition to the "loose" default metadata items we provide, include a "stage"
    # or "extra" attribute here that maps stage name to a dict of that stage's custom
    # metadata items
    # that dict should be a defaultdict(lambda: None)
    # if a stage wants to rewrite one of the default items, it should instead create
    # its own copy within it's dictionary
