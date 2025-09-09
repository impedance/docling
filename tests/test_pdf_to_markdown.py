import base64
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

import pdf_to_md
import preprocess_docling


PNG_DOT = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR4nGJk+M/wHwAE/wM/SEuxAAAAAElFTkSuQmCC"
)


def test_convert_pdf_to_markdown(tmp_path, monkeypatch):
    # Prepare dummy input file
    input_path = tmp_path / "dummy.pdf"
    input_path.write_text("dummy", encoding="utf-8")

    # Fake HTML returned from docling conversion
    html = """
    <html><body>
    <h1>First Chapter</h1>
    <p>Intro text.</p>
    <img src="images/img-0001.png" alt="Dot"/>
    <h1>Second Chapter</h1>
    <p>Second text.</p>
    </body></html>
    """
    img_bytes = base64.b64decode(PNG_DOT)

    def fake_convert(path: str):
        return html, {"img-0001.png": img_bytes}

    monkeypatch.setattr(preprocess_docling, "convert_with_docling_to_html", fake_convert)

    out_dir = tmp_path / "out"
    pdf_to_md.convert_pdf_to_markdown(str(input_path), str(out_dir))

    # images saved
    img_path = out_dir / "images" / "img-0001.png"
    assert img_path.exists()

    # chapters saved
    md1 = (out_dir / "1-first-chapter.md").read_text(encoding="utf-8")
    md2 = (out_dir / "2-second-chapter.md").read_text(encoding="utf-8")

    assert "# First Chapter" in md1
    assert "Intro text." in md1
    assert "![Dot](images/img-0001.png)" in md1

    assert "# Second Chapter" in md2
    assert "Second text." in md2

