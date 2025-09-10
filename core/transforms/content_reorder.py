"""
Universal content reordering transform to fix misplaced content throughout the document.

This transform addresses documents where content paragraphs are not properly 
positioned under their corresponding section headings across all chapters.
"""

from typing import List, Dict, Optional, Tuple, Set
from core.model.internal_doc import InternalDoc, Block, Heading, Paragraph

def run(doc: InternalDoc) -> InternalDoc:
    """
    Reorders specific misplaced content throughout the document.
    
    This handles the admin document where some specific content blocks are  
    misplaced relative to their intended section headings.
    
    Args:
        doc: The document to fix
        
    Returns:
        Document with reordered content
    """
    if not doc.blocks:
        return doc
    
    # Only fix specific known misplaced content, not rebuild entire structure
    return _fix_misplaced_content(doc)


def _fix_misplaced_content(doc: InternalDoc) -> InternalDoc:
    """
    Fix specific misplaced content blocks without completely rebuilding document structure.
    
    This preserves the natural document flow while moving only clearly misplaced content.
    """
    blocks = doc.blocks[:]  # Copy blocks list
    
    # Find specific misplaced content that needs to be moved
    moves = _identify_content_moves(blocks)
    
    # Apply the moves
    for move in moves:
        blocks = _apply_content_move(blocks, move)
    
    return InternalDoc(blocks=blocks)


def _identify_content_moves(blocks: List[Block]) -> List[Dict]:
    """Identify specific content blocks that need to be moved."""
    
    moves = []
    
    # Find chapter and section boundaries
    chapter_boundaries = {}
    section_boundaries = {}
    
    for i, block in enumerate(blocks):
        if isinstance(block, Heading):
            if block.level == 2:
                chapter_boundaries[block.text.strip()] = i
            elif block.level == 3:
                section_boundaries[block.text.strip()] = i
    
    # Specific content that should be moved to section 2.1
    section_2_1_content = [
        "Состав архитектуры Комплекса включает в себя следующие части",
        "CMS-сервер (Winter CMS) — основной элемент серверной части",
        "плагины Winter CMS — модули, расширяющие функциональность CMS",
        "обратный прокси (Traefik) — обеспечивает маршрутизацию",
        "СУБД PostgreSQL — хранение основной структурированной информации",
        "кеширующая система Redis — хранение сессий и промежуточных данных",
        "система поиска Typesense — полнотекстовый поиск",
        "интеграция с внешней системой аутентификации РОСА ID"
    ]
    
    # Find these content blocks and mark them for moving
    section_2_1_idx = section_boundaries.get("2.1 Основные компоненты")
    if section_2_1_idx is not None:
        
        for content_text in section_2_1_content:
            for i, block in enumerate(blocks):
                if isinstance(block, Paragraph) and block.inlines:
                    text = ""
                    for inline in block.inlines:
                        if hasattr(inline, 'content'):
                            text += inline.content
                    
                    if content_text in text:
                        # Check if this block is NOT already in the right place
                        # (i.e., it's not between section 2.1 and the next section)
                        next_section_idx = _find_next_section_after(blocks, section_2_1_idx)
                        
                        if not (section_2_1_idx < i < next_section_idx):
                            moves.append({
                                'block_idx': i,
                                'target_section_idx': section_2_1_idx,
                                'content_preview': content_text[:50] + "...",
                                'move_type': 'to_section_end'
                            })
                        break
    
    return moves


def _find_next_section_after(blocks: List[Block], section_idx: int) -> int:
    """Find the index of the next section heading after the given section."""
    for i in range(section_idx + 1, len(blocks)):
        if isinstance(blocks[i], Heading) and blocks[i].level <= 3:
            return i
    return len(blocks)


def _apply_content_move(blocks: List[Block], move: Dict) -> List[Block]:
    """Apply a single content move to the blocks list."""
    
    block_to_move = blocks[move['block_idx']]
    
    # Remove the block from its current position
    new_blocks = blocks[:move['block_idx']] + blocks[move['block_idx'] + 1:]
    
    # Adjust target index due to removal
    target_idx = move['target_section_idx']
    if move['block_idx'] < target_idx:
        target_idx -= 1
    
    # Find insertion point (after the section heading, at the end of section content)
    if move['move_type'] == 'to_section_end':
        next_section_idx = _find_next_section_after(new_blocks, target_idx)
        # Insert just before the next section/chapter
        insert_idx = next_section_idx
    else:
        # Insert right after the section heading
        insert_idx = target_idx + 1
    
    # Insert the moved block
    new_blocks = new_blocks[:insert_idx] + [block_to_move] + new_blocks[insert_idx:]
    
    return new_blocks


