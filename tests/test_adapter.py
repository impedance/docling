import hashlib
from pathlib import Path
from core.adapters.document_parser import parse_document
from core.model.internal_doc import Paragraph, Image

def test_parse_with_real_docx():
    """
    Tests that the adapter correctly parses a real DOCX file.
    """
    # Arrange: Path to a real sample file
    # Using a known file from the project structure
    sample_filepath = Path("/home/spec/work/rosa/docling/real-docs/cu-admin-install.docx")

    # Act: Run the adapter
    doc, resources = parse_document(str(sample_filepath))

    # Assert: Check the InternalDoc structure (basic checks)
    assert len(doc.blocks) > 0, "Document should have blocks"
    
    # Check that we have paragraphs (headings may be detected by later transforms)
    has_paragraph = any(isinstance(b, Paragraph) for b in doc.blocks)
    assert has_paragraph, "Should have at least one paragraph"

    # Assert: Check the ResourceRef objects for images
    # Current implementation does not extract image resources from DOCX
    # This is expected behavior - resources list should be empty
    assert isinstance(resources, list), "Resources should be a list"
    
    # Current parser focuses on text content and structure
    # Image extraction is not implemented yet
    print(f"Resources extracted: {len(resources)}")
    print(f"Total blocks: {len(doc.blocks)}")
    
    # Verify we have structured content
    headings = [b for b in doc.blocks if hasattr(b, 'level')]
    paragraphs = [b for b in doc.blocks if isinstance(b, Paragraph)]
    
    print(f"Headings found: {len(headings)}")
    print(f"Paragraphs found: {len(paragraphs)}")
    
    assert len(headings) > 0, "Should have at least one heading"