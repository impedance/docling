from typing import List, Tuple

from core.model.internal_doc import InternalDoc
from core.model.resource_ref import ResourceRef
from .docx_parser import parse_docx_to_internal_doc

def _detect_file_type(file_path: str) -> str:
    """Detect file type based on extension."""
    file_path_lower = file_path.lower()
    if file_path_lower.endswith('.docx'):
        return 'docx'
    else:
        return 'unknown'


def parse_document(file_path: str) -> Tuple[InternalDoc, List[ResourceRef]]:
    """
    Parses a document file using appropriate parser based on file type.
    Routes DOCX files to specialized XML parser for better chapter extraction.
    Currently only supports DOCX files.
    """
    file_type = _detect_file_type(file_path)
    
    if file_type == 'docx':
        # Use specialized DOCX parser for better chapter extraction
        return parse_docx_to_internal_doc(file_path)
    
    # Only DOCX files are supported
    raise ValueError(f"Unsupported file type: {file_type}. Only DOCX files are supported.")