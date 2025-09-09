"""Docling-powered preprocessing for DOCX/PDF → HTML and image extraction.

This module provides a thin wrapper around the Docling library to obtain
HTML representation of a document together with extracted images.  The HTML
output is tailored for further processing by the project's splitter and
Markdown renderer.
"""

from __future__ import annotations

import base64
import mimetypes
import os
from pathlib import Path
from typing import Dict, List, Tuple

from bs4 import BeautifulSoup  # type: ignore
import re


def remove_table_of_contents(html_content: str) -> str:
    """Remove common table of contents sections from HTML."""

    soup = BeautifulSoup(html_content, "lxml")

    for p in soup.find_all("p"):
        text = p.get_text()
        if "СОДЕРЖАНИЕ" in text:
            current = p
            while current:
                next_sibling = current.next_sibling
                if current.name == "p":
                    toc_links = current.find_all("a", href=re.compile(r"#__RefHeading"))
                    if toc_links:
                        current.extract()
                    else:
                        break
                current = next_sibling
            break

    for p in soup.find_all("p"):
        links = p.find_all("a", href=re.compile(r"#__RefHeading"))
        if links:
            text_content = p.get_text().strip()
            if re.match(r"^\d+(\.\d+)*\s+.*\s+\d+$", text_content) or len(links) >= 2:
                p.extract()

    return str(soup)


def convert_with_docling_to_html(input_path: str) -> Tuple[str, Dict[str, bytes]]:
    """Convert a document to HTML using Docling and extract embedded images.

    Returns
    -------
    html : str
        HTML string with image ``src`` attributes rewritten to ``images/<name>``.
    resources : Dict[str, bytes]
        Mapping of image file names to binary data.
    """

    try:
        from docling.document_converter import DocumentConverter  # type: ignore
        from docling_core.types.doc.base import ImageRefMode  # type: ignore
    except Exception as exc:  # pragma: no cover - import error handled at runtime
        raise ImportError(
            "Docling is not installed or failed to import. Please `pip install docling`."
        ) from exc

    converter = DocumentConverter()
    result = converter.convert(input_path)
    html = result.document.export_to_html(image_mode=ImageRefMode.EMBEDDED)

    soup = BeautifulSoup(html, "lxml")
    resources: Dict[str, bytes] = {}
    for idx, img in enumerate(soup.find_all("img"), start=1):
        src = img.get("src", "")
        if not src.startswith("data:"):
            continue
        header, b64data = src.split(",", 1)
        mime = header.split(";", 1)[0].split(":", 1)[1]
        ext = mimetypes.guess_extension(mime) or ".png"
        name = f"img-{idx:04d}{ext}"
        resources[name] = base64.b64decode(b64data)
        img["src"] = f"images/{name}"

    return str(soup), resources


def export_images(resources: Dict[str, bytes], images_dir: str) -> List[str]:
    """Save binary resources to ``images_dir`` and return saved file names."""

    os.makedirs(images_dir, exist_ok=True)
    saved: List[str] = []
    for name, data in resources.items():
        path = Path(images_dir) / name
        if not path.exists():
            with open(path, "wb") as fh:
                fh.write(data)
        saved.append(name)
    return saved


def convert_doc_to_html(input_path: str) -> str:
    """High level helper returning cleaned HTML for downstream processing."""

    html, _ = convert_with_docling_to_html(input_path)
    html = remove_table_of_contents(html)
    return html


def extract_images_with_docling(input_path: str, images_dir: str) -> List[str]:
    """Extract images using Docling and save them to ``images_dir``."""

    _, resources = convert_with_docling_to_html(input_path)
    return export_images(resources, images_dir)

