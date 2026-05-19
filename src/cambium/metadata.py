"""Cambium Page Metadata Structure and Handlers"""

from __future__ import annotations

import logging
from typing import Optional

from pydantic import BaseModel


class LeafMetadata(BaseModel):
    """Leaf Metadata Object

    Contains all Page Metadata for each Leaf

    """

    title: Optional[str] = None
    """Page Title"""
