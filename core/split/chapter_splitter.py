from typing import List, Set
from pydantic import BaseModel

from core.model.internal_doc import InternalDoc, Heading, Block

class ChapterRules(BaseModel):
    """Defines the rules for splitting a document into chapters."""
    level: int = 1 # The heading level to split on.
    # Special section titles that should be grouped with title page as chapter 0
    zero_chapter_sections: Set[str] = {"аннотация", "содержание", "ао \"нтц ит роса\""}

def split_into_chapters(doc: InternalDoc, rules: ChapterRules) -> List[InternalDoc]:
    """
    Splits a single InternalDoc into a list of InternalDocs, each representing a chapter.

    Args:
        doc: The document to split.
        rules: The rules defining how to split the document.

    Returns:
        A list of InternalDoc objects, where each is a chapter.
    """
    if not doc.blocks:
        return []

    # First pass: collect zero-chapter blocks (title page, annotation, TOC, etc.)
    zero_chapter_blocks: List[Block] = []
    main_content_blocks: List[Block] = []
    
    collecting_zero_chapter = True
    
    for block in doc.blocks:
        is_split_heading = isinstance(block, Heading) and block.level == rules.level
        
        if is_split_heading:
            heading_text = block.text.strip().lower()
            # Remove numbering and check if this should be in zero chapter
            clean_heading = _clean_heading_for_comparison(heading_text)
            
            if clean_heading in rules.zero_chapter_sections:
                # This heading belongs to zero chapter
                zero_chapter_blocks.append(block)
                collecting_zero_chapter = True
            else:
                # This is the first "real" chapter - stop collecting for zero chapter
                collecting_zero_chapter = False
                main_content_blocks.append(block)
        else:
            if collecting_zero_chapter:
                zero_chapter_blocks.append(block)
            else:
                main_content_blocks.append(block)
    
    # Now split main content into chapters
    chapters: List[InternalDoc] = []
    
    # Add zero chapter if it has content
    if zero_chapter_blocks:
        chapters.append(InternalDoc(blocks=zero_chapter_blocks))
    
    # Split remaining content into chapters
    current_chapter_blocks: List[Block] = []
    
    for block in main_content_blocks:
        is_split_heading = isinstance(block, Heading) and block.level == rules.level
        
        if is_split_heading and current_chapter_blocks:
            # Start of a new chapter, so we finalize the previous one
            chapters.append(InternalDoc(blocks=current_chapter_blocks))
            current_chapter_blocks = [block]  # Start the new chapter with the heading
        else:
            # Continue adding to the current chapter
            current_chapter_blocks.append(block)
    
    # Add the last remaining chapter
    if current_chapter_blocks:
        chapters.append(InternalDoc(blocks=current_chapter_blocks))
    
    return chapters


def _clean_heading_for_comparison(heading_text: str) -> str:
    """
    Clean heading text for comparison by removing numbers and extra formatting.
    
    Args:
        heading_text: The raw heading text
        
    Returns:
        Cleaned text for comparison
    """
    import re
    # Remove various numbering patterns (1, 1.1, 0.0.0.0.0.0.0.0.1, etc.)
    cleaned = re.sub(r'^\d+(\.\d+)*\.?\s*', '', heading_text)
    return cleaned.strip().lower()
