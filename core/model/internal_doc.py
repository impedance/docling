from __future__ import annotations
from typing import List, Union, Literal
from pydantic import BaseModel, Field

# --- Inline Elements ---

class Text(BaseModel):
    """Represents plain text."""
    type: Literal["text"] = "text"
    content: str

class Bold(BaseModel):
    """Represents bold text."""
    type: Literal["bold"] = "bold"
    content: str

class Italic(BaseModel):
    """Represents italic text."""
    type: Literal["italic"] = "italic"
    content: str

class Link(BaseModel):
    """Represents a hyperlink."""
    type: Literal["link"] = "link"
    content: str
    href: str

Inline = Union[Text, Bold, Italic, Link]

# --- Block Elements ---

class Paragraph(BaseModel):
    """A sequence of inline elements."""
    type: Literal["paragraph"] = "paragraph"
    inlines: List[Inline] = Field(default_factory=list)

class Heading(BaseModel):
    """A document heading."""
    type: Literal["heading"] = "heading"
    level: int = Field(..., gt=0, le=6)
    text: str

class Image(BaseModel):
    """An image reference."""
    type: Literal["image"] = "image"
    alt: str = ""
    resource_id: str  # Corresponds to a ResourceRef

class ListItem(BaseModel):
    """An item in a list, can contain nested blocks."""
    type: Literal["list_item"] = "list_item"
    blocks: List["Block"] = Field(default_factory=list)

class ListBlock(BaseModel):
    """An ordered or unordered list."""
    type: Literal["list"] = "list"
    ordered: bool = False
    items: List[ListItem] = Field(default_factory=list)

class TableCell(BaseModel):
    """A cell in a table."""
    type: Literal["table_cell"] = "table_cell"
    blocks: List["Block"] = Field(default_factory=list)

class TableRow(BaseModel):
    """A row in a table."""
    type: Literal["table_row"] = "table_row"
    cells: List[TableCell] = Field(default_factory=list)

class Table(BaseModel):
    """A table."""
    type: Literal["table"] = "table"
    header: TableRow
    rows: List[TableRow] = Field(default_factory=list)

Block = Union[Paragraph, Heading, Image, ListBlock, Table]

# Update forward references for nested models
ListItem.model_rebuild()
TableCell.model_rebuild()

class InternalDoc(BaseModel):
    """Represents the entire document as a tree of blocks."""
    blocks: List[Block] = Field(default_factory=list)
