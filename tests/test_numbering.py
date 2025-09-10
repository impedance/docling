"""
Unit tests for heading numbering functionality.
"""
import pytest
from unittest.mock import patch, mock_open
import tempfile
import zipfile
from pathlib import Path

from core.numbering.heading_numbering import (
    NumberedHeading, 
    extract_headings_with_numbers,
    _fmt,
    _roman,
    _slug
)
from core.numbering.md_numbering import apply_numbers_to_markdown
from core.numbering.validators import (
    validate_numbering, 
    validate_markdown_numbering,
    NumberingValidationError
)
from core.output.file_naming import chapter_index_from_h1, generate_chapter_filename


class TestHeadingNumbering:
    """Tests for XML-based heading numbering extraction."""
    
    def test_roman_formatting(self):
        """Test Roman numeral formatting."""
        assert _roman(1) == "I"
        assert _roman(4) == "IV"
        assert _roman(9) == "IX"
        assert _roman(10) == "X"
        assert _roman(50) == "L"
    
    def test_number_formatting(self):
        """Test various number formats."""
        assert _fmt("decimal", 5) == "5"
        assert _fmt("upperroman", 3) == "III"
        assert _fmt("lowerroman", 4) == "iv"
        assert _fmt("upperletter", 1) == "A"
        assert _fmt("lowerletter", 2) == "b"
    
    def test_slug_generation(self):
        """Test slug generation from text."""
        assert _slug("Technical Requirements") == "technical-requirements"
        assert _slug("Технические требования") == "технические-требования"
        assert _slug("Test with 123 numbers!") == "test-with-123-numbers"
    
    def test_extract_headings_with_mock_docx(self):
        """Test heading extraction with mocked DOCX data."""
        # This is a simplified test - in real scenarios we'd need proper XML
        mock_document_xml = b'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
        <w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
        <w:body>
            <w:p>
                <w:pPr>
                    <w:outlineLvl w:val="0"/>
                </w:pPr>
                <w:r><w:t>Test Heading</w:t></w:r>
            </w:p>
        </w:body>
        </w:document>'''
        
        mock_numbering_xml = b'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
        <w:numbering xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
        </w:numbering>'''
        
        mock_styles_xml = b'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
        <w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
        </w:styles>'''
        
        with patch('zipfile.ZipFile') as mock_zip:
            mock_zip.return_value.__enter__.return_value.read.side_effect = [
                mock_document_xml, mock_numbering_xml, mock_styles_xml
            ]
            
            headings = extract_headings_with_numbers("fake.docx")
            assert len(headings) == 1
            assert headings[0].text == "Test Heading"
            assert headings[0].level == 1
            assert headings[0].number == "1"


class TestMdNumbering:
    """Tests for markdown numbering application."""
    
    def test_apply_numbers_basic(self):
        """Test basic number application to markdown."""
        md_text = """# Introduction
## Overview
# Implementation
## Details"""
        
        headings = [
            NumberedHeading(level=1, text="Introduction", number="1", anchor="introduction"),
            NumberedHeading(level=2, text="Overview", number="1.1", anchor="overview"),
            NumberedHeading(level=1, text="Implementation", number="2", anchor="implementation"),
            NumberedHeading(level=2, text="Details", number="2.1", anchor="details")
        ]
        
        result = apply_numbers_to_markdown(md_text, headings)
        
        lines = result.splitlines()
        assert lines[0] == "# 1 Introduction"
        assert lines[1] == "## 1.1 Overview"
        assert lines[2] == "# 2 Implementation"
        assert lines[3] == "## 2.1 Details"
    
    def test_apply_numbers_with_existing(self):
        """Test applying numbers when headings already have numbering."""
        md_text = """# 1.5 Old Number Introduction
## 2.3 Old Number Overview"""
        
        headings = [
            NumberedHeading(level=1, text="Introduction", number="1", anchor="introduction"),
            NumberedHeading(level=2, text="Overview", number="1.1", anchor="overview")
        ]
        
        result = apply_numbers_to_markdown(md_text, headings)
        
        lines = result.splitlines()
        assert lines[0] == "# 1 Old Number Introduction"  # Should include the cleaned text
        assert lines[1] == "## 1.1 Old Number Overview"
    
    def test_apply_numbers_insufficient_headings(self):
        """Test behavior when there are fewer numbered headings than markdown headings."""
        md_text = """# First
# Second
# Third"""
        
        headings = [
            NumberedHeading(level=1, text="First", number="1", anchor="first")
        ]
        
        result = apply_numbers_to_markdown(md_text, headings)
        
        lines = result.splitlines()
        assert lines[0] == "# 1 First"
        assert lines[1] == "# Second"  # No number applied
        assert lines[2] == "# Third"   # No number applied


class TestValidators:
    """Tests for numbering validation."""
    
    def test_validate_numbering_success(self):
        """Test successful validation."""
        headings = [
            NumberedHeading(level=1, text="Introduction", number="1", anchor="intro"),
            NumberedHeading(level=2, text="Overview", number="1.1", anchor="overview"),
            NumberedHeading(level=2, text="Details", number="1.2", anchor="details"),
            NumberedHeading(level=1, text="Implementation", number="2", anchor="impl")
        ]
        
        # Should not raise any exception
        validate_numbering(headings)
    
    def test_validate_h1_monotonicity_failure(self):
        """Test H1 monotonicity validation failure."""
        headings = [
            NumberedHeading(level=1, text="Introduction", number="1", anchor="intro"),
            NumberedHeading(level=1, text="Implementation", number="3", anchor="impl")  # Skips 2
        ]
        
        with pytest.raises(NumberingValidationError, match="not monotonic"):
            validate_numbering(headings)
    
    def test_validate_level_consistency_failure(self):
        """Test level consistency validation failure."""
        headings = [
            NumberedHeading(level=1, text="Introduction", number="1", anchor="intro"),
            NumberedHeading(level=3, text="Details", number="1.1.1", anchor="details")  # Skips level 2
        ]
        
        with pytest.raises(NumberingValidationError, match="level jumps"):
            validate_numbering(headings)
    
    def test_validate_markdown_numbering_success(self):
        """Test successful markdown validation."""
        md_text = """# 1 Introduction
## 1.1 Overview
# 2 Implementation"""
        
        # Should not raise any exception
        validate_markdown_numbering(md_text)
    
    def test_validate_markdown_numbering_failure(self):
        """Test markdown validation failure."""
        md_text = """# 1 Introduction
## Overview
# 2 Implementation"""  # Second heading missing number
        
        with pytest.raises(NumberingValidationError, match="missing numbering"):
            validate_markdown_numbering(md_text)


class TestFileNaming:
    """Tests for file naming with extracted chapter numbers."""
    
    def test_chapter_index_extraction(self):
        """Test extracting chapter index from H1 text."""
        assert chapter_index_from_h1("1 Introduction") == 1
        assert chapter_index_from_h1("3.1 Technical Requirements") == 3
        assert chapter_index_from_h1("# 2 Architecture") == 2
        assert chapter_index_from_h1("No number here") == 1  # fallback
    
    def test_generate_chapter_filename(self):
        """Test generating chapter filename with number extraction."""
        # Test title page (index 0)
        filename = generate_chapter_filename(0, "АО НТЦ ИТ РОСА")
        assert filename == "00-ao-ntts-it-rosa.md"
        
        # Test with numbered heading
        filename = generate_chapter_filename(99, "3 Technical Requirements")
        assert filename == "03-technical-requirements.md"
        
        # Test fallback when no number in title
        filename = generate_chapter_filename(5, "Just a Title")
        assert filename == "05-just-a-title.md"
        
        # Test with complex numbering
        filename = generate_chapter_filename(1, "1.2 Setup and Installation")
        assert filename == "01-setup-and-installation.md"


# Integration test
def test_integration_numbering_pipeline():
    """Test the complete numbering pipeline integration."""
    # Create sample headings as if extracted from DOCX
    extracted_headings = [
        NumberedHeading(level=1, text="Общие сведения", number="1", anchor="obschie-svedeniya"),
        NumberedHeading(level=2, text="Функциональное назначение", number="1.1", anchor="funkcionalnoe-naznachenie"),
        NumberedHeading(level=1, text="Архитектура комплекса", number="2", anchor="arhitektura-kompleksa"),
        NumberedHeading(level=2, text="Основные компоненты", number="2.1", anchor="osnovnye-komponenty")
    ]
    
    # Validate the headings
    validate_numbering(extracted_headings)
    
    # Apply to markdown
    mock_md = """# Общие сведения
## Функциональное назначение  
# Архитектура комплекса
## Основные компоненты"""
    
    numbered_md = apply_numbers_to_markdown(mock_md, extracted_headings)
    
    # Validate the result
    validate_markdown_numbering(numbered_md)
    
    # Test filename generation
    filename1 = generate_chapter_filename(1, "1 Общие сведения")
    filename2 = generate_chapter_filename(2, "2 Архитектура комплекса")
    
    assert filename1 == "01-obshchie-svedeniia.md"
    assert filename2 == "02-arkhitektura-kompleksa.md"