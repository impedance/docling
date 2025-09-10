#!/usr/bin/env python3
"""
Find numbered headings in DOCX file
"""

import zipfile, re
from xml.etree import ElementTree as ET

NS = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}

def find_numbered_headings():
    docx_file = "docs-docx-pdfs/dev-portal-admin.docx"
    
    print(f"Searching for numbered headings in: {docx_file}")
    print("=" * 60)
    
    with zipfile.ZipFile(docx_file) as z:
        doc_xml = z.read("word/document.xml")
        body = ET.fromstring(doc_xml).find(".//w:body", NS)
        
        # Search through all paragraphs for ones that might contain numbering
        print("Searching for paragraphs with numbering patterns:")
        found_numbered = 0
        
        for i, p in enumerate(body.findall("w:p", NS)):
            # Get text content
            texts = []
            for t in p.findall(".//w:t", NS):
                texts.append(t.text or "")
            full_text = "".join(texts).strip()
            
            if full_text:
                # Check if text starts with a number pattern
                patterns = [
                    r'^\d+(\.\d+)*\s+',  # "4.1.3 " or "2.1 " or "2 "
                    r'^\d+(\.\d+)*\.\s+', # "4.1.3. "
                ]
                
                for pattern in patterns:
                    if re.match(pattern, full_text):
                        print(f"  Paragraph {i+1}: '{full_text[:80]}...' " if len(full_text) > 80 else f"  Paragraph {i+1}: '{full_text}'")
                        
                        # Check properties of this paragraph
                        pPr = p.find("w:pPr", NS)
                        if pPr is not None:
                            # Check for numbering
                            numPr = pPr.find("w:numPr", NS)
                            if numPr is not None:
                                numId_el = numPr.find("w:numId", NS)
                                ilvl_el = numPr.find("w:ilvl", NS)
                                numId = numId_el.attrib.get(f"{{{NS['w']}}}val", "") if numId_el is not None else ""
                                ilvl = ilvl_el.attrib.get(f"{{{NS['w']}}}val", "") if ilvl_el is not None else ""
                                print(f"    Has numPr: numId={numId}, ilvl={ilvl}")
                            
                            # Check for outline level
                            outline = pPr.find("w:outlineLvl", NS)
                            if outline is not None:
                                val = outline.attrib.get(f"{{{NS['w']}}}val")
                                print(f"    Has outline level: {val}")
                            
                            # Check for style
                            pStyle = pPr.find("w:pStyle", NS)
                            if pStyle is not None:
                                style = pStyle.attrib.get(f"{{{NS['w']}}}val", "")
                                print(f"    Has style: {style}")
                        
                        found_numbered += 1
                        if found_numbered >= 10:  # Limit output
                            print("  ... (showing first 10 matches)")
                            break
                        
                        break  # Found a pattern, no need to check other patterns for this paragraph
                
                if found_numbered >= 10:
                    break

if __name__ == "__main__":
    find_numbered_headings()