"""Utilities for preprocessing DOCX files."""

from __future__ import annotations

import os
import re
import subprocess

import mammoth
from bs4 import BeautifulSoup

from .heading_numbering import add_numbering_to_html


def convert_docx_to_html(docx_path: str, style_map_path: str) -> str:
    """Convert DOCX to HTML using a Mammoth style map and add heading numbering."""
    with open(docx_path, "rb") as docx_file, open(
        style_map_path, "r", encoding="utf-8"
    ) as style_map_file:
        style_map = style_map_file.read()
        result = mammoth.convert_to_html(docx_file, style_map=style_map)
    
    # Add heading numbering based on TOC information
    html_with_numbering = add_numbering_to_html(result.value, docx_path)
    return html_with_numbering


def extract_images(docx_path: str, output_dir: str) -> None:
    """Extract images from DOCX using Pandoc."""
    os.makedirs(output_dir, exist_ok=True)
    command = [
        "pandoc",
        docx_path,
        "--extract-media",
        output_dir,
        "-t",
        "markdown",
        "-o",
        os.devnull,
    ]
    subprocess.run(command, check=True)


def remove_table_of_contents(html_content: str) -> str:
    """
    Remove table of contents section from HTML content.
    
    Identifies and completely removes the TOC section that typically starts with 
    "СОДЕРЖАНИЕ" and contains multiple links to document sections. Both the 
    "СОДЕРЖАНИЕ" heading and all TOC links are removed.
    """
    soup = BeautifulSoup(html_content, "lxml")
    
    # Strategy 1: Find text "СОДЕРЖАНИЕ" and remove all subsequent links until first __RefHeading anchor
    for p in soup.find_all("p"):
        text = p.get_text()
        if "СОДЕРЖАНИЕ" in text:
            # Found TOC start, now remove all subsequent TOC links
            current = p
            while current:
                next_sibling = current.next_sibling
                
                # If this paragraph contains TOC links, remove them
                if current.name == "p":
                    # Remove all href links that point to __RefHeading in this paragraph
                    toc_links = current.find_all("a", href=re.compile(r"#__RefHeading"))
                    if toc_links:
                        # Remove the entire paragraph including "СОДЕРЖАНИЕ"
                        current.extract()
                    else:
                        # No more TOC links, stop removing
                        break
                
                current = next_sibling
            break
    
    # Strategy 2: Remove any remaining standalone TOC link paragraphs
    for p in soup.find_all("p"):
        # If paragraph contains only TOC links and tabs/numbers, remove it
        links = p.find_all("a", href=re.compile(r"#__RefHeading"))
        if links:
            # Check if paragraph is mostly TOC content (contains mainly links and numbers)
            text_content = p.get_text().strip()
            # Remove paragraph if it's primarily TOC links (contains numbers and section titles)
            if re.match(r'^\d+(\.\d+)*\s+.*\s+\d+$', text_content) or len(links) >= 2:
                p.extract()
    
    return str(soup)
