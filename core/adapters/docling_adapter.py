from typing import List, Tuple, Any, Dict
import hashlib
import base64

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

# --- Mocked Docling Interaction ---
# In a real implementation, this function would call the actual docling process
# and get its JSON output. For now, it's a placeholder.

def run_docling_parser(file_path: str) -> Dict[str, Any]:
    """
    A mock function that simulates running the docling parser on a file
    and returns a structured JSON-like dictionary.
    """
    # This is a hardcoded response for testing purposes.
    # It represents a simple document structure.
    return {
        "metadata": {
            "title": "Example Document",
        },
        "resources": {
            "img_1": {
                "mime_type": "image/png",
                "content_b64": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=",
            }
        },
        "blocks": [
            {"type": "heading", "level": 1, "text": "Document Title"},
            {
                "type": "paragraph",
                "inlines": [
                    {"type": "text", "content": "This is a "},
                    {"type": "bold", "content": "sample"},
                    {"type": "text", "content": " paragraph."},
                ],
            },
            {"type": "image", "alt": "A single black pixel", "resource_id": "img_1"},
        ],
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
