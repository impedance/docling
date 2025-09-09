"""High level helper to convert PDF documents to chaptered Markdown."""

from __future__ import annotations

import re
from pathlib import Path

import html2md_rules
import preprocess_docling
import splitter


def _slugify(text: str) -> str:
    """Simplistic slugification to create filesystem-friendly names."""

    import unicodedata

    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
    return text or "chapter"


def convert_pdf_to_markdown(input_path: str, output_dir: str) -> None:
    """Convert ``input_path`` PDF into Markdown files placed in ``output_dir``.

    The function relies solely on deterministic rules without any LLM usage.
    Images are exported to ``output_dir/images`` and chapters are split by
    ``<h1>`` tags.
    """

    out = Path(output_dir)
    images_dir = out / "images"

    html, resources = preprocess_docling.convert_with_docling_to_html(input_path)
    preprocess_docling.export_images(resources, str(images_dir))

    chapters = splitter.split_html_by_h1(html)
    if not chapters:
        chapters = [html]

    out.mkdir(parents=True, exist_ok=True)
    for idx, chapter_html in enumerate(chapters, start=1):
        m = re.search(r"<h1[^>]*>(.*?)</h1>", chapter_html, re.IGNORECASE | re.DOTALL)
        title = m.group(1).strip() if m else f"Chapter {idx}"
        slug = _slugify(title)
        md = html2md_rules.html_to_markdown(chapter_html, idx, title, slug)
        (out / f"{idx}-{slug}.md").write_text(md, encoding="utf-8")

