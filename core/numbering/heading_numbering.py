# heading_numbering.py
import zipfile, re
from xml.etree import ElementTree as ET
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}

@dataclass
class NumberedHeading:
    level: int
    text: str
    number: str
    anchor: str
    num_id: Optional[int] = None
    ilvl: Optional[int] = None

@dataclass
class Lvl:
    ilvl: int
    start: int = 1
    numFmt: str = "decimal"
    lvlText: str = "%1."
    restart: Optional[int] = None

@dataclass
class NumDef:
    numId: int
    abstractNumId: int
    lvls: Dict[int, Lvl]

_ROMAN = ["","I","II","III","IV","V","VI","VII","VIII","IX","X","XI","XII","XIII","XIV","XV","XVI","XVII","XVIII","XIX","XX"]
def _roman(n:int)->str:
    if n < len(_ROMAN): return _ROMAN[n]
    res, vals = "", [(1000,"M"),(900,"CM"),(500,"D"),(400,"CD"),(100,"C"),(90,"XC"),(50,"L"),(40,"XL"),(10,"X"),(9,"IX"),(5,"V"),(4,"IV"),(1,"I")]
    for v,s in vals:
        while n>=v: res+=s; n-=v
    return res

def _fmt(fmt: str, n: int) -> str:
    fmt = (fmt or "").lower()
    if fmt in ("decimal","decimalzero","cardinaltext"): return str(n)
    if fmt in ("upperroman","roman"): return _roman(n)
    if fmt == "lowerroman": return _roman(n).lower()
    if fmt == "upperletter": return chr(ord('A') + ((n-1) % 26))
    if fmt == "lowerletter": return chr(ord('a') + ((n-1) % 26))
    return str(n)

def _slug(s:str)->str:
    s = s.strip().lower()
    s = re.sub(r'[^a-z0-9\u0400-\u04FF\s-]+', '', s)
    s = re.sub(r'\s+', '-', s)
    return re.sub(r'-+', '-', s).strip('-')

def _parse_numbering(xml: bytes) -> Dict[int, NumDef]:
    root = ET.fromstring(xml); nums: Dict[int, NumDef] = {}; abstract: Dict[int, Dict[int, Lvl]] = {}
    for an in root.findall("w:abstractNum", NS):
        an_id = int(an.get(f"{{{NS['w']}}}abstractNumId")); lvls={}
        for lvl in an.findall("w:lvl", NS):
            ilvl = int(lvl.get(f"{{{NS['w']}}}ilvl"))
            start = lvl.find("w:start", NS); start_val = int(start.get(f"{{{NS['w']}}}val")) if start is not None else 1
            numFmt_el = lvl.find("w:numFmt", NS); fmt = numFmt_el.get(f"{{{NS['w']}}}val") if numFmt_el is not None else "decimal"
            lvlText_el = lvl.find("w:lvlText", NS); lvlText = lvlText_el.get(f"{{{NS['w']}}}val") if lvlText_el is not None else "%1."
            restart_el = lvl.find("w:lvlRestart", NS); restart = int(restart_el.get(f"{{{NS['w']}}}val")) if restart_el is not None else None
            lvls[ilvl] = Lvl(ilvl, start_val, fmt, lvlText, restart)
        abstract[an_id] = lvls
    for n in root.findall("w:num", NS):
        numId = int(n.get(f"{{{NS['w']}}}numId"))
        an_ref = n.find("w:abstractNumId", NS)
        if an_ref is None: continue
        an_id = int(an_ref.get(f"{{{NS['w']}}}val"))
        nums[numId] = NumDef(numId, an_id, abstract.get(an_id, {}))
    return nums

def _style_to_level(styles_xml: Optional[bytes]) -> Dict[str, int]:
    if not styles_xml: return {}
    res: Dict[str,int] = {}
    root = ET.fromstring(styles_xml)
    for s in root.findall("w:style", NS):
        if s.get(f"{{{NS['w']}}}type") != "paragraph": continue
        sid = s.get(f"{{{NS['w']}}}styleId")
        name_el = s.find("w:name", NS); name = (name_el.get(f"{{{NS['w']}}}val") if name_el is not None else "").lower()
        if sid and (name.startswith("heading") or "заголовок" in name):
            m = re.search(r'(\d+)$', sid) or re.search(r'(\d+)$', name)
            if m: res[sid] = int(m.group(1)) - 1
        ppr = s.find("w:pPr", NS); ol = ppr.find("w:outlineLvl", NS) if ppr is not None else None
        if ol is not None and sid:
            lvl = int(ol.get(f"{{{NS['w']}}}val")); res[sid] = min(res.get(sid, lvl), lvl) if sid in res else lvl
    return res

def extract_headings_with_numbers(docx_path: str) -> List[NumberedHeading]:
    with zipfile.ZipFile(docx_path, "r") as z:
        doc = z.read("word/document.xml")
        try:
            numbering = z.read("word/numbering.xml")
        except KeyError:
            numbering = b"<numbering/>"  # Empty numbering if file doesn't exist
        try:
            styles = z.read("word/styles.xml")
        except KeyError:
            styles = b"<styles/>"  # Empty styles if file doesn't exist
    
    nums = _parse_numbering(numbering)
    style2lvl = _style_to_level(styles)
    root = ET.fromstring(doc); body = root.find("w:body", NS)
    counters_by_numId: Dict[int, List[int]] = {}
    results: List[NumberedHeading] = []

    for p in body.findall("w:p", NS):
        ppr = p.find("w:pPr", NS)
        if ppr is None: continue
        style_el = ppr.find("w:pStyle", NS)
        style_id = style_el.get(f"{{{NS['w']}}}val") if style_el is not None else None

        level = None
        if style_id and style_id in style2lvl: level = style2lvl[style_id]
        if level is None:
            ol = ppr.find("w:outlineLvl", NS)
            if ol is not None: level = int(ol.get(f"{{{NS['w']}}}val"))
        if level is None and style_id and re.match(r'(?i)Heading\d+|Заголовок\s*\d+', style_id):
            m = re.search(r'(\d+)$', style_id);  level = int(m.group(1)) - 1 if m else None
        text = ''.join(t.text or '' for t in p.findall(".//w:t", NS)).strip()
        if level is None or not text: continue

        number_text = ""; numId = None; ilvl = None
        numPr = ppr.find("w:numPr", NS)
        if numPr is not None:
            ilvl_el = numPr.find("w:ilvl", NS); numId_el = numPr.find("w:numId", NS)
            if ilvl_el is not None and numId_el is not None:
                ilvl = int(ilvl_el.get(f"{{{NS['w']}}}val")); numId = int(numId_el.get(f"{{{NS['w']}}}val"))
                ndef = nums.get(numId)
                if ndef:
                    if numId not in counters_by_numId:
                        counters_by_numId[numId] = [0]*10
                        for i in range(10):
                            if i in ndef.lvls: counters_by_numId[numId][i] = ndef.lvls[i].start - 1
                    for i in range(ilvl+1,10): counters_by_numId[numId][i] = 0
                    counters_by_numId[numId][ilvl] += 1
                    parts = []
                    for i in range(ilvl+1):
                        n = counters_by_numId[numId][i]
                        fmt = ndef.lvls.get(i, Lvl(i)).numFmt
                        parts.append(_fmt(fmt, n))
                    lvlText = ndef.lvls.get(ilvl, Lvl(ilvl)).lvlText or ("%1."*(ilvl+1))
                    out = lvlText
                    for idx, pnum in enumerate(parts, start=1):
                        out = out.replace(f"%{idx}", pnum)
                    number_text = out.strip().rstrip(".")
        if not number_text:
            GLOBAL = -1
            if GLOBAL not in counters_by_numId: counters_by_numId[GLOBAL] = [0]*9
            stack = counters_by_numId[GLOBAL]
            for i in range(level+1,9): stack[i] = 0
            stack[level] += 1
            number_text = ".".join(str(stack[i]) for i in range(level+1))

        results.append(NumberedHeading(
            level=level+1, text=text, number=number_text, anchor=_slug(text),
            num_id=numId, ilvl=ilvl
        ))
    return results