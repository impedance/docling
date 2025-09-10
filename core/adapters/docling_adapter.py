from typing import List, Tuple, Any, Dict
import hashlib
import base64

from docling.document_converter import DocumentConverter

from core.model.internal_doc import (
    InternalDoc,
    Block,
    Heading,
    Paragraph,
    Image,
    Text,
    Bold,
    Italic,
    Link,
    Inline,
)
from core.model.resource_ref import ResourceRef


def run_docling_parser(file_path: str) -> Dict[str, Any]:
    """
    Parses a document file using the real docling DocumentConverter
    and returns a structured dictionary compatible with our mapping functions.
    """
    # Initialize the docling converter
    converter = DocumentConverter()
    
    # Convert the document
    result = converter.convert(file_path)
    document = result.document
    
    # Extract metadata
    metadata = {
        "title": getattr(document, 'title', '') or "Untitled Document",
    }
    
    # Process pictures/images to create resources
    resources = {}
    for i, picture in enumerate(document.pictures):
        # Create a unique resource ID
        resource_id = f"img_{i + 1}"
        
        # For now, we'll handle image resources without actual binary data
        # This is a limitation of the current docling API - images are referenced but not embedded
        resources[resource_id] = {
            "mime_type": "image/png",  # Default mime type
            "content_b64": "",  # Empty for now - docling doesn't provide binary data directly
            "alt": getattr(picture, 'text', '') or f"Image {i + 1}",
        }
    
    # Process text elements to create blocks
    blocks = []
    
    # Process text items (headings, paragraphs, etc.)
    for text_item in document.texts:
        # Get the text content
        text_content = text_item.text if hasattr(text_item, 'text') else str(text_item)
        
        # Determine the block type based on docling's classification
        item_type = getattr(text_item, 'label', 'paragraph').lower()
        
        if 'title' in item_type or 'heading' in item_type or 'section' in item_type:
            # Extract heading level (default to 1 if not specified)
            level = 1
            if hasattr(text_item, 'level'):
                level = text_item.level
            elif 'h1' in item_type or '1' in item_type:
                level = 1
            elif 'h2' in item_type or '2' in item_type:
                level = 2
            elif 'h3' in item_type or '3' in item_type:
                level = 3
            
            blocks.append({
                "type": "heading",
                "level": level,
                "text": text_content
            })
        else:
            # Treat as paragraph with simple text inline
            blocks.append({
                "type": "paragraph",
                "inlines": [
                    {"type": "text", "content": text_content}
                ]
            })
    
    # Add image blocks for pictures
    for i, picture in enumerate(document.pictures):
        resource_id = f"img_{i + 1}"
        alt_text = getattr(picture, 'text', '') or f"Image {i + 1}"
        
        blocks.append({
            "type": "image",
            "alt": alt_text,
            "resource_id": resource_id
        })
    
    return {
        "metadata": metadata,
        "resources": resources,
        "blocks": blocks
    }

# --- Mapper ---

def _map_inlines(inline_data: List[Dict[str, Any]]) -> List[Inline]:
    """Maps a list of inline data from docling format to our AST models."""
    inlines = []
    for item in inline_data:
        type = item.get("type")
        if type == "text":
            inlines.append(Text(content=item.get("content", "")))
        elif type == "bold":
            inlines.append(Bold(content=item.get("content", "")))
        elif type == "italic":
            inlines.append(Italic(content=item.get("content", "")))
        elif type == "link":
            inlines.append(Link(content=item.get("content", ""), href=item.get("href", "")))
    return inlines

def _map_blocks(block_data: List[Dict[str, Any]]) -> List[Block]:
    """Maps a list of block data from docling format to our AST models."""
    blocks = []
    for item in block_data:
        type = item.get("type")
        if type == "heading":
            blocks.append(Heading(level=item.get("level", 1), text=item.get("text", "")))
        elif type == "paragraph":
            blocks.append(Paragraph(inlines=_map_inlines(item.get("inlines", []))))
        elif type == "image":
            blocks.append(Image(alt=item.get("alt", ""), resource_id=item.get("resource_id", "")))
        # Other block types (List, Table) would be handled here.
    return blocks


# --- Public API ---

def parse_with_docling(file_path: str) -> Tuple[InternalDoc, List[ResourceRef]]:
    """
    Parses a document file using the docling engine and converts the output
    into the internal AST representation.

    Args:
        file_path: The absolute path to the document file.

    Returns:
        A tuple containing the InternalDoc AST and a list of extracted resources.
    """
    # 1. Get the raw output from docling
    docling_output = run_docling_parser(file_path)

    # 2. Parse and map resources
    resources = []
    raw_resources = docling_output.get("resources", {})
    for res_id, res_data in raw_resources.items():
        content_b64 = res_data.get("content_b64", "")
        content = base64.b64decode(content_b64)
        sha256 = hashlib.sha256(content).hexdigest()
        resources.append(
            ResourceRef(
                id=res_id,
                mime_type=res_data.get("mime_type", ""),
                content=content,
                sha256=sha256,
            )
        )

    # 3. Parse and map the document structure (AST)
    doc_blocks = _map_blocks(docling_output.get("blocks", []))
    internal_doc = InternalDoc(blocks=doc_blocks)

    return internal_doc, resources
