from pathlib import Path
from typing import List, Tuple

from core.adapters.docling_adapter import parse_with_docling
from core.model.internal_doc import InternalDoc
from core.model.resource_ref import ResourceRef
# from core.model.config import PipelineConfig # To be created
from core.output.writer import Writer
from core.render.assets_exporter import export_assets
from core.render.markdown_renderer import render_to_markdown
from core.split.chapter_splitter import split_into_chapters
from core.transforms.normalize import normalize
from core.transforms.structure_fixes import fix_structure


class DocumentPipeline:
    def __init__(self, config): # config will be PipelineConfig
        self.config = config
        self.writer = Writer()

    def process(self, input_path: str, output_dir: str):
        """
        Runs the full document processing pipeline.
        """
        # 1. Parse with docling adapter
        doc, resources = parse_with_docling(input_path)

        # 2. Apply transforms
        doc = normalize(doc)
        doc = fix_structure(doc)

        # 3. Split into chapters
        chapters = split_into_chapters(doc, level=1) # placeholder for config.split_level

        # 4. Export assets
        output_path = Path(output_dir)
        assets_dir = output_path / "assets" # placeholder for config.assets_dir
        asset_map = export_assets(resources, assets_dir, self.writer)

        # 5. Render markdown for each chapter
        rendered_chapters = []
        for chapter in chapters:
            markdown_content = render_to_markdown(chapter, asset_map)
            rendered_chapters.append(markdown_content)

        # 6. Generate TOC and manifest
        # toc_content = toc_builder.build_toc(chapters, ...)
        # manifest_content = toc_builder.build_manifest(...)

        # 7. Write all files
        # self.writer.write_text(...)

        # For now, just returning the processed data
        return {
            "chapters": rendered_chapters,
            "asset_map": asset_map,
        }
