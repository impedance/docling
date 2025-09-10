#!/usr/bin/env python3
"""
Test script to check what text is being extracted from DOCX headings
"""

from core.adapters.docx_parser import parse_docx_to_internal_doc

def test_numbering_extraction():
    docx_file = "docs-docx-pdfs/dev-portal-admin.docx"
    
    print(f"Testing numbering extraction from: {docx_file}")
    print("=" * 60)
    
    try:
        internal_doc, resources = parse_docx_to_internal_doc(docx_file)
        
        print("Extracted headings:")
        heading_count = 0
        for i, block in enumerate(internal_doc.blocks):
            if hasattr(block, 'level') and block.level <= 3:  # Show H1, H2, H3
                print(f"  H{block.level}: '{block.text}'")
                heading_count += 1
                if heading_count >= 15:  # Show first 15 headings
                    print("  ... (truncated)")
                    break
                    
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_numbering_extraction()