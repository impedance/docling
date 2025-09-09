"""Docling-powered preprocessing for DOCX/PDF → HTML (+images).

This module is a *drop-in* alternative to `preprocess.py` for the existing pipeline.
It keeps the downstream contracts the same:
- returns HTML string for splitting by <h1>
- saves images to an output/images directory (relative paths preserved)

Why HTML and not Markdown?
- Your validators, splitter, and LLM prompts are already tuned for HTML→Markdown with rules.
- Keeping HTML preserves rich structure for your rules (tables, code blocks, special divs).

Requirements:
    pip install docling  # or the specific package name/version you use

Notes:
- The exact Docling API may vary by version; the adapter isolates imports so the rest of the app is unaffected.
- If Docling is not available at runtime, we raise a clear ImportError.
"""

from __future__ import annotations

import os
import hashlib
from pathlib import Path
from typing import Tuple, Dict, List, Optional

# Local helpers from your project
from .heading_numbering import add_numbering_to_html
from .preprocess import remove_table_of_contents  # reuse your existing TOC cleaner


def _sha1(data: bytes) -> str:
    import hashlib
    return hashlib.sha1(data).hexdigest()


def convert_with_docling_to_html(input_path: str) -> Tuple[str, Dict[str, bytes]]:
    """Parse DOCX/PDF with Docling and return (html, resources).

    Returns:
        html: HTML string with structure and semantic blocks.
        resources: mapping resource_id -> binary content (images etc.).
    """
    try:
        # Lazy import to keep adapter boundary thin
        import docling  # type: ignore
    except Exception as e:
        raise ImportError("Docling is not installed or failed to import. Please `pip install docling`.\n" + str(e))

    # --- PSEUDO-API below: replace with your concrete docling calls ---
    # The idea:
    #   doc = docling.Document.from_file(input_path)
    #   html = doc.to_html()    # or doc.render(format="html")
    #   resources = {res.id: res.bytes for res in doc.resources(images=True)}
    #
    # To keep the scaffold runnable, we simulate minimal output and defer real wiring to you.
    suffix = Path(input_path).suffix.lower()
    fake_title = Path(input_path).stem
    html = f"""<h1>{fake_title}</h1>
<p>Этот HTML сгенерирован адаптером docling (заглушка). Подключите реальный вызов Docling.</p>
<h1>Глава 1. Введение</h1>
<p>Текст главы 1…</p>
<h1>Глава 2. Детали</h1>
<p>Текст главы 2…</p>
"""
    resources: Dict[str, bytes] = {}
    return html, resources


def export_images(resources: Dict[str, bytes], images_dir: str) -> List[str]:
    """Save binary resources (images) to images_dir.
    Returns list of saved relative filenames.
    """
    os.makedirs(images_dir, exist_ok=True)
    saved: List[str] = []
    for rid, data in resources.items():
        h = _sha1(data)[:16]
        # Very rough content sniffing; replace with actual media-type from docling if available.
        ext = ".png"
        name = f"img-{h}{ext}"
        path = os.path.join(images_dir, name)
        if not os.path.exists(path):
            with open(path, "wb") as f:
                f.write(data)
        saved.append(name)
    return saved


def convert_doc_to_html(input_path: str, style_map_path: Optional[str] = None) -> str:
    """High-level function mirroring preprocess.convert_docx_to_html(...), but via Docling.

    - Parses input with Docling (DOCX or PDF)
    - Injects heading numbering via your TOC-based helper (only for DOCX; harmless for PDFs if no TOC)
    - Removes TOC (re-using your existing logic)
    """
    html, _ = convert_with_docling_to_html(input_path)
    # Preserve your numbering logic based on DOCX TOC if available
    try:
        html = add_numbering_to_html(html, input_path)
    except Exception:
        # Non-fatal if no TOC or non-DOCX
        pass
    # Strip TOC (your cleaner handles heuristics)
    html = remove_table_of_contents(html)
    return html


def extract_images_with_docling(input_path: str, images_dir: str) -> List[str]:
    """Extract images via Docling and save to images_dir.
    Returns list of saved filenames.
    """
    _, resources = convert_with_docling_to_html(input_path)
    return export_images(resources, images_dir)
