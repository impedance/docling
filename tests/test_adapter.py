from unittest.mock import patch
import hashlib

from core.adapters.docling_adapter import parse_with_docling
from core.model.internal_doc import Heading, Paragraph, Image, Bold, Text

# This is the simulated JSON output we expect from our mock `run_docling_parser`
MOCK_DOCLING_OUTPUT = {
    "metadata": {
        "title": "Example Document",
    },
    "resources": {
        "img_1": {
            "mime_type": "image/png",
            # A base64 encoded 1x1 black pixel PNG
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

@patch("core.adapters.docling_adapter.run_docling_parser")
def test_parse_with_docling_maps_correctly(mock_run_parser):
    """
    Tests that the adapter correctly maps a mocked docling output to our
    InternalDoc and ResourceRef models.
    """
    # Arrange: Configure the mock to return our predefined JSON structure
    mock_run_parser.return_value = MOCK_DOCLING_OUTPUT
    dummy_filepath = "/path/to/fake.docx"

    # Act: Run the adapter
    doc, resources = parse_with_docling(dummy_filepath)

    # Assert: Check that the mock was called
    mock_run_parser.assert_called_once_with(dummy_filepath)

    # Assert: Check the InternalDoc structure
    assert len(doc.blocks) == 3
    # Check heading
    assert isinstance(doc.blocks[0], Heading)
    assert doc.blocks[0].level == 1
    assert doc.blocks[0].text == "Document Title"
    # Check paragraph
    assert isinstance(doc.blocks[1], Paragraph)
    assert len(doc.blocks[1].inlines) == 3
    assert isinstance(doc.blocks[1].inlines[0], Text)
    assert isinstance(doc.blocks[1].inlines[1], Bold)
    assert doc.blocks[1].inlines[1].content == "sample"
    # Check image
    assert isinstance(doc.blocks[2], Image)
    assert doc.blocks[2].alt == "A single black pixel"
    assert doc.blocks[2].resource_id == "img_1"

    # Assert: Check the ResourceRef objects
    assert len(resources) == 1
    resource = resources[0]
    assert resource.id == "img_1"
    assert resource.mime_type == "image/png"
    
    # Verify content and hash
    assert resource.content is not None
    assert hashlib.sha256(resource.content).hexdigest() == "63ef318d96b5d0d0ceba6e04a4e622b1158335cdc67c49e27839132c6f655058"
