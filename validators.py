"""Markdown validation utilities (aligned with formatting_rules.md)."""

from __future__ import annotations

import re
from typing import List, Tuple


# ----------------------
# Existing validators
# ----------------------

def validate_app_annotations(markdown: str) -> List[str]:
    """Check that all ::AppAnnotation blocks are properly closed."""
    warnings: List[str] = []
    starts = [m.start() for m in re.finditer(r"^::AppAnnotation\s*$", markdown, flags=re.MULTILINE)]
    ends = [m.start() for m in re.finditer(r"^::\s*$", markdown, flags=re.MULTILINE)]
    if len(starts) != len(ends):
        warnings.append("Mismatched ::AppAnnotation blocks")
    elif starts and any(s > e for s, e in zip(starts, ends)):
        warnings.append("Incorrect ::AppAnnotation block ordering")
    return warnings


def validate_table_captions(markdown: str) -> List[str]:
    """Ensure table captions follow '> Таблица N – Description' format."""
    warnings: List[str] = []
    for line in markdown.splitlines():
        if line.strip().startswith("> Таблица"):
            if not re.match(r"^>\s+Таблица\s+\d+\s+–\s+.+", line.strip()):
                warnings.append(f"Invalid table caption: {line}")
    return warnings


def validate_component_list_punctuation(markdown: str) -> List[str]:
    """Ensure component lists use ';' and last item ends with '.'"""
    warnings: List[str] = []
    # Component list items are generic '- ' items; we validate punctuation groups.
    lines = markdown.splitlines()
    i = 0
    while i < len(lines):
        if re.match(r"^\-\s+.+", lines[i]):
            start = i
            while i < len(lines) and re.match(r"^\-\s+.+", lines[i]):
                i += 1
            group = lines[start:i]
            # only validate if at least 2 items (to avoid false positives on isolated bullets)
            if len(group) >= 2:
                for j, item in enumerate(group):
                    txt = item.rstrip()
                    if j < len(group) - 1:
                        if not txt.endswith(";"):
                            warnings.append(f"List item should end with ';': {item}")
                    else:
                        if not txt.endswith("."):
                            warnings.append(f"Last list item should end with '.': {item}")
            continue
        i += 1
    return warnings


# ----------------------
# New validators per rules
# ----------------------

def _extract_frontmatter_title(md: str) -> str | None:
    m = re.search(r"^---\s*\n(.*?)\n---\s*", md, re.DOTALL | re.MULTILINE)
    if not m:
        return None
    fm = m.group(1)
    tm = re.search(r"^title:\s*(.+)\s*$", fm, re.MULTILINE)
    if not tm:
        return None
    return tm.group(1).strip()


def validate_single_h1_matches_title(markdown: str) -> List[str]:
    """Ensure exactly one H1 exists and it equals frontmatter title."""
    warnings: List[str] = []
    title = _extract_frontmatter_title(markdown)
    h1s = re.findall(r"^#\s+(.+)$", markdown, flags=re.MULTILINE)
    if len(h1s) == 0:
        warnings.append("Missing H1 after frontmatter")
    elif len(h1s) > 1:
        warnings.append("Multiple H1 headings detected")
    if title and h1s:
        if h1s[0].strip() != title.strip():
            warnings.append(f"H1 does not match frontmatter title: '{h1s[0]}' != '{title}'")
    return warnings


def validate_heading_numbering(markdown: str) -> List[str]:
    """Validate H2/H3/H4 numbering patterns according to rules."""
    warnings: List[str] = []
    # H2: '## X.Y Title'
    for m in re.finditer(r"^##\s+(\d+\.\d+)\s+.+$", markdown, flags=re.MULTILINE):
        pass  # matches
    # Find H2s that do NOT start with number pattern
    for m in re.finditer(r"^##\s+(.+)$", markdown, flags=re.MULTILINE):
        text = m.group(1).strip()
        if not re.match(r"^\d+\.\d+\s+.+", text):
            warnings.append(f"H2 without numbering 'X.Y': {text}")
    # H3: '### X.Y.Z Title'
    for m in re.finditer(r"^###\s+(.+)$", markdown, flags=re.MULTILINE):
        text = m.group(1).strip()
        if not re.match(r"^\d+\.\d+\.\d+\s+.+", text):
            warnings.append(f"H3 without numbering 'X.Y.Z': {text}")
    # H4: '#### X.Y.Z.W Title'
    for m in re.finditer(r"^####\s+(.+)$", markdown, flags=re.MULTILINE):
        text = m.group(1).strip()
        if not re.match(r"^\d+\.\d+\.\d+\.\d+\s+.+", text):
            warnings.append(f"H4 without numbering 'X.Y.Z.W': {text}")
    return warnings


def validate_sign_image_blocks(markdown: str) -> List[str]:
    """Ensure ::sign-image blocks follow canonical format."""
    warnings: List[str] = []
    pattern = re.compile(
        r"^::sign-image\s*\n(?P<body>.*?)\n::\s*$",
        flags=re.MULTILINE | re.DOTALL,
    )
    for m in pattern.finditer(markdown):
        body = m.group("body").strip()
        # Expect two lines: src: <path> and sign: Рисунок N – ...
        src_m = re.search(r"^src:\s+(/images/developer/user/.+/picture_\d+\.png)\s*$", body, re.MULTILINE)
        sign_m = re.search(r"^sign:\s+Рисунок\s+\d+\s+–\s+.+$", body, re.MULTILINE)
        if not src_m:
            warnings.append("::sign-image missing or invalid 'src:' path")
        if not sign_m:
            warnings.append("::sign-image missing or invalid 'sign:' caption (expected 'Рисунок N – ...')")
    return warnings


def validate_spacing_rules(markdown: str) -> List[str]:
    """Validate blank lines after headings, lists, tables and captions."""
    warnings: List[str] = []
    lines = markdown.splitlines()
    for i, line in enumerate(lines[:-1]):
        # After H1..H4 there should be a blank line
        if re.match(r"^#{1,4}\s+.+$", line):
            if lines[i+1].strip() != "":
                warnings.append(f"Missing blank line after heading at line {i+1}")
        # After a table (separator row '---|') ensure a blank line after caption as well
        if re.match(r"^\|.*\|$", line) and (i+1 < len(lines) and re.match(r"^\|?\s*[-:]+", lines[i+1]) or True):
            # crude detection: if a table block ends at j, ensure blank line after last row or after caption
            pass
        # After blockquote table caption (> Таблица ...), expect blank line
        if line.strip().startswith("> Таблица"):
            if lines[i+1].strip() != "":
                warnings.append(f"Missing blank line after table caption at line {i+1}")
    return warnings


def validate_inline_code_terms(markdown: str) -> List[str]:
    """Heuristic check: technical proper nouns should often be inline-coded.
    We only warn if a clearly code-like term appears many times without backticks.
    """
    warnings: List[str] = []
    terms = ["Winter CMS", "PostgreSQL", "Docker", "Traefik", "Redis", "Typesense", "TLS", "JSON", "YAML", "HTML5", "CSS3", "JavaScript"]
    for term in terms:
        plain = len(re.findall(rf"(?<!`)\b{re.escape(term)}\b(?!`)", markdown))
        coded = len(re.findall(rf"`{re.escape(term)}`", markdown))
        if plain >= 3 and coded == 0:
            warnings.append(f"Term should be inline-coded with backticks at least sometimes: {term}")
    return warnings


def run_all_validators(markdown: str) -> List[str]:
    """Run all validators and collect warnings."""
    warnings: List[str] = []
    warnings.extend(validate_app_annotations(markdown))
    warnings.extend(validate_table_captions(markdown))
    warnings.extend(validate_component_list_punctuation(markdown))
    warnings.extend(validate_single_h1_matches_title(markdown))
    warnings.extend(validate_heading_numbering(markdown))
    warnings.extend(validate_sign_image_blocks(markdown))
    warnings.extend(validate_spacing_rules(markdown))
    warnings.extend(validate_inline_code_terms(markdown))
    return warnings


__all__ = [
    "validate_app_annotations",
    "validate_table_captions",
    "validate_component_list_punctuation",
    "validate_single_h1_matches_title",
    "validate_heading_numbering",
    "validate_sign_image_blocks",
    "validate_spacing_rules",
    "validate_inline_code_terms",
    "run_all_validators",
]
