#!/usr/bin/env python3
"""
Create chapter files using our integrated pipeline for cu-admin-install.docx
"""

import os
from pathlib import Path
from core.adapters.document_parser import parse_document
from core.numbering.auto_numberer import add_automatic_numbering

def create_chapters_from_docx(docx_file: str, output_dir: str):
    """Create chapter markdown files from DOCX using our integrated parser."""
    output_path = Path(output_dir)
    doc_name = Path(docx_file).stem
    doc_output = output_path / doc_name
    doc_output.mkdir(parents=True, exist_ok=True)
    
    print(f"Creating chapters from: {docx_file}")
    print(f"Output directory: {doc_output}")
    print("=" * 60)
    
    try:
        internal_doc, resources = parse_document(docx_file)
        
        # Add automatic hierarchical numbering to all headings
        numbered_doc = add_automatic_numbering(internal_doc)
        print(f"Added automatic numbering to headings")
        
        # Group content by H1 chapters
        chapters = []
        current_chapter = {"title": "front-matter", "blocks": []}
        
        for block in numbered_doc.blocks:
            if hasattr(block, 'level') and block.level == 1:
                # Start new chapter
                if current_chapter["blocks"]:
                    chapters.append(current_chapter)
                current_chapter = {"title": block.text, "blocks": [block]}
            else:
                current_chapter["blocks"].append(block)
        
        # Add last chapter
        if current_chapter["blocks"]:
            chapters.append(current_chapter)
        
        written_files = []
        
        # Write each chapter to a file
        for i, chapter in enumerate(chapters, 1):
            # Create filename
            title_slug = chapter["title"].lower()
            title_slug = "".join(c if c.isalnum() or c in " -_" else "" for c in title_slug)
            title_slug = "-".join(title_slug.split())[:50]
            
            filename = f"{i:02d}-{title_slug}.md"
            file_path = doc_output / filename
            
            # Generate markdown content
            content_lines = []
            
            for block in chapter["blocks"]:
                if hasattr(block, 'level'):  # Heading
                    content_lines.append(f"{'#' * block.level} {block.text}")
                elif hasattr(block, 'inlines'):  # Paragraph
                    # Extract text from inlines
                    text_parts = []
                    for inline in block.inlines:
                        if hasattr(inline, 'content'):
                            text_parts.append(inline.content)
                    text = "".join(text_parts).strip()
                    if text:
                        content_lines.append(text)
                
                content_lines.append("")  # Add blank line after each block
            
            # Write file
            content = "\n".join(content_lines)
            file_path.write_text(content, encoding='utf-8')
            written_files.append(file_path)
            
            print(f"Created: {filename} ({len(chapter['blocks'])} blocks)")
        
        print(f"\nTotal chapters created: {len(chapters)}")
        print(f"Written files:")
        for file_path in written_files:
            print(f" - {file_path}")
            
        return chapters, written_files
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return [], []

if __name__ == "__main__":
    docx_file = "docs-docx-pdfs/dev-portal-admin.docx"
    output_dir = "dev_portal_chapters_with_numbering"
    
    chapters, files = create_chapters_from_docx(docx_file, output_dir)
    
    if files:
        print(f"\n✅ Successfully created {len(chapters)} chapter files!")
    else:
        print(f"\n❌ Failed to create chapter files!")