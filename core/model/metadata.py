from typing import List, Optional
from pydantic import BaseModel

class TocEntry(BaseModel):
    """A single entry in the Table of Contents."""
    level: int
    title: str
    anchor: str # Link anchor

class Metadata(BaseModel):
    """
    Contains metadata about the document.
    """
    title: Optional[str] = None
    authors: List[str] = []
    language: Optional[str] = None
    toc: List[TocEntry] = []
