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
