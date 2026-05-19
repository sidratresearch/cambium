"""Cambium Page Metadata Structure and Handlers"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel

from .log import get_logger

logger = get_logger(__name__)


class LeafMetadata(BaseModel):
    """Leaf Metadata Object

    Contains all Page Metadata for each Leaf

    """

    title: Optional[str] = None
    """Page Title"""
