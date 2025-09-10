"""
Chapter Extractor for DOCX XML

Extracts hierarchical chapter structure from DOCX files with numbering preservation.
Creates structured JSON representation of document outline.
"""
from __future__ import annotations
import zipfile
import re
from typing import Dict, List, Tuple, Optional
from xml.etree import ElementTree as ET
from pathlib import Path
from dataclasses import dataclass

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


@dataclass
class ChapterNode:
    """Represents a chapter/section node with hierarchical structure."""
    level: int
    title: str
    number: str = ""
    full_text: str = ""
    children: List['ChapterNode'] = None
    
    def __post_init__(self):
        if self.children is None:
            self.children = []
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "level": self.level,
            "title": self.title,
            "number": self.number,
            "full_text": self.full_text,
            "children": [child.to_dict() for child in self.children]
        }


def _read_docx_part(z: zipfile.ZipFile, name: str) -> bytes | None:
    """Read a part from DOCX archive."""
    return z.read(name) if name in z.namelist() else None


def _build_styles_map(styles_xml: bytes | None) -> Dict[str, str]:
    """Map styleId -> human-readable name from styles.xml."""
    if not styles_xml:
        return {}
    
    root = ET.fromstring(styles_xml)
    styles_map: Dict[str, str] = {}
    
    for style in root.findall(".//w:style", NS):
        style_id = style.attrib.get(f"{{{NS['w']}}}styleId")
        name_el = style.find("w:name", NS)
        name = name_el.attrib.get(f"{{{NS['w']}}}val") if name_el is not None else style_id
        if style_id:
            styles_map[style_id] = name
    
    return styles_map


def _extract_paragraph_text(paragraph: ET.Element) -> str:
    """Extract text from paragraph element."""
    texts: List[str] = []
    for text_el in paragraph.findall(".//w:t", NS):
        texts.append(text_el.text or "")
    return "".join(texts).strip()


def _extract_heading_number_and_title(text: str) -> Tuple[str, str]:
    """Extract chapter number and title from heading text.
    
    Args:
        text: Full heading text (e.g., "4.1.3 Installation and Setup")
        
    Returns:
        Tuple of (number, title) where number might be empty if no numbering found
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


def _detect_heading_level(paragraph: ET.Element, styles_map: Dict[str, str], 
                         heading_patterns: List[str]) -> Optional[int]:
    """Detect heading level from paragraph properties."""
    pPr = paragraph.find("w:pPr", NS)
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
        style_id = pStyle.attrib.get(f"{{{NS['w']}}}val", "")
        style_name = styles_map.get(style_id, style_id) or style_id
        
        for pattern in heading_patterns:
            match = re.match(pattern, style_name, flags=re.IGNORECASE)
            if match:
                try:
                    return int(match.group(1))
                except ValueError:
                    continue
        
        # Also try styleId like Heading1
        match = re.match(r"^Heading(\d)$", style_id, flags=re.IGNORECASE)
        if match:
            return int(match.group(1))
    
    return None


def extract_chapter_structure(docx_path: str | Path) -> List[ChapterNode]:
    """
    Extract hierarchical chapter structure from DOCX file.
    
    Args:
        docx_path: Path to the DOCX file
        
    Returns:
        List of top-level ChapterNode objects with nested structure
    """
    docx_path = Path(docx_path)
    
    with zipfile.ZipFile(docx_path) as z:
        doc_xml = _read_docx_part(z, "word/document.xml")
        styles_xml = _read_docx_part(z, "word/styles.xml")
    
    if not doc_xml:
        raise RuntimeError("word/document.xml not found")
    
    styles_map = _build_styles_map(styles_xml)
    body = ET.fromstring(doc_xml).find(".//w:body", NS)
    if body is None:
        raise RuntimeError("No <w:body> found")
    
    patterns = DEFAULT_HEADING_PATTERNS
    headings: List[ChapterNode] = []
    
    # Extract all headings first
    for paragraph in body.findall("w:p", NS):
        level = _detect_heading_level(paragraph, styles_map, patterns)
        if level:
            text = _extract_paragraph_text(paragraph)
            if text:  # Only process non-empty headings
                number, title = _extract_heading_number_and_title(text)
                node = ChapterNode(
                    level=level,
                    title=title or text,
                    number=number,
                    full_text=text
                )
                headings.append(node)
    
    # Build hierarchical structure
    return _build_hierarchy(headings)


def _build_hierarchy(headings: List[ChapterNode]) -> List[ChapterNode]:
    """Build hierarchical structure from flat list of headings."""
    if not headings:
        return []
    
    root_nodes: List[ChapterNode] = []
    stack: List[ChapterNode] = []
    
    for heading in headings:
        # Pop stack until we find a valid parent (lower level number)
        while stack and stack[-1].level >= heading.level:
            stack.pop()
        
        if stack:
            # Add as child to the last item in stack
            stack[-1].children.append(heading)
        else:
            # Add as root node
            root_nodes.append(heading)
        
        # Push current heading to stack
        stack.append(heading)
    
    return root_nodes


def export_chapter_map_json(chapter_nodes: List[ChapterNode]) -> Dict:
    """
    Export chapter structure as JSON-serializable dictionary.
    
    Args:
        chapter_nodes: List of top-level chapter nodes
        
    Returns:
        Dictionary suitable for JSON serialization
    """
    return {
        "document_structure": {
            "chapters": [node.to_dict() for node in chapter_nodes],
            "total_chapters": len(chapter_nodes),
            "max_depth": _calculate_max_depth(chapter_nodes)
        }
    }


def _calculate_max_depth(nodes: List[ChapterNode], current_depth: int = 1) -> int:
    """Calculate maximum depth of the hierarchy."""
    if not nodes:
        return current_depth - 1
    
    max_depth = current_depth
    for node in nodes:
        if node.children:
            depth = _calculate_max_depth(node.children, current_depth + 1)
            max_depth = max(max_depth, depth)
    
    return max_depth


def extract_and_export_chapter_map(docx_path: str | Path) -> Dict:
    """
    Extract chapter structure and export as JSON-ready dictionary.
    
    Args:
        docx_path: Path to the DOCX file
        
    Returns:
        JSON-serializable dictionary with hierarchical chapter structure
    """
    chapter_nodes = extract_chapter_structure(docx_path)
    return export_chapter_map_json(chapter_nodes)