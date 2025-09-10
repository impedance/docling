from typing import List, Tuple
import hashlib
from docling.document_converter import DocumentConverter
from docling_core.types.doc import (
    SectionHeaderItem,
    TextItem,
    PictureItem,
)

from core.model.internal_doc import (
    InternalDoc,
    Block,
    Heading,
    Paragraph,
    Image,
    Text as InlineText,
    Inline,
)
from core.model.resource_ref import ResourceRef

def _map_inlines_from_text_item(text_item: TextItem) -> List[Inline]:
    """Maps a docling TextItem to a list of Inline AST nodes."""
    return [InlineText(content=text_item.text)]

def parse_with_docling(file_path: str) -> Tuple[InternalDoc, List[ResourceRef]]:
    """
    Parses a document file using the real docling DocumentConverter
    and returns the InternalDoc AST and a list of extracted resources.
    """
    converter = DocumentConverter()
    result = converter.convert(file_path)
    document = result.document

    blocks: List[Block] = []
    resources: List[ResourceRef] = []
    
    # Combine all document items (texts, pictures, etc.) into a single list
    # and sort them by their position in the document to preserve the original order.
    all_items = sorted(
        document.texts + document.pictures,
        key=lambda item: item.position
    )

    for item in all_items:
        if isinstance(item, SectionHeaderItem):
            blocks.append(Heading(level=item.level, text=item.text))
        elif isinstance(item, TextItem):
            blocks.append(Paragraph(inlines=_map_inlines_from_text_item(item)))
        elif isinstance(item, PictureItem):
            resource_id = f"img_{len(resources) + 1}"
            content = item.content
            sha256 = hashlib.sha256(content).hexdigest()
            
            resource = ResourceRef(
                id=resource_id,
                mime_type=item.mimetype,
                content=content,
                sha256=sha256,
            )
            resources.append(resource)
            
            blocks.append(Image(alt=item.text or f"Image {len(resources)}", resource_id=resource_id))

    internal_doc = InternalDoc(blocks=blocks)
    return internal_doc, resources