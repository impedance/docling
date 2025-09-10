from typing import List, Dict
from core.model.metadata import Metadata


def build_index(chapters: List[Dict], meta: Metadata) -> str:
    """Builds an index.md file content linking to all chapters."""
    title = meta.title or "Table of Contents"
    lines = [f"# {title}", ""]
    for ch in chapters:
        lines.append(f"- [{ch['title']}]({ch['path']})")
    return "\n".join(lines) + "\n"


def build_manifest(chapters: List[Dict], asset_map: Dict[str, str], meta: Metadata) -> Dict:
    """Builds a manifest structure for serialization to JSON."""
    return {
        "metadata": meta.model_dump(),
        "chapters": chapters,
        "assets": asset_map,
    }
