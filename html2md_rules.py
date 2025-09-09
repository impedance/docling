"""Deterministic HTML → Markdown converter aligned with formatting_rules.md.

This is a pragmatic, partial implementation to get acceptable Markdown without LLM.
It covers headings, paragraphs, lists, code blocks with languages & filenames,
blockquotes, tables (basic), AppAnnotation, and ::sign-image blocks.
"""

from __future__ import annotations

from bs4 import BeautifulSoup, NavigableString, Tag  # type: ignore
import re
from typing import List


def html_to_markdown(html: str, chapter_number: int, title: str, slug: str) -> str:
    soup = BeautifulSoup(html, "lxml")

    # Ensure there is one H1 at top
    blocks: List[str] = []

    # frontmatter minimal (navigation injected later)
    fm = ["---", f"title: {title}", "---", ""]
    blocks.extend(fm)
    blocks.append(f"# {title}")
    blocks.append("")

    # iterate over top-level nodes after the first H1 (if present)
    # fallback: process all body children
    body = soup.body or soup
    # If multiple H1/H2 exist, we just process sequentially.
    for node in body.children:
        if isinstance(node, NavigableString):
            continue
        if not isinstance(node, Tag):
            continue
        if node.name == "h1":
            # Skip additional H1s; treat content as H2 if numeric prefix exists
            text = node.get_text(" ").strip()
            if re.match(r"^\d+\.", text):
                blocks.append(f"## {text}")
                blocks.append("")
            continue
        if node.name == "h2":
            blocks.append(f"## {node.get_text(' ').strip()}")
            blocks.append("")
            continue
        if node.name == "h3":
            blocks.append(f"### {node.get_text(' ').strip()}")
            blocks.append("")
            continue
        if node.name == "h4":
            blocks.append(f"#### {node.get_text(' ').strip()}")
            blocks.append("")
            continue
        if node.name in ("p",):
            txt = node.get_text(" ").strip()
            if not txt:
                continue
            blocks.append(txt)
            blocks.append("")
            continue
        if node.name in ("ul", "ol"):
            for li in node.find_all("li", recursive=False):
                txt = li.get_text(" ").strip()
                if not txt:
                    continue
                if node.name == "ul":
                    blocks.append(f"- {txt}")
                else:
                    blocks.append(f"1. {txt}")
            blocks.append("")
            continue
        if node.name == "pre":
            code = node.find("code")
            if code:
                cls = code.get("class", [])
                lang = None
                filename = None
                for c in cls:
                    if c.startswith("language-"):
                        lang = c.replace("language-", "")
                    if c.startswith("filename-"):
                        filename = c.replace("filename-", "")
                fence = lang or ""
                header = f"{fence}"
                if filename:
                    header += f" {filename.replace('-', '.')}"  # heuristic map e.g. docker-compose
                blocks.append(f"```{header}".rstrip())
                blocks.append(code.get_text())
                blocks.append("```")
                blocks.append("")
                continue
        if node.name == "blockquote":
            text = node.get_text("\n").strip()
            for line in text.splitlines():
                blocks.append(f"> {line}")
            blocks.append("")
            continue
        if node.name == "img":
            src = node.get("src", "").strip()
            alt = node.get("alt", "").strip()
            if src:
                blocks.append(f"![{alt}]({src})")
                blocks.append("")
            continue
        if node.name == "table":
            # very basic table conversion
            rows = node.find_all("tr")
            if not rows:
                continue
            # header if first row has th
            header_cells = rows[0].find_all(["th","td"])
            header = "| " + " | ".join(_cell_text(c) for c in header_cells) + " |"
            sep = "| " + " | ".join("---" for _ in header_cells) + " |"
            blocks.append(header)
            blocks.append(sep)
            for r in rows[1:]:
                cells = r.find_all(["td","th"])
                line = "| " + " | ".join(_cell_text(c) for c in cells) + " |"
                blocks.append(line)
            blocks.append("")
            continue
        if node.name == "div":
            cls = node.get("class", [])
            if "app-annotation" in cls:
                blocks.append("::AppAnnotation")
                text = node.get_text("\n").strip()
                blocks.append(text)
                blocks.append("::")
                blocks.append("")
                continue
            if "image-block" in cls or "figure-block" in cls or "image-caption" in cls:
                # Try to synthesize ::sign-image from <img> and caption text
                img = node.find("img")
                caption = node.get_text(" ").strip()
                if img and img.get("src"):
                    blocks.append("::sign-image")
                    blocks.append(f"src: {img.get('src')}")
                    # If caption already starts with 'Рисунок N –', keep; else make generic
                    if re.match(r"^Рисунок\s+\d+\s+–\s+.+", caption):
                        blocks.append(f"sign: {caption}")
                    else:
                        blocks.append(f"sign: Рисунок 1 – {caption}")
                    blocks.append("::")
                    blocks.append("")
                    continue
    return "\n".join(blocks).rstrip() + "\n"


def _cell_text(cell: Tag) -> str:
    # Preserve <br> as line breaks
    text = ""
    for item in cell.contents:
        if isinstance(item, NavigableString):
            text += str(item)
        elif isinstance(item, Tag) and item.name == "br":
            text += "<br>"
        else:
            text += item.get_text()
    return " ".join(text.split())
