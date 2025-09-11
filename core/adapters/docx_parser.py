
"""
docx_parser.py
Parse DOCX files using WordprocessingML (DOCX XML) to extract structured content.
- Detects headings via w:outlineLvl (preferred) or paragraph style names.
- Extracts all text content with proper heading levels.
- Returns structured data compatible with InternalDoc AST format.

This module replaces the generic docling parsing for DOCX files to ensure
proper chapter extraction and heading numbering preservation.
"""
from __future__ import annotations
import zipfile, re, argparse
from pathlib import Path
from typing import Dict, List, Tuple
from xml.etree import ElementTree as ET

# Internal model imports
from core.model.internal_doc import (
    InternalDoc,
    Block,
    Heading,
    Paragraph,
    Text as InlineText,
    Inline,
)
from core.model.resource_ref import ResourceRef

NS = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}

DEFAULT_HEADING_PATTERNS = [
    r"^Heading\s*(\d)$",           # English
    r"^Заголовок\s*(\d)$",         # Russian exact
    r".*Заголовок\s*(\d)$",        # Russian with prefixes like 'ROSA_Заголовок 1'
    r"^Titre\s*(\d)$",             # French
    r"^Überschrift\s*(\d)$",       # German
    r"^Encabezado\s*(\d)$",        # Spanish
    r".*\bheading\s*(\d)$",        # fallback lowercase '... heading 2'
]

def _read(z: zipfile.ZipFile, name: str) -> bytes | None:
    return z.read(name) if name in z.namelist() else None

def _styles_map(styles_xml: bytes | None) -> Dict[str, str]:
    """Map styleId -> human-readable name from styles.xml."""
    if not styles_xml: return {}
    root = ET.fromstring(styles_xml)
    out: Dict[str, str] = {}
    for s in root.findall(".//w:style", NS):
        sid = s.attrib.get(f"{{{NS['w']}}}styleId")
        name_el = s.find("w:name", NS)
        name = name_el.attrib.get(f"{{{NS['w']}}}val") if name_el is not None else sid
        if sid: out[sid] = name
    return out

def _get_paragraph_number(p: ET.Element, numbering_xml: bytes = None) -> str:
    """Extract paragraph numbering (e.g., '4.1.3') from Word's numbering system."""
    pPr = p.find("w:pPr", NS)
    if pPr is None:
        return ""
    
    numPr = pPr.find("w:numPr", NS)
    if numPr is None:
        return ""
    
    # Extract numId and ilvl
    numId_el = numPr.find("w:numId", NS)
    ilvl_el = numPr.find("w:ilvl", NS)
    
    if numId_el is None or ilvl_el is None:
        return ""
    
    numId = numId_el.attrib.get(f"{{{NS['w']}}}val", "")
    ilvl = ilvl_el.attrib.get(f"{{{NS['w']}}}val", "0")
    
    # For now, we'll use a simplified approach since parsing numbering.xml
    # is complex. We'll look for common numbering patterns in the text itself
    return ""

def _extract_numbering_from_runs(p: ET.Element) -> str:
    """Extract any numbering text from paragraph runs."""
    # Look for text that looks like numbering at the start of the paragraph
    runs = p.findall(".//w:r", NS)
    if not runs:
        return ""
    
    # Get text from the first few runs to check for numbering
    first_run_texts = []
    for run in runs[:3]:  # Check first 3 runs only
        texts = []
        for t in run.findall("w:t", NS):
            if t.text:
                texts.append(t.text)
        run_text = "".join(texts)
        if run_text.strip():
            first_run_texts.append(run_text)
    
    full_start = "".join(first_run_texts)
    
    # Pattern to match numbering at start: "4.1.3 " or "4.1 " or "4 "
    numbering_patterns = [
        r'^(\d+(?:\.\d+)*)\s+',  # "4.1.3 " 
        r'^(\d+(?:\.\d+)*)\.\s+',  # "4.1.3. "
    ]
    
    for pattern in numbering_patterns:
        match = re.match(pattern, full_start)
        if match:
            return match.group(1)
    
    return ""

def _text_of(p: ET.Element) -> str:
    """Extract text from paragraph, including any manual numbering."""
    texts: List[str] = []
    for t in p.findall(".//w:t", NS):
        texts.append(t.text or "")
    full_text = "".join(texts).strip()
    
    return full_text

def _text_with_numbering(p: ET.Element) -> str:
    """Extract text from paragraph, preserving any numbering."""
    # First try to extract automatic numbering
    auto_number = _get_paragraph_number(p)
    if auto_number:
        # Remove the numbering from the text if it's duplicated
        text = _text_of(p)
        number, title = _extract_heading_number_and_title(text)
        if number:  # If text already has numbering, use the text as-is
            return text
        else:  # Add the automatic numbering to clean text
            return f"{auto_number} {text}" if text else auto_number
    
    # Fallback: try to extract numbering from text runs
    run_number = _extract_numbering_from_runs(p)
    text = _text_of(p)
    
    if run_number:
        # Check if the number is already in the text
        if text.startswith(run_number):
            return text
        else:
            return f"{run_number} {text}" if text else run_number
    
    return text

def _extract_heading_number_and_title(text: str) -> tuple[str, str]:
    """Extract chapter number and title from heading text.
    
    Args:
        text: Full heading text (e.g., "4.1.3 Installation and Setup")
        
    Returns:
        tuple of (number, title) where number might be empty if no numbering found
    """
    # Pattern to match various numbering formats
    number_patterns = [
        r'^(\d+(?:\.\d+)*)\s+(.+)$',  # "4.1.3 Title" or "2.1 Title" or "2 Title"
        r'^(\d+(?:\.\d+)*)\.\s+(.+)$',  # "4.1.3. Title" 
        r'^(\d+(?:\.\d+)*)\s*[-–—]\s*(.+)$',  # "4.1.3 - Title" or "4.1.3 – Title"
    ]
    
    for pattern in number_patterns:
        match = re.match(pattern, text.strip())
        if match:
            return match.group(1), match.group(2).strip()
    
    # No numbering found, return empty number and full text as title
    return "", text

def _heading_level(p: ET.Element, styles_map: Dict[str,str], heading_patterns: List[str]) -> int | None:
    """Return heading level (1..9) or None if not a heading."""
    pPr = p.find("w:pPr", NS)
    if pPr is None:
        return None
    # Prefer outlineLvl when present
    outline = pPr.find("w:outlineLvl", NS)
    if outline is not None:
        val = outline.attrib.get(f"{{{NS['w']}}}val")
        if val is not None:
            try:
                return int(val) + 1  # outlineLvl 0 => H1
            except ValueError:
                pass
    # Fallback: paragraph style name
    pStyle = pPr.find("w:pStyle", NS)
    if pStyle is not None:
        sid = pStyle.attrib.get(f"{{{NS['w']}}}val", "")
        sname = styles_map.get(sid, sid) or sid
        for pat in heading_patterns:
            m = re.match(pat, sname, flags=re.IGNORECASE)
            if m:
                try:
                    return int(m.group(1))
                except ValueError:
                    continue
        # Also try styleId like Heading1
        m = re.match(r"^Heading(\d)$", sid, flags=re.IGNORECASE)
        if m:
            return int(m.group(1))
    return None

def _slug(text: str, maxlen: int = 80) -> str:
    s = re.sub(r"[^\w\s-]", "", text, flags=re.UNICODE)
    s = re.sub(r"\s+", "-", s).strip("-_").lower()
    return (s or "section")[:maxlen].rstrip("-_")

def split_docx_by_h1(
    docx_path: str | Path,
    out_dir: str | Path,
    heading_patterns: List[str] | None = None,
) -> Tuple[List[dict], List[Path]]:
    """
    Split DOCX by H1 into Markdown files.
    Returns: (sections, written_paths)
      sections: list of {"title": str, "lines": List[str]}
      written_paths: list of Paths written
    """
    docx_path = Path(docx_path)
    out_root = Path(out_dir) / docx_path.stem
    out_root.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(docx_path) as z:
        doc_xml = _read(z, "word/document.xml")
        styles_xml = _read(z, "word/styles.xml")
    if not doc_xml:
        raise RuntimeError("word/document.xml not found")

    styles_map = _styles_map(styles_xml)
    body = ET.fromstring(doc_xml).find(".//w:body", NS)
    if body is None:
        raise RuntimeError("No <w:body> found")

    patterns = heading_patterns or DEFAULT_HEADING_PATTERNS

    sections: List[dict] = []
    current = {"title": "front-matter", "lines": []}  # content before first H1

    for p in body.findall("w:p", NS):
        lvl = _heading_level(p, styles_map, patterns)
        if lvl:
            # For headings, use numbering-aware text extraction
            t = _text_with_numbering(p)
        else:
            # For regular paragraphs, use simple text extraction
            t = _text_of(p)
            
        if lvl == 1 and t:
            # Start new chapter
            if current["lines"]:
                sections.append(current)
            current = {"title": t, "lines": [f"# {t}\n"]}
        else:
            if t:
                if lvl:
                    current["lines"].append(f"{'#'*lvl} {t}\n")
                else:
                    current["lines"].append(t + "\n")

    if current["lines"]:
        sections.append(current)

    written: List[Path] = []
    for i, sec in enumerate(sections, 1):
        name = f"{i:02d}-{_slug(sec['title'])}.md"
        path = out_root / name
        path.write_text("".join(sec["lines"]), encoding="utf-8")
        written.append(path)

    return sections, written

def parse_docx_to_internal_doc(docx_path: str) -> Tuple[InternalDoc, List[ResourceRef]]:
    """
    Parse DOCX file and return InternalDoc AST format.
    Uses comprehensive XML-based heading numbering extraction.
    
    Args:
        docx_path: Path to the DOCX file
        
    Returns:
        Tuple of (InternalDoc, List[ResourceRef])
    """
    from core.numbering.heading_numbering import extract_headings_with_numbers
    
    docx_path = Path(docx_path)
    
    # Extract numbered headings using comprehensive XML parsing
    numbered_headings = extract_headings_with_numbers(str(docx_path))
    
    with zipfile.ZipFile(docx_path) as z:
        doc_xml = _read(z, "word/document.xml")
        styles_xml = _read(z, "word/styles.xml")
    
    if not doc_xml:
        raise RuntimeError("word/document.xml not found")
    
    styles_map = _styles_map(styles_xml)
    body = ET.fromstring(doc_xml).find(".//w:body", NS)
    if body is None:
        raise RuntimeError("No <w:body> found")
    
    patterns = DEFAULT_HEADING_PATTERNS
    blocks: List[Block] = []
    resources: List[ResourceRef] = []  # DOCX images would need separate extraction
    heading_iter = iter(numbered_headings)
    
    for p in body.findall("w:p", NS):
        lvl = _heading_level(p, styles_map, patterns)
        text = _text_of(p)  # Get basic text first
        
        if text:  # Only process non-empty paragraphs
            if lvl:
                # For headings, try to get numbered text from extracted headings
                try:
                    numbered_heading = next(heading_iter)
                    # Use the numbered text with proper formatting and correct level
                    numbered_text = f"{numbered_heading.number} {numbered_heading.text}"
                    # Cap heading level at 6 to comply with Heading model validation
                    level = min(numbered_heading.level + 1, 6)
                    blocks.append(Heading(level=level, text=numbered_text))
                except StopIteration:
                    # Fallback if we run out of numbered headings
                    # Cap heading level at 6 to comply with Heading model validation
                    level = min(lvl, 6)
                    blocks.append(Heading(level=level, text=text))
            else:
                # Create paragraph with inline text
                inlines = [InlineText(content=text)]
                blocks.append(Paragraph(inlines=inlines))
    
    internal_doc = InternalDoc(blocks=blocks)
    return internal_doc, resources

# Simple CLI
def _cli():
    ap = argparse.ArgumentParser(description="Split DOCX into Markdown chapters by H1")
    ap.add_argument("docx", help="Path to .docx")
    ap.add_argument("-o", "--out", default="out", help="Output directory (default: out)")
    args = ap.parse_args()
    sections, written = split_docx_by_h1(args.docx, args.out)
    print(f"Chapters: {len(sections)}")
    print("Written files:")
    for p in written:
        print(" -", p)

if __name__ == "__main__":
    _cli()
