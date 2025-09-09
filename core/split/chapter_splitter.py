from typing import List
from pydantic import BaseModel

from core.model.internal_doc import InternalDoc, Heading, Block

class ChapterRules(BaseModel):
    """Defines the rules for splitting a document into chapters."""
    level: int = 1 # The heading level to split on.

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

    chapters: List[InternalDoc] = []
    current_chapter_blocks: List[Block] = []

    for block in doc.blocks:
        is_split_heading = isinstance(block, Heading) and block.level == rules.level

        if is_split_heading and current_chapter_blocks:
            # Start of a new chapter, so we finalize the previous one.
            chapters.append(InternalDoc(blocks=current_chapter_blocks))
            current_chapter_blocks = [block] # Start the new chapter with the heading
        else:
            # Continue adding to the current chapter.
            current_chapter_blocks.append(block)

    # Add the last remaining chapter
    if current_chapter_blocks:
        chapters.append(InternalDoc(blocks=current_chapter_blocks))

    return chapters
