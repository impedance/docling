import pytest
from pydantic import ValidationError

from core.model.internal_doc import (
    Heading,
    Paragraph,
    Text,
    Bold,
    InternalDoc,
    Image
)
from core.model.metadata import Metadata, TocEntry
from core.model.resource_ref import ResourceRef


def test_heading_validation():
    """Tests that Heading model validates levels correctly."""
    # Valid levels
    assert Heading(level=1, text="Title").level == 1
    assert Heading(level=6, text="Subtitle").level == 6

    # Invalid levels
    with pytest.raises(ValidationError):
        Heading(level=0, text="Invalid")
    with pytest.raises(ValidationError):
        Heading(level=7, text="Invalid")


def test_paragraph_creation():
    """Tests creation of a Paragraph with mixed inline content."""
    p = Paragraph(inlines=[
        Text(content="Hello, "),
        Bold(content="world"),
        Text(content="!"),
    ])
    assert len(p.inlines) == 3
    assert p.inlines[1].type == "bold"
    assert p.inlines[1].content == "world"


def test_internal_doc_creation():
    """Tests the creation of a simple InternalDoc."""
    doc = InternalDoc(blocks=[
        Heading(level=1, text="Document Title"),
        Paragraph(inlines=[Text(content="This is the first paragraph.")]),
        Image(resource_id="img1", alt="An example image"),
    ])
    assert len(doc.blocks) == 3
    assert isinstance(doc.blocks[0], Heading)
    assert isinstance(doc.blocks[2], Image)
    assert doc.blocks[0].text == "Document Title"


def test_metadata_creation():
    """Tests the creation of a Metadata object."""
    meta = Metadata(
        title="My Awesome Document",
        authors=["John Doe"],
        toc=[
            TocEntry(level=1, title="Introduction", anchor="intro")
        ]
    )
    assert meta.title == "My Awesome Document"
    assert meta.authors == ["John Doe"]
    assert len(meta.toc) == 1
    assert meta.toc[0].title == "Introduction"


def test_resource_ref_creation():
    """Tests the creation of a ResourceRef object."""
    content = b"some image data"
    resource = ResourceRef(
        id="image1",
        mime_type="image/png",
        content=content,
        sha256="somehash" # In a real scenario, this would be a calculated hash
    )
    assert resource.id == "image1"
    assert resource.mime_type == "image/png"
    assert resource.content == content

