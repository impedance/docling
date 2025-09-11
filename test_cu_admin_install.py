#!/usr/bin/env python3
"""
Test DOCX parsing with cu-admin-install.docx file.
"""

from core.adapters.document_parser import parse_document

def test_cu_admin_docx():
    """Test cu-admin-install.docx parsing."""
    docx_file = "real-docs/cu-admin-install.docx"
    
    print(f"Testing DOCX parsing with: {docx_file}")
    print("=" * 60)
    
    try:
        internal_doc, resources = parse_document(docx_file)
        
        print(f"Successfully parsed document:")
        print(f"- Total blocks: {len(internal_doc.blocks)}")
        
        # Count and display headings by level
        heading_counts = {}
        h1_headings = []
        all_headings = []
        paragraph_count = 0
        
        for block in internal_doc.blocks:
            if hasattr(block, 'level'):  # It's a heading
                level = block.level
                heading_counts[level] = heading_counts.get(level, 0) + 1
                all_headings.append((level, block.text))
                
                if level == 1:
                    h1_headings.append(block.text)
                    print(f"  H{level}: {block.text}")
                elif level <= 3:  # Show H2 and H3 as well
                    print(f"    H{level}: {block.text[:60]}...")
            else:  # It's a paragraph
                paragraph_count += 1
        
        print(f"\nH1 Chapters found ({len(h1_headings)}):")
        for i, title in enumerate(h1_headings, 1):
            print(f"{i}. {title}")
        
        print(f"\nSummary:")
        for level in sorted(heading_counts.keys()):
            print(f"- H{level} headings: {heading_counts[level]}")
        print(f"- Paragraphs: {paragraph_count}")
        print(f"- Resources: {len(resources)}")
        
        return True, len(h1_headings)
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False, 0

if __name__ == "__main__":
    success, chapter_count = test_cu_admin_docx()
    if success:
        print(f"\n✅ DOCX parsing successful! Found {chapter_count} main chapters.")
    else:
        print(f"\n❌ DOCX parsing failed!")