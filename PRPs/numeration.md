
# Implementation Guide (Scoped): Preserve DOCX Heading Numbering in Markdown

## Goal (scoped)

Извлечь «видимую» нумерацию заголовков из **DOCX XML** (`document.xml`, `numbering.xml`, `styles.xml`) и гарантированно проставить её:

1. в тексте всех H1–H6 заголовков финальных `.md`,
2. в префиксах имён файлов глав (по H1).
   Других изменений пайплайна не требуется. Речь только о нумерации.&#x20;

## Deliverables

* Модуль XML-парсинга нумерации: `heading_numbering.py` (или обновить существующий одноимённый файл).
* Утилита для вживления номеров в Markdown: `md_numbering.py`.
* Точечные вызовы:

  * в месте, где формируется markdown (после конвертации из DOCX) — применить нумерацию к заголовкам,
  * в сплиттере — использовать номер из H1 для имени файла.
* Юнит- и интеграционные тесты только на кейсы с нумерацией.

## Integration points (минимальные правки)

* **`heading_numbering.py`** — реализовать `extract_headings_with_numbers(docx_path) -> List[NumberedHeading]`.
* **`preprocess.py`** (или ваш шаг DOCX→MD): после генерации `md_text` вызвать `apply_numbers_to_markdown(md_text, numbered_headings)`.
* **`splitter.py`**: при именовании файла главы брать первый компонент `heading_number` из H1.
* **`validators.py`**: добавить валидации нумерации (монотонность, отсутствие «дыр» и согласованность уровней).
  Такая точка встраивания соответствует модели из ваших документах, но мы сознательно ограничиваемся задачей нумерации.&#x20;

---

## Data model

```python
# types used across modules
from dataclasses import dataclass
from typing import Optional

@dataclass
class NumberedHeading:
    level: int          # 1..6
    text: str           # plain visible text (no number)
    number: str         # formatted visible number: "1", "1.2", "IV", "A.1" etc.
    anchor: str         # kebab-case slug from text
    num_id: Optional[int] = None  # w:numId if present
    ilvl: Optional[int] = None    # w:ilvl if present
```

---

## 1) XML-парсинг нумерации (новый/обновлённый `heading_numbering.py`)

Реализуй полный разбор `numbering.xml` (`abstractNum/lvl`: `start`, `numFmt`, `lvlText`, `lvlRestart`), сопоставление `styles.xml` → уровень заголовка (по `w:outlineLvl` и/или имени «Heading 1 / Заголовок 1»), и проход по `document.xml`: для каждого `w:p` с заголовочным стилем вычисляй видимый номер по `w:numPr` (`numId`/`ilvl`); если `numPr` отсутствует — применяй fallback «1.1.1» по уровню заголовка. Код ниже self-contained:

```python
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
        numbering = z.read("word/numbering.xml")
        styles = z.read("word/styles.xml")
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
```

---

## 2) Применить номера к Markdown (новый `md_numbering.py`)

Последовательно проходит по строкам MD; каждый раз, когда встречает `^#{1,6}\s+...`, подставляет **следующий** номер из списка заголовков. Это даёт устойчивое сопоставление «по порядку документа», не требуя сложных эвристик на «совпадение текста».

```python
# md_numbering.py
import re
from typing import Iterable
from heading_numbering import NumberedHeading

HEADING_RE = re.compile(r'^(#{1,6})\s+(.*\S)\s*$')

def apply_numbers_to_markdown(md_text: str, numbered: Iterable[NumberedHeading]) -> str:
    """
    Walk through MD lines; for each heading line, prefix with the next heading.number.
    If line already begins with a number like '1.2 ' — replace it (avoid double numbering).
    """
    it = iter(numbered)
    out_lines = []
    for line in md_text.splitlines():
        m = HEADING_RE.match(line)
        if not m:
            out_lines.append(line)
            continue
        hashes, title = m.group(1), m.group(2)

        # Strip any existing leading number (e.g., '1.2.3 ' / 'IV ' / 'A.1 ')
        title_clean = re.sub(r'^[\dIVXLCDM]+(?:[\.\-]\d+)*\s+', '', title, flags=re.IGNORECASE)

        try:
            h = next(it)
        except StopIteration:
            # No more headings from DOCX — keep as-is
            out_lines.append(f"{hashes} {title_clean}")
            continue

        out_lines.append(f"{hashes} {h.number} {title_clean}")
    return "\n".join(out_lines) + "\n"
```

> Если в пайплайне есть AST-рендерер, вместо текстовой замены просто положи `heading_number` в узел и рендерь `f"{h.heading_number} {h.text}"`. Мы оставляем текстовую реализацию, чтобы не трогать остальной проект: минимум инвазивных правок.&#x20;

---

## 3) Точки встраивания

### A) Там, где собирается Markdown (например, `preprocess.py`)

1. На входе есть исходный `.docx` и уже полученный `md_text` (после mammoth/pandoc/другого конвертера).
2. В самом конце шага (перед записью файла):

```python
from heading_numbering import extract_headings_with_numbers
from md_numbering import apply_numbers_to_markdown

def convert_docx_to_md_with_numbering(docx_path: str) -> str:
    md_text = convert_docx_to_md(docx_path)  # ваша существующая функция
    heads = extract_headings_with_numbers(docx_path)
    md_text = apply_numbers_to_markdown(md_text, heads)
    return md_text
```

### B) В `splitter.py` (имена файлов глав)

При разрезании по H1 возьми **первый компонент** номера как целочисленный индекс:

```python
import re

def chapter_index_from_h1(heading_line: str) -> int:
    # heading_line: "# 3 Технические требования"
    m = re.match(r'^#{1,6}\s+([^\s]+)\s+.*$', heading_line.strip())
    if not m:
        return 1
    num = m.group(1)  # e.g., "3" or "3.1"
    first = re.split(r'[.\-]', num)[0]
    try:
        return int(first)
    except ValueError:
        return 1

def filename_for_chapter(h1_line: str, slug: str) -> str:
    idx = chapter_index_from_h1(h1_line)
    return f"{idx:02d}-{slug}.md"
```

---

## 4) Validators (минимум)

Добавь проверки в `validators.py`:

* **Монотонность H1**: индексы H1 должны возрастать на 1.
* **Согласованность уровней**: после H2 нельзя сразу перейти к H4 (нельзя «перепрыгивать»).
* **Запрет двойной нумерации**: проверять, что после применения `apply_numbers_to_markdown` нет повторов вроде `1 1 Введение`.

Псевдокод:

```python
def validate_numbering(md_text: str) -> None:
    # 1) ensure H1 numbers are 1..N without gaps
    # 2) ensure levels increase/decrease корректно (±1 по иерархии)
    # 3) ensure each heading starts with number token
    ...
```

---

## 5) Tests (обязательные)

Юнит-тесты:

* **unit\_xml\_decimal**: DOCX с decimal; ожидаем «1», «1.1», «1.2», «2», …
* **unit\_mixed\_formats**: upperRoman / lowerLetter — корректный формат компонентов.
* **unit\_fallback**: DOCX без `numPr` — «1.1.1» по уровням.
* **unit\_md\_apply**: `apply_numbers_to_markdown` корректно подставляет/замещает начальные числа.

Интеграция (минимум):

* Прогон конвертера на одном образце `.docx`; проверка:
  a) Все H1–H6 начинаются с цифробуквенного номерного токена;
  b) Имена файлов глав имеют префикс `NN-`;
  c) Никаких «двойных» префиксов.


---

## 6) Edge cases

* `lvlText` c пунктуацией («%1.%2.») — после подстановки делай `strip()` и `rstrip('.')`.
* `start` по умолчанию = 1; `lvlRestart` можно игнорировать на первом проходе (при необходимости — сбрасывай счётчики при повышении уровня).
* Поддержка кириллицы в slug (сохранить буквы, пробелы → `-`).
* Если после конвертера какой-то заголовок исчез — номер просто не будет потреблён; функция `apply_numbers_to_markdown` не упадёт.

---

## 7) Acceptance Criteria (Definition of Done — только для нумерации)

* Каждый заголовок H1–H6 в итоговых `.md` начинается с видимого номера, совпадающего с исходным DOCX.
* Имена файлов глав начинаются с `NN-`, где `NN` — первый компонент номера H1.
* Валидаторы проходят без ошибок.
* Тесты для decimal/roman/letter/fallback зелёные.
* Не изменены нерелевантные части пайплайна (минимум инвазивности, только точки интеграции).&#x20;

---

## 8) Hand-off checklist (для LLM-исполнителя)

1. Вставь `heading_numbering.py` (код выше) и `md_numbering.py`.
2. Подключи `extract_headings_with_numbers` + `apply_numbers_to_markdown` в месте, где у тебя уже есть `md_text` из DOCX.
3. Обнови именование глав в `splitter.py` для префикса `NN-`.
4. Добавь быстрые валидаторы и тесты.
5. Прогон на `dev-portal-admin.docx` / `cu-admin-install.docx` и сравнение с эталонными MD, где номера сохранены.

Если при вживлении номеров встречаются коллизии (заголовки сильно изменены после конвертера), временно используй строго **последовательное сопоставление по порядку**, как в `apply_numbers_to_markdown` — это даёт предсказуемый и стабильный результат.

если нумерацию восстановить не удается, используй первый markdown файл после конвертации, в нем содержатся все номера заголовков вместе с названиями заголовков