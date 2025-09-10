# md_numbering.py
import re
from typing import Iterable
from core.numbering.heading_numbering import NumberedHeading

HEADING_RE = re.compile(r'^(#{1,6})\s+(.*\S)\s*$')

def apply_numbers_to_markdown(md_text: str, numbered: Iterable[NumberedHeading]) -> str:
    """
    Walk through MD lines; for each heading line, prefix with the next heading.number.
    If line already begins with a number like '1.2 ' — replace it (avoid double numbering).
    """
    it = iter(numbered)
    out_lines = []
    for line in md_text.splitlines():
        m = HEADING_RE.match(line)
        if not m:
            out_lines.append(line)
            continue
        hashes, title = m.group(1), m.group(2)

        # Strip any existing leading number (e.g., '1.2.3 ' / 'IV ' / 'A.1 ')
        # Use word boundary to ensure we match complete number tokens
        title_clean = re.sub(r'^(?:\d+(?:[.\-]\d+)*|[IVXLCDM]+)\s+', '', title, flags=re.IGNORECASE)

        try:
            h = next(it)
        except StopIteration:
            # No more headings from DOCX — keep as-is
            out_lines.append(f"{hashes} {title_clean}")
            continue

        out_lines.append(f"{hashes} {h.number} {title_clean}")
    return "\n".join(out_lines) + "\n"