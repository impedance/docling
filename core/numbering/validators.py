"""
Validation functions for heading numbering consistency.
"""
import re
from typing import List
from core.numbering.heading_numbering import NumberedHeading


class NumberingValidationError(Exception):
    """Raised when heading numbering validation fails."""
    pass


def validate_numbering(headings: List[NumberedHeading]) -> None:
    """Validate that heading numbering is consistent and monotonic.
    
    Args:
        headings: List of numbered headings to validate
        
    Raises:
        NumberingValidationError: If validation fails
    """
    if not headings:
        return
    
    # Check H1 monotonicity
    _validate_h1_monotonicity(headings)
    
    # Check level consistency (no skipping)
    _validate_level_consistency(headings)
    
    # Check for double numbering in text
    _validate_no_double_numbering(headings)


def _validate_h1_monotonicity(headings: List[NumberedHeading]) -> None:
    """Ensure H1 numbers are monotonic (1, 2, 3, etc.)"""
    h1_numbers = []
    for heading in headings:
        if heading.level == 1:
            # Extract first component of number
            try:
                first_num = int(heading.number.split('.')[0])
                h1_numbers.append(first_num)
            except (ValueError, IndexError):
                raise NumberingValidationError(
                    f"H1 heading has invalid number format: '{heading.number}'"
                )
    
    # Check if numbers are sequential without gaps
    for i, num in enumerate(h1_numbers, 1):
        if num != i:
            raise NumberingValidationError(
                f"H1 numbers are not monotonic. Expected {i}, got {num}"
            )


def _validate_level_consistency(headings: List[NumberedHeading]) -> None:
    """Ensure heading levels don't skip (e.g., no H2 directly followed by H4)"""
    prev_level = 0
    
    for heading in headings:
        level_diff = heading.level - prev_level
        
        # Level can increase by at most 1, or decrease by any amount
        if level_diff > 1:
            raise NumberingValidationError(
                f"Heading level jumps from {prev_level} to {heading.level}. "
                f"Cannot skip levels. Heading: '{heading.text}'"
            )
        
        prev_level = heading.level


def _validate_no_double_numbering(headings: List[NumberedHeading]) -> None:
    """Check that headings don't have double numbering like '1.1 1.1 Title'"""
    for heading in headings:
        # Look for pattern where the number appears twice
        text_after_number = heading.text.strip()
        
        # Remove the expected number from the beginning
        expected_pattern = re.escape(heading.number) + r'\s+'
        if re.match(expected_pattern, text_after_number):
            remaining = re.sub(expected_pattern, '', text_after_number, count=1)
            
            # Check if the remaining text starts with the same number
            if re.match(expected_pattern, remaining):
                raise NumberingValidationError(
                    f"Double numbering detected in heading: '{heading.text}'"
                )


def validate_markdown_numbering(md_text: str) -> None:
    """Validate that all headings in markdown text start with numbers.
    
    Args:
        md_text: Markdown content to validate
        
    Raises:
        NumberingValidationError: If any heading lacks numbering
    """
    lines = md_text.splitlines()
    heading_pattern = re.compile(r'^(#{1,6})\s+(.+)$')
    
    for line_num, line in enumerate(lines, 1):
        match = heading_pattern.match(line)
        if not match:
            continue
        
        level = len(match.group(1))
        title = match.group(2).strip()
        
        # Check if title starts with a number
        if not re.match(r'^[\dIVXLCDM]+(?:[.\-]\d+)*\s+', title, re.IGNORECASE):
            raise NumberingValidationError(
                f"Line {line_num}: Heading missing numbering: '{line}'"
            )