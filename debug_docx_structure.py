#!/usr/bin/env python3
"""
Debug script to inspect DOCX XML structure for numbering
"""

import zipfile
from xml.etree import ElementTree as ET
from pathlib import Path

NS = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}

def debug_docx_structure():
    docx_file = "docs-docx-pdfs/dev-portal-admin.docx"
    
    print(f"Debugging DOCX structure: {docx_file}")
    print("=" * 60)
    
    with zipfile.ZipFile(docx_file) as z:
        # List all files in the DOCX
        print("Files in DOCX:")
        for name in z.namelist():
            print(f"  {name}")
        print()
        
        # Read document.xml
        doc_xml = z.read("word/document.xml")
        body = ET.fromstring(doc_xml).find(".//w:body", NS)
        
        # Read numbering.xml if it exists
        numbering_xml = None
        if "word/numbering.xml" in z.namelist():
            numbering_xml = z.read("word/numbering.xml")
            print("Found numbering.xml!")
        else:
            print("No numbering.xml found")
        print()
        
        # Examine first few paragraphs in detail
        print("First few paragraphs (detailed):")
        for i, p in enumerate(body.findall("w:p", NS)[:10]):
            print(f"\nParagraph {i+1}:")
            
            # Check paragraph properties
            pPr = p.find("w:pPr", NS)
            if pPr is not None:
                print("  Properties found:")
                
                # Check for numbering
                numPr = pPr.find("w:numPr", NS)
                if numPr is not None:
                    numId_el = numPr.find("w:numId", NS)
                    ilvl_el = numPr.find("w:ilvl", NS)
                    numId = numId_el.attrib.get(f"{{{NS['w']}}}val", "") if numId_el is not None else ""
                    ilvl = ilvl_el.attrib.get(f"{{{NS['w']}}}val", "") if ilvl_el is not None else ""
                    print(f"    Numbering: numId={numId}, ilvl={ilvl}")
                
                # Check for outline level
                outline = pPr.find("w:outlineLvl", NS)
                if outline is not None:
                    val = outline.attrib.get(f"{{{NS['w']}}}val")
                    print(f"    Outline level: {val}")
                
                # Check for style
                pStyle = pPr.find("w:pStyle", NS)
                if pStyle is not None:
                    style = pStyle.attrib.get(f"{{{NS['w']}}}val", "")
                    print(f"    Style: {style}")
            
            # Get text content
            texts = []
            for t in p.findall(".//w:t", NS):
                texts.append(t.text or "")
            full_text = "".join(texts).strip()
            
            if full_text:
                print(f"  Text: '{full_text}'")
                
                # Check first run for potential numbering
                first_run = p.find(".//w:r", NS)
                if first_run is not None:
                    run_texts = []
                    for t in first_run.findall("w:t", NS):
                        run_texts.append(t.text or "")
                    first_run_text = "".join(run_texts)
                    if first_run_text:
                        print(f"  First run: '{first_run_text}'")

if __name__ == "__main__":
    debug_docx_structure()