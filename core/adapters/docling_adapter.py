from typing import List, Tuple
import hashlib
import base64
from pathlib import Path
from docling.document_converter import DocumentConverter
from docling_core.types.doc import (
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
from .docx_parser import parse_docx_to_internal_doc

def _detect_file_type(file_path: str) -> str:
    """Detect file type based on extension."""
    file_path_lower = file_path.lower()
    if file_path_lower.endswith('.docx'):
        return 'docx'
    elif file_path_lower.endswith('.pdf'):
        return 'pdf'
    else:
        return 'unknown'

def _map_inlines_from_text_item(text_item: TextItem) -> List[Inline]:
    """Maps a docling TextItem to a list of Inline AST nodes."""
    return [InlineText(content=text_item.text)]

def _extract_image_data(picture_item: PictureItem) -> bytes:
    """Extract binary image data from PictureItem."""
    image_ref = picture_item.image
    if hasattr(image_ref, 'pil_image') and image_ref.pil_image:
        # Convert PIL image to bytes
        import io
        img_buffer = io.BytesIO()
        image_ref.pil_image.save(img_buffer, format='PNG')
        return img_buffer.getvalue()
    elif hasattr(image_ref, 'uri') and image_ref.uri:
        # Extract from data URI (data:image/png;base64,...)
        uri = image_ref.uri
        if uri.startswith('data:') and ';base64,' in uri:
            base64_data = uri.split(';base64,')[1]
            return base64.b64decode(base64_data)
    
    # Fallback - return empty bytes if we can't extract image data
    return b''

def parse_with_docling(file_path: str) -> Tuple[InternalDoc, List[ResourceRef]]:
    """
    Parses a document file using appropriate parser based on file type.
    Routes DOCX files to specialized XML parser for better chapter extraction.
    Uses docling for PDF and other formats.
    """
    file_type = _detect_file_type(file_path)
    
    if file_type == 'docx':
        # Use specialized DOCX parser for better chapter extraction
        return parse_docx_to_internal_doc(file_path)
    
    # Use docling for PDF and other formats
    converter = DocumentConverter()
    result = converter.convert(file_path)
    document = result.document

    blocks: List[Block] = []
    resources: List[ResourceRef] = []
    
    # Use iterate_items to get items in document order
    for item_tuple in document.iterate_items():
        item, page_num = item_tuple
        
        if isinstance(item, TextItem):
            # Check if this is a heading based on label
            if hasattr(item, 'label') and str(item.label) in ['title', 'heading', 'section_header']:
                # Treat as level 1 heading
                blocks.append(Heading(level=1, text=item.text))
            elif hasattr(item, 'formatting') and item.formatting:
                # Check if text has bold formatting that might indicate a heading
                # For now, just create paragraphs - headings will be fixed by structure transforms later
                blocks.append(Paragraph(inlines=_map_inlines_from_text_item(item)))
            else:
                blocks.append(Paragraph(inlines=_map_inlines_from_text_item(item)))
                
        elif isinstance(item, PictureItem):
            # Extract image data
            content = _extract_image_data(item)
            
            if content:  # Only create resource if we have actual image data
                resource_id = f"img_{len(resources) + 1:03d}"
                sha256 = hashlib.sha256(content).hexdigest()
                
                # Try to determine MIME type
                mime_type = "image/png"  # Default
                if hasattr(item.image, 'pil_image') and item.image.pil_image:
                    pil_format = item.image.pil_image.format
                    if pil_format:
                        mime_type = f"image/{pil_format.lower()}"
                
                resource = ResourceRef(
                    id=resource_id,
                    mime_type=mime_type,
                    content=content,
                    sha256=sha256,
                )
                resources.append(resource)
                
                # Get alt text from caption or generate default
                caption_text = getattr(item, 'caption_text', None)
                if caption_text and hasattr(caption_text, '__call__'):
                    # If caption_text is a method, call it
                    try:
                        alt_text = str(caption_text())
                    except Exception:
                        alt_text = f"Image {len(resources)}"
                elif isinstance(caption_text, str):
                    alt_text = caption_text
                else:
                    alt_text = f"Image {len(resources)}"
                
                blocks.append(Image(alt=alt_text, resource_id=resource_id))

    internal_doc = InternalDoc(blocks=blocks)
    return internal_doc, resources