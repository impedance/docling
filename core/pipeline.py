import json
from pathlib import Path
from typing import List, NamedTuple

from core.adapters.document_parser import parse_document
from core.model.metadata import Metadata
from core.model.config import PipelineConfig
from core.output.writer import Writer
from core.output.file_naming import generate_chapter_filename
from core.output.toc_builder import build_index, build_manifest
from core.render.assets_exporter import export_assets
from core.render.markdown_renderer import render_markdown
from core.split.chapter_splitter import split_into_chapters, ChapterRules
from core.transforms.normalize import run as normalize
from core.transforms.structure_fixes import run as fix_structure
from core.transforms.content_reorder import run as reorder_content


class PipelineResult(NamedTuple):
    """Result structure returned by DocumentPipeline.process()"""
    success: bool
    chapter_files: List[str]
    index_file: str
    manifest_file: str
    asset_files: List[str]
    error_message: str = ""


class DocumentPipeline:
    def __init__(self, config: PipelineConfig):
        self.config = config
        self.writer = Writer()

    def process(self, input_path: str, output_dir: str) -> PipelineResult:
        """
        Runs the full document processing pipeline.
        
        Args:
            input_path: Path to the input document (DOCX)
            output_dir: Directory to write output files
            
        Returns:
            PipelineResult with success status and file paths
        """
        try:
            # Setup output directories
            output_path = Path(output_dir)
            input_basename = Path(input_path).stem
            doc_output_dir = output_path / input_basename
            chapters_dir = doc_output_dir / "chapters"
            assets_dir = doc_output_dir / self.config.assets_dir
            
            # Ensure directories exist
            self.writer.ensure_dir(doc_output_dir)
            self.writer.ensure_dir(chapters_dir)
            
            # 1. Parse with docling adapter
            doc, resources = parse_document(input_path)

            # 2. Apply transforms
            doc = normalize(doc)
            doc = fix_structure(doc)
            doc = reorder_content(doc)

            # 3. Split into chapters
            rules = ChapterRules(level=self.config.split_level)
            chapters = split_into_chapters(doc, rules)

            # 4. Export assets
            asset_map = export_assets(resources, str(assets_dir))

            # 5. Render markdown for each chapter and write files
            chapter_files = []
            chapter_info = []
            
            for i, chapter in enumerate(chapters):
                # Generate chapter title
                if i == 0:
                    # For chapter 0, combine special sections into a meaningful title
                    chapter_title = _get_zero_chapter_title(chapter)
                else:
                    # For main chapters, find first heading and renumber it
                    chapter_title = _get_main_chapter_title(chapter, i)
                
                # Fallback
                if not chapter_title:
                    chapter_title = f"Chapter {i}"
                
                # Generate filename - start numbering from 0 for title page/TOC
                filename = generate_chapter_filename(i, chapter_title, self.config.chapter_pattern)
                chapter_path = chapters_dir / filename
                
                # Render markdown
                markdown_content = render_markdown(chapter, asset_map)
                
                # Write chapter file
                self.writer.write_text(chapter_path, markdown_content)
                chapter_files.append(str(chapter_path))
                
                # Store chapter info for TOC
                chapter_info.append({
                    "title": chapter_title,
                    "path": f"chapters/{filename}"
                })

            # 6. Generate metadata
            metadata = Metadata(
                title=input_basename.replace('-', ' ').replace('_', ' ').title(),
                language=self.config.locale
            )

            # 7. Generate and write index.md (TOC)
            index_content = build_index(chapter_info, metadata)
            index_path = doc_output_dir / "index.md"
            self.writer.write_text(index_path, index_content)

            # 8. Generate and write manifest.json
            manifest_data = build_manifest(chapter_info, asset_map, metadata)
            manifest_path = doc_output_dir / "manifest.json"
            manifest_json = json.dumps(manifest_data, indent=2, ensure_ascii=False)
            self.writer.write_text(manifest_path, manifest_json)

            # Get list of asset files - asset_map values are relative paths that include the directory name
            asset_files = []
            for relative_path in asset_map.values():
                # Extract just the filename from the relative path (remove the directory part)
                filename = Path(relative_path).name
                asset_files.append(str(assets_dir / filename))

            return PipelineResult(
                success=True,
                chapter_files=chapter_files,
                index_file=str(index_path),
                manifest_file=str(manifest_path),
                asset_files=asset_files
            )

        except Exception as e:
            return PipelineResult(
                success=False,
                chapter_files=[],
                index_file="",
                manifest_file="",
                asset_files=[],
                error_message=str(e)
            )


def _get_zero_chapter_title(chapter) -> str:
    """
    Generate title for chapter 0 (title page, TOC, annotation, etc.).
    
    Args:
        chapter: The chapter document
        
    Returns:
        Appropriate title for zero chapter
    """
    # Look for specific section titles
    found_sections = []
    
    for block in chapter.blocks:
        if block.type == "heading" and hasattr(block, 'text') and block.text.strip():
            heading_text = block.text.strip().lower()
            
            # Clean heading text
            import re
            clean_heading = re.sub(r'^\d+(\.\d+)*\.?\s*', '', heading_text).strip()
            
            if 'аннотация' in clean_heading:
                found_sections.append('АННОТАЦИЯ')
            elif 'содержание' in clean_heading:
                found_sections.append('СОДЕРЖАНИЕ')
    
    # Return combined title or fallback
    if found_sections:
        return ' и '.join(found_sections)
    
    return 'АННОТАЦИЯ'  # Default for zero chapter


def _get_main_chapter_title(chapter, chapter_num: int) -> str:
    """
    Generate title for main chapters (1, 2, 3, etc.) with proper renumbering.
    
    Args:
        chapter: The chapter document
        chapter_num: The new chapter number (1, 2, 3...)
        
    Returns:
        Properly numbered chapter title
    """
    for block in chapter.blocks:
        if block.type == "heading" and hasattr(block, 'text') and block.text.strip():
            heading_text = block.text.strip()
            
            # Remove old numbering
            import re
            clean_title = re.sub(r'^\d+(\.\d+)*\.?\s*', '', heading_text).strip()
            
            # Return with new numbering
            return f"{chapter_num} {clean_title}"
    
    return ""
