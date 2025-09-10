import hashlib
from pathlib import Path
from core.adapters.docling_adapter import parse_with_docling
from core.model.internal_doc import Paragraph, Image

def test_parse_with_real_docx():
    """
    Tests that the adapter correctly parses a real DOCX file.
    """
    # Arrange: Path to a real sample file
    # Using a known file from the project structure
    sample_filepath = Path("/home/spec/work/rosa/docling/docx-s/cu-admin-install.docx")

    # Act: Run the adapter
    doc, resources = parse_with_docling(str(sample_filepath))

    # Assert: Check the InternalDoc structure (basic checks)
    assert len(doc.blocks) > 0, "Document should have blocks"
    
    # Check that we have paragraphs (headings may be detected by later transforms)
    has_paragraph = any(isinstance(b, Paragraph) for b in doc.blocks)
    assert has_paragraph, "Should have at least one paragraph"

    # Assert: Check the ResourceRef objects for images
    # This document is expected to have images
    assert len(resources) > 0, "Should extract at least one resource"
    
    # Verify resource properties
    resource = resources[0]
    assert resource.id.startswith("img_")
    assert resource.mime_type in ["image/png", "image/jpeg", "image/gif"]
    assert resource.content is not None
    assert len(resource.sha256) == 64 # SHA256 hex digest length
    assert hashlib.sha256(resource.content).hexdigest() == resource.sha256

    # Check that an image block exists and references a resource
    image_blocks = [b for b in doc.blocks if isinstance(b, Image)]
    assert len(image_blocks) > 0, "Should have at least one image block"
    
    referenced_resource_ids = {res.id for res in resources}
    assert image_blocks[0].resource_id in referenced_resource_ids, "Image block must reference a valid resource"