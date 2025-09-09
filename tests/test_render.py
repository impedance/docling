import hashlib
from pathlib import Path

from core.model.internal_doc import InternalDoc, Heading, Paragraph, Text, Bold, Image
from core.model.resource_ref import ResourceRef
from core.render.assets_exporter import export_assets
from core.render.markdown_renderer import render_markdown

def test_export_assets(tmp_path: Path):
    """
    Tests the assets exporter, including deduplication.
    """
    # Arrange
    assets_dir = tmp_path / "assets"
    content1 = b"image data one"
    hash1 = hashlib.sha256(content1).hexdigest()
    content2 = b"image data two"
    hash2 = hashlib.sha256(content2).hexdigest()

    resources = [
        ResourceRef(id="img1", mime_type="image/png", content=content1, sha256=hash1),
        ResourceRef(id="img2", mime_type="image/jpeg", content=content2, sha256=hash2),
        # This is a duplicate of img1 in terms of content
        ResourceRef(id="img3", mime_type="image/png", content=content1, sha256=hash1),
    ]

    # Act
    asset_map = export_assets(resources, str(assets_dir))

    # Assert
    # Check that the correct files were written
    assert (assets_dir / "img1.png").exists()
    assert (assets_dir / "img2.jpg").exists()
    # Check that the duplicate file was NOT written
    assert not (assets_dir / "img3.png").exists()

    # Check that the file content is correct
    assert (assets_dir / "img1.png").read_bytes() == content1

    # Check that the returned asset_map is correct
    assert asset_map == {
        "img1": "assets/img1.png",
        "img2": "assets/img2.jpg",
        "img3": "assets/img1.png",  # img3 should point to the file from img1
    }

def test_render_markdown():
    """
    Tests that the Markdown renderer correctly converts an InternalDoc AST to a string.
    """
    # Arrange
    doc = InternalDoc(blocks=[
        Heading(level=1, text="Document Title"),
        Paragraph(inlines=[
            Text(content="This is a "),
            Bold(content="sample"),
            Text(content=" paragraph."),
        ]),
        Image(resource_id="img_1", alt="An example image"),
    ])
    asset_map = {"img_1": "assets/img_1.png"}

    # Act
    markdown_output = render_markdown(doc, asset_map)

    # Assert
    expected_markdown = (
        "# Document Title\n\n"
        "This is a **sample** paragraph.\n\n"
        "![An example image](assets/img_1.png)"
    )
    assert markdown_output == expected_markdown
