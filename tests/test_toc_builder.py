from core.output.toc_builder import build_index, build_manifest
from core.model.metadata import Metadata


def test_build_index_and_manifest():
    chapters = [
        {"index": 1, "title": "Intro", "path": "chapters/01-intro.md"},
        {"index": 2, "title": "Usage", "path": "chapters/02-usage.md"},
    ]
    meta = Metadata(title="My Doc")

    index_md = build_index(chapters, meta)
    expected_index = (
        "# My Doc\n\n"
        "- [Intro](chapters/01-intro.md)\n"
        "- [Usage](chapters/02-usage.md)\n"
    )
    assert index_md == expected_index

    asset_map = {"img1": "assets/img1.png"}
    manifest = build_manifest(chapters, asset_map, meta)
    expected_manifest = {
        "metadata": meta.model_dump(),
        "chapters": chapters,
        "assets": asset_map,
    }
    assert manifest == expected_manifest
