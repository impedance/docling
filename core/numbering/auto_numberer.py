"""
Automatic hierarchical numbering for document headings.
Generates numbering like: 1, 1.1, 1.1.1, 1.2, 2, 2.1, etc.
"""

from typing import List, Dict
from core.model.internal_doc import InternalDoc, Block, Heading

class AutoNumberer:
    """Generates automatic hierarchical numbering for headings."""
    
    def __init__(self):
        self.counters: Dict[int, int] = {}  # level -> counter
        self.reset()
    
    def reset(self):
        """Reset all counters."""
        self.counters = {}
    
    def get_number_for_level(self, level: int) -> str:
        """Get the next number for the given heading level.
        
        Args:
            level: Heading level (1, 2, 3, etc.)
            
        Returns:
            String representation of the number (e.g., "1.2.3")
        """
        # Increment counter for this level
        self.counters[level] = self.counters.get(level, 0) + 1
        
        # Reset counters for all deeper levels
        levels_to_remove = [l for l in self.counters if l > level]
        for l in levels_to_remove:
            del self.counters[l]
        
        # Build number string from level 1 down to current level
        number_parts = []
        for l in range(1, level + 1):
            if l in self.counters:
                number_parts.append(str(self.counters[l]))
        
        return ".".join(number_parts)

def add_automatic_numbering(doc: InternalDoc) -> InternalDoc:
    """Add automatic hierarchical numbering to all headings in the document.
    
    Args:
        doc: InternalDoc with headings to number
        
    Returns:
        New InternalDoc with numbered headings
    """
    numberer = AutoNumberer()
    new_blocks: List[Block] = []
    
    for block in doc.blocks:
        if isinstance(block, Heading):
            # Generate number for this heading level
            number = numberer.get_number_for_level(block.level)
            
            # Check if heading already has numbering
            text = block.text.strip()
            if text and not text[0].isdigit():
                # Add numbering to heading text
                numbered_text = f"{number} {text}"
                new_block = Heading(level=block.level, text=numbered_text)
            else:
                # Heading might already have numbering, replace it
                # Find where the title starts (after potential existing numbering)
                import re
                match = re.match(r'^[\d\.\s]+(.+)$', text)
                if match:
                    title = match.group(1).strip()
                    numbered_text = f"{number} {title}"
                else:
                    numbered_text = f"{number} {text}"
                new_block = Heading(level=block.level, text=numbered_text)
            
            new_blocks.append(new_block)
        else:
            # Keep non-heading blocks as-is
            new_blocks.append(block)
    
    return InternalDoc(blocks=new_blocks)

def add_numbering_to_chapters(chapters: List[InternalDoc]) -> List[InternalDoc]:
    """Add automatic numbering across all chapters in sequence.
    
    Args:
        chapters: List of chapter InternalDocs
        
    Returns:
        List of chapters with continuous numbering across all chapters
    """
    numberer = AutoNumberer()
    numbered_chapters: List[InternalDoc] = []
    
    for chapter in chapters:
        new_blocks: List[Block] = []
        
        for block in chapter.blocks:
            if isinstance(block, Heading):
                # Generate number for this heading level
                number = numberer.get_number_for_level(block.level)
                
                # Add numbering to heading text
                text = block.text.strip()
                if text and not text[0].isdigit():
                    # Add numbering
                    numbered_text = f"{number} {text}"
                else:
                    # Replace existing numbering
                    import re
                    match = re.match(r'^[\d\.\s]+(.+)$', text)
                    if match:
                        title = match.group(1).strip()
                        numbered_text = f"{number} {title}"
                    else:
                        numbered_text = f"{number} {text}"
                
                new_block = Heading(level=block.level, text=numbered_text)
                new_blocks.append(new_block)
            else:
                # Keep non-heading blocks as-is
                new_blocks.append(block)
        
        numbered_chapters.append(InternalDoc(blocks=new_blocks))
    
    return numbered_chapters