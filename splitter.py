"""HTML splitting utilities."""

from __future__ import annotations

import re
import zipfile
from pathlib import Path
from typing import List, Dict, Optional
from xml.etree import ElementTree as ET

from bs4 import BeautifulSoup


def split_html_by_h1(html_content: str) -> List[str]:
    """Split HTML content into fragments by <h1> headings."""
    soup = BeautifulSoup(html_content, "lxml")
    chapters: List[str] = []

    # First try standard H1 tags
    h1_tags = soup.find_all("h1")
    if h1_tags:
        for h1 in h1_tags:
            parts = [str(h1)]
            for sibling in h1.next_siblings:
                if getattr(sibling, "name", None) == "h1":
                    break
                parts.append(str(sibling))
            chapters.append("".join(parts))
        return chapters

    # If no H1 tags found, try to detect chapters by numbered TOC anchors
    return _split_by_toc_anchors(soup)


def _split_by_toc_anchors(soup: BeautifulSoup) -> List[str]:
    """Split HTML by TOC anchor patterns like <a id="_Toc..."></a>."""
    # Find all anchor tags with TOC IDs that appear to be chapter markers
    toc_anchors = soup.find_all("a", id=re.compile(r"_Toc\d+"))

    if not toc_anchors:
        return []

    # Look for chapter markers - either numbered or major section headings
    chapter_markers = []
    for anchor in toc_anchors:
        # Get the text that follows this anchor
        next_text = _get_text_after_anchor(anchor)

        # Check if it starts with a number followed by space or dot (numbered chapters)
        if re.match(r"^\d+[\s\.]+", next_text.strip()):
            chapter_markers.append(anchor)
        # Or check if it's a major section heading (like "Общие сведения", "Веб-интерфейс", etc.)
        elif _is_major_section_heading(next_text.strip()):
            chapter_markers.append(anchor)

    if not chapter_markers:
        return []

    chapters: List[str] = []

    for i, marker in enumerate(chapter_markers):
        # Find the parent element of the marker (usually a <p> tag)
        marker_parent = marker.parent if marker.parent else marker

        chapter_parts = [str(marker_parent)]

        # Find all content until the next chapter marker
        current_element = marker_parent
        next_marker = chapter_markers[i + 1] if i + 1 < len(chapter_markers) else None
        next_marker_parent = (
            next_marker.parent if next_marker and next_marker.parent else next_marker
        )

        # Collect all sibling elements until we hit the next chapter
        while current_element.next_sibling:
            current_element = current_element.next_sibling

            # Skip whitespace-only text nodes
            if isinstance(current_element, str) and not current_element.strip():
                continue

            # Stop if we reached the next chapter marker or its parent
            if next_marker_parent and (
                current_element == next_marker_parent
                or (
                    hasattr(current_element, "find")
                    and current_element.find(lambda tag: tag == next_marker)
                )
            ):
                break

            # Stop collecting content if we've moved too far from the chapter heading
            # This prevents including global footer content in the last chapter
            if not next_marker_parent and _is_likely_global_content(current_element):
                break

            chapter_parts.append(str(current_element))

        if chapter_parts:
            chapters.append("".join(chapter_parts))

    return chapters


def _is_major_section_heading(text: str) -> bool:
    """Check if text looks like a major section heading."""
    # Only recognize specific known major sections to avoid too much splitting
    major_section_patterns = [
        r"^Общие сведения$",
        r"^Установка и настройка",
        r"^Веб-интерфейс",
        r"^Настройка параметров$",
        r"^Управление поставщиками$",
        r"^Управление ресурсами$",
        r"^Контроль$",
        r"^Управление автоматизацией$",
        r"^Мониторинг",  # May have ", отчеты и оповещения" after it
        r"^Тарифы$",
        r"^Службы$",
        r"^Предоставление ВМ$",
        r"^API$",
    ]

    # First clean the text - remove trailing content that might be attached
    clean_text = text.strip()

    # For real document: split on common delimiters that indicate content continuation
    # But be careful not to split on the heading text itself
    for delimiter in [
        "Для доступа",
        "РОСА Менеджер",
        "предназначено",
        "описаны в документе",
    ]:
        if delimiter in clean_text and not clean_text.startswith(delimiter):
            clean_text = clean_text.split(delimiter)[0].strip()

    # Check against our specific patterns
    for pattern in major_section_patterns:
        if re.match(pattern, clean_text, re.IGNORECASE):
            # Additional validation - make sure it's not too long (likely noise)
            if len(clean_text.split()) <= 4:
                return True

    return False


def _is_toc_or_navigation_content(text: str) -> bool:
    """
    Проверяет, является ли текст содержимым оглавления или навигационными элементами.
    
    Такой контент должен быть исключен из глав.
    """
    if not text:
        return False
        
    text_lower = text.lower().strip()
    
    # Проверяем на содержание оглавления
    toc_patterns = [
        'содержание',
        'оглавление', 
        'table of contents',
        'toc',
    ]
    
    # Если текст начинается с паттернов оглавления
    if any(text_lower.startswith(pattern) for pattern in toc_patterns):
        return True
    
    # Проверяем на наличие табуляций с номерами страниц (характерно для TOC)
    if re.search(r'\t+\d+\s*$', text) or re.search(r'\.{3,}\s*\d+\s*$', text):
        return True
    
    # Проверяем на множественные ссылки на разделы подряд
    if text.count('href="#') > 3:  # Много ссылок подряд - скорее всего TOC
        return True
    
    # Проверяем на нумерованные разделы с точками (1.1, 1.2, etc.)
    section_numbers = re.findall(r'\d+\.\d+', text)
    if len(section_numbers) > 2:  # Много номеров разделов
        return True
    
    return False


def _is_likely_global_content(element) -> bool:
    """
    Check if an element is likely to be global document content
    that shouldn't be included in any specific chapter.
    
    This helps prevent global footers, references, or other 
    document-wide content from being included in the last chapter.
    """
    if not hasattr(element, 'get_text'):
        return False
    
    text = element.get_text(strip=True).lower()
    
    # Check for global content patterns
    global_patterns = [
        # Footer-like content
        'все права защищены',
        'copyright',
        '© ',
        'все торговые марки',
        
        # Reference sections
        'список литературы',
        'библиография',
        'источники',
        'references',
        
        # Document metadata
        'версия документа',
        'дата создания',
        'дата изменения',
        'номер версии',
        
        # Contact info
        'техническая поддержка',
        'служба поддержки',
        'обратная связь',
        'контактная информация',
        
        # Legal disclaimers
        'отказ от ответственности',
        'disclaimer',
        'условия использования',
        'пользовательское соглашение'
    ]
    
    # If the text matches global patterns, it's likely global content
    for pattern in global_patterns:
        if pattern in text:
            return True
    
    # Additional heuristics:
    # 1. Very short content at the end might be global
    if len(text) < 20 and any(word in text for word in ['©', 'все права', 'version']):
        return True
    
    # 2. Content that appears to be page numbers or document references
    if len(text.split()) <= 3 and any(char.isdigit() for char in text):
        # Check if it looks like "стр. 15" or "версия 1.0"
        if any(word in text for word in ['стр', 'page', 'версия', 'version']):
            return True
    
    return False


def _get_text_after_anchor(anchor) -> str:
    """Get text content immediately following an anchor tag."""
    text_parts = []
    current = anchor

    # Look through next siblings for text content
    for _ in range(10):  # Limit search to avoid infinite loops
        if current.next_sibling:
            current = current.next_sibling
            if hasattr(current, "get_text"):
                text = current.get_text().strip()
                if text:
                    text_parts.append(text)
                    break
            elif isinstance(current, str) and current.strip():
                text_parts.append(current.strip())
                break

    return " ".join(text_parts) if text_parts else ""


def extract_headings_from_docx(docx_path: str) -> List[Dict]:
    """
    Extract chapter headings directly from DOCX XML structure with level information.

    Returns a list of dictionaries with heading text, level, and style information.
    This provides more reliable chapter detection than HTML parsing.
    """
    try:
        headings = []

        with zipfile.ZipFile(docx_path, "r") as docx:
            # First, analyze styles to get comprehensive heading information
            heading_styles = _analyze_heading_styles(docx)

            # Read the main document
            document_xml = docx.read("word/document.xml")
            root = ET.fromstring(document_xml)

            # Define namespaces for Word XML
            namespaces = {
                "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
            }

            # Find all paragraphs
            paragraphs = root.findall(".//w:p", namespaces)

            for i, para in enumerate(paragraphs):
                heading_info = _extract_heading_from_paragraph(
                    para, heading_styles, namespaces, i
                )
                if heading_info:
                    headings.append(heading_info)

            return headings

    except Exception as e:
        print(f"Warning: Could not extract headings from DOCX: {e}")
        return []


def split_html_using_docx_structure(html_content: str, docx_path: str) -> List[str]:
    """
    Split HTML using heading structure extracted from original DOCX file.
    
    UNIVERSAL VERSION: Preserves original chapter titles and handles all heading levels.
    """
    if not Path(docx_path).exists():
        # Fall back to HTML-only approach
        return split_html_by_h1(html_content)

    # Extract all main chapters from DOCX
    main_chapters_info = extract_main_chapters_from_docx_with_position(docx_path)
    if not main_chapters_info:
        print(
            f"Warning: No main chapters found in {docx_path}, falling back to HTML parsing"
        )
        return split_html_by_h1(html_content)

    main_chapters = [chapter['title'] for chapter in main_chapters_info]
    print(f"Found {len(main_chapters)} main chapters in DOCX: {main_chapters}")

    # Parse HTML
    soup = BeautifulSoup(html_content, "lxml")
    
    # Find heading elements for each chapter
    heading_elements = []
    for chapter_info in main_chapters_info:
        title = chapter_info['title']
        
        # Find the actual heading element in HTML with multiple strategies
        found_element = None
        all_elements = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p'])
        
        # Strategy 1: Exact match
        for elem in all_elements:
            elem_text = elem.get_text(strip=True)
            if elem_text == title:
                # Skip table of contents entries (contain page numbers or tabs)
                if not re.search(r'\t\d+\s*$', elem_text) and 'toc' not in elem.get('class', []):
                    found_element = elem
                    break
        
        # Strategy 2: Partial match for numbered headings
        if not found_element:
            for elem in all_elements:
                elem_text = elem.get_text(strip=True)
                if title in elem_text and len(elem_text) - len(title) < 20:
                    if not re.search(r'\t\d+\s*$', elem_text) and 'toc' not in elem.get('class', []):
                        found_element = elem
                        break
        
        # Strategy 3: Search for text nodes containing the title
        if not found_element:
            pattern = re.compile(re.escape(title), re.IGNORECASE)
            for text_node in soup.find_all(string=pattern):
                parent = text_node.find_parent(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p'])
                if parent:
                    parent_text = parent.get_text(strip=True)
                    # Avoid table of contents
                    if not re.search(r'\t\d+\s*$', parent_text) and len(parent_text.split()) <= 15:
                        found_element = parent
                        break
        
        # Strategy 4: Search for TOC anchors near the title text
        if not found_element:
            # Look for anchors with IDs like _Toc... that might be near our title
            toc_anchors = soup.find_all('a', id=re.compile(r'_Toc\d+'))
            for anchor in toc_anchors:
                # Check text after the anchor
                next_text = anchor.next_sibling
                if isinstance(next_text, str) and title in next_text:
                    parent = anchor.find_parent(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
                    if parent:
                        found_element = parent
                        break
        
        # Strategy 5: Fuzzy search based on keywords from title
        if not found_element:
            title_words = title.lower().split()
            for elem in all_elements:
                elem_text = elem.get_text(strip=True).lower()
                # Check if most title words are present
                matches = sum(1 for word in title_words if word in elem_text)
                if matches >= len(title_words) * 0.7:  # 70% match
                    if not re.search(r'\t\d+\s*$', elem_text) and len(elem_text.split()) <= 15:
                        found_element = elem
                        break
        
        if found_element:
            heading_elements.append((chapter_info, found_element))
            print(f"Found heading for '{title}' in <{found_element.name}>")
        else:
            print(f"Warning: Could not find heading for '{title}' in HTML")
    
    if not heading_elements:
        print("No heading elements found, trying fallback approach")
        # Fallback: use any H1 tags found in HTML
        h1_elements = soup.find_all('h1')
        if h1_elements:
            print(f"Found {len(h1_elements)} H1 elements for fallback")
            for i, h1 in enumerate(h1_elements):
                heading_elements.append(({'title': h1.get_text(strip=True), 'position': i}, h1))
        else:
            return split_html_by_h1(html_content)
    
    # Sort by document order
    def element_position(elem_tuple):
        _, element = elem_tuple
        return list(soup.descendants).index(element)
    
    heading_elements.sort(key=element_position)
    
    # Split content between headings - IMPROVED VERSION
    chapters = []
    for i, (chapter_info, heading_element) in enumerate(heading_elements):
        next_heading_element = heading_elements[i + 1][1] if i + 1 < len(heading_elements) else None
        
        chapter_content = []
        
        # CREATE CONSISTENT H1 HEADING - always use clean original title
        original_title = chapter_info['title']
        chapter_content.append(f"<h1>{original_title}</h1>")
        
        # Collect all content between this heading and the next
        current = heading_element.next_sibling
        collected_elements = set([id(heading_element)])  # Track what we've collected to avoid duplicates
        
        while current:
            # Stop if we reach the next chapter heading
            if next_heading_element and current == next_heading_element:
                break
                
            # Check if we've reached a different main chapter by examining text content
            if next_heading_element and hasattr(current, 'find_all'):
                # Check if current element contains the next chapter heading
                if next_heading_element in current.find_all():
                    break
            
            # Skip whitespace-only text nodes
            if isinstance(current, str) and not current.strip():
                current = current.next_sibling
                continue
            
            # Skip table of contents and other navigational elements
            if hasattr(current, 'find_all'):
                # Check if element contains TOC patterns
                current_text = current.get_text() if hasattr(current, 'get_text') else str(current)
                if _is_toc_or_navigation_content(current_text):
                    current = current.next_sibling
                    continue
            
            # Avoid duplicate elements
            current_id = id(current)
            if current_id not in collected_elements:
                chapter_content.append(str(current))
                collected_elements.add(current_id)
            
            current = current.next_sibling
        
        # Join chapter content
        chapter_html = "".join(chapter_content)
        
        chapters.append(chapter_html)
        
        print(f"Chapter {i + 1} '{chapter_info['title']}' content length: {len(chapter_html)} chars")
    
    return chapters


def _analyze_heading_styles(docx: zipfile.ZipFile) -> Dict[str, Dict]:
    """
    Анализ всех заголовочных стилей в DOCX документе.

    Возвращает словарь со стилями заголовков и их метаданными.
    """
    heading_styles = {}

    try:
        styles_xml = docx.read("word/styles.xml")
        styles_root = ET.fromstring(styles_xml)

        namespaces = {
            "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
        }
        styles = styles_root.findall(".//w:style", namespaces)

        for style in styles:
            style_id = style.get(
                "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}styleId"
            )
            style_type = style.get(
                "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}type"
            )

            if style_id and style_type == "paragraph":
                # Получаем имя стиля
                name_elem = style.find(".//w:name", namespaces)
                name = (
                    name_elem.get(
                        "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val",
                        "",
                    )
                    if name_elem is not None
                    else ""
                )

                # Проверяем outline level (уровень заголовка)
                outline_lvl_elem = style.find(".//w:outlineLvl", namespaces)
                outline_level = (
                    outline_lvl_elem.get(
                        "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val",
                        "",
                    )
                    if outline_lvl_elem is not None
                    else ""
                )

                # Определяем, является ли стиль заголовочным
                is_heading = _is_heading_style(name, outline_level)
                level = _determine_heading_level(name, outline_level)

                if is_heading:
                    heading_styles[style_id] = {
                        "name": name,
                        "level": level,
                        "outline_level": outline_level,
                        "is_main_chapter": _is_main_chapter_style(style_id, name),
                    }

    except Exception as e:
        print(f"Warning: Could not analyze heading styles: {e}")

    return heading_styles


def _is_heading_style(name: str, outline_level: str) -> bool:
    """Определяет, является ли стиль заголовочным."""
    name_lower = name.lower()

    # Проверка по имени стиля
    heading_keywords = ["heading", "заголовок", "rosa_заголовок"]
    if any(keyword in name_lower for keyword in heading_keywords):
        return True

    # Проверка по outline level
    if outline_level and outline_level.isdigit():
        level = int(outline_level)
        return 0 <= level <= 8  # Обычно заголовки имеют outline level 0-8

    return False


def _determine_heading_level(name: str, outline_level: str) -> int:
    """Определяет уровень заголовка."""
    # Сначала пробуем определить по outline level
    if outline_level and outline_level.isdigit():
        return int(outline_level) + 1

    # Затем пробуем извлечь из имени стиля
    level_match = re.search(r"(\d+)", name)
    if level_match:
        return int(level_match.group(1))

    # По умолчанию уровень 1
    return 1


def _is_main_chapter_style(style_id: str, name: str) -> bool:
    """
    Определяет, является ли стиль стилем основных глав документа.

    Основные главы - это заголовки первого уровня, которые должны использоваться
    для разделения документа на отдельные файлы.
    """
    # Для РОСА документов основные главы используют специфические стили
    rosa_main_styles = {
        "ROSA13",  # ROSA_Заголовок 1 - основной стиль для глав
    }
    if style_id in rosa_main_styles:
        return True

    # Стандартные стили заголовков первого уровня
    standard_main_styles = {"13", "1"}  # heading 1, ! Заголовок 1
    if style_id in standard_main_styles:
        return True

    # ИСКЛЮЧАЕМ стили, которые НЕ являются основными главами
    excluded_style_ids = {
        "ROSAf1",   # ROSA_Заголовок_Перечень|Приложение - служебные разделы
        "ROSAff0",  # Служебные заголовки 
        "ROSAb",    # Аннотация, содержание
        "ROSAf9",   # Заголовки таблиц (Google Chrome, Yandex Browser и т.д.)
        "ROSAc",    # Заголовки столбцов таблиц
    }
    if style_id in excluded_style_ids:
        return False

    # Исключаем служебные заголовки по имени
    excluded_patterns = [
        "таблица",
        "table", 
        "аннотация",
        "annotation",
        "содержание",
        "toc",
        "столбец",
        "column",
        "перечень сокращений",  # Конкретно этот раздел
        "список сокращений",
        "сокращение",
        "расшифровка",
    ]

    name_lower = name.lower()
    if any(pattern in name_lower for pattern in excluded_patterns):
        return False

    return False


def _extract_heading_from_paragraph(
    para, heading_styles: Dict, namespaces: Dict, para_index: int
) -> Optional[Dict]:
    """
    Извлекает информацию о заголовке из параграфа, если он является заголовком.
    """
    # Проверяем стиль параграфа
    style_element = para.find(".//w:pStyle", namespaces)
    if style_element is None:
        return None

    style_val = style_element.get(
        "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val"
    )
    if not style_val or style_val not in heading_styles:
        return None

    # Извлекаем текст
    text_elements = para.findall(".//w:t", namespaces)
    text = "".join([t.text or "" for t in text_elements]).strip()

    if not text:
        return None

    style_info = heading_styles[style_val]

    return {
        "text": text,
        "level": style_info["level"],
        "style": style_val,
        "style_name": style_info["name"],
        "outline_level": style_info["outline_level"],
        "is_main_chapter": style_info["is_main_chapter"],
        "paragraph_index": para_index,
    }


def extract_main_chapters_from_docx_with_position(docx_path: str, limit: int = None) -> List[Dict]:
    """
    Извлекает основные главы (первого уровня) из DOCX документа.
    
    Возвращает список словарей с информацией о главах включая их позицию.
    Если limit указан, возвращает только первые N глав.
    """
    try:
        all_headings = extract_headings_from_docx(docx_path)
        
        # Фильтруем только основные главы
        main_chapters = []
        for heading in all_headings:
            if (heading["is_main_chapter"] and 
                heading["level"] == 1 and 
                _is_meaningful_chapter_heading(heading["text"])):
                main_chapters.append({
                    'title': heading["text"],
                    'position': heading["paragraph_index"],
                    'style': heading["style"]
                })
        
        # Сортируем по позиции в документе
        main_chapters.sort(key=lambda x: x['position'])
        
        # Применяем ограничение только если оно задано
        if limit is not None:
            return main_chapters[:limit]
        return main_chapters
        
    except Exception as e:
        print(f"Warning: Could not extract main chapters with position: {e}")
        return []


def extract_all_headings_with_hierarchy(docx_path: str) -> List[Dict]:
    """
    Извлекает ВСЕ заголовки из документа с полной иерархией.
    
    Возвращает список всех заголовков любого уровня с информацией о позиции
    и родительских заголовках. Это поможет обрабатывать глубокую вложенность типа 5.3.1.x.
    """
    try:
        all_headings = extract_headings_from_docx(docx_path)
        
        # Добавляем информацию о родительских заголовках
        headings_with_hierarchy = []
        parent_stack = []  # Стек родительских заголовков
        
        for heading in all_headings:
            level = heading["level"]
            
            # Очищаем стек до текущего уровня
            while parent_stack and parent_stack[-1]["level"] >= level:
                parent_stack.pop()
            
            # Создаем запись с информацией о иерархии
            heading_info = {
                'title': heading["text"],
                'level': level,
                'position': heading["paragraph_index"],
                'style': heading["style"],
                'is_main_chapter': heading["is_main_chapter"],
                'parents': [p["title"] for p in parent_stack],  # Список родительских заголовков
                'parent_positions': [p["position"] for p in parent_stack],
                'full_path': " > ".join([p["title"] for p in parent_stack] + [heading["text"]])
            }
            
            headings_with_hierarchy.append(heading_info)
            
            # Добавляем текущий заголовок в стек родителей
            parent_stack.append({
                "title": heading["text"],
                "level": level,
                "position": heading["paragraph_index"]
            })
        
        return headings_with_hierarchy
        
    except Exception as e:
        print(f"Warning: Could not extract headings with hierarchy: {e}")
        return []


def extract_main_chapters_from_docx(docx_path: str) -> List[str]:
    """
    Извлекает только основные главы (первого уровня) из DOCX документа.

    Возвращает список текстов заголовков основных глав, которые должны
    использоваться для разделения документа на отдельные файлы.
    """
    try:
        all_headings = extract_headings_from_docx(docx_path)

        # Фильтруем только основные главы
        main_chapters = []
        for heading in all_headings:
            if heading["is_main_chapter"] and heading["level"] == 1:
                # Дополнительная фильтрация по содержанию заголовка
                if _is_meaningful_chapter_heading(heading["text"]):
                    main_chapters.append(heading["text"])

        return main_chapters

    except Exception as e:
        print(f"Warning: Could not extract main chapters: {e}")
        return []


def _is_meaningful_chapter_heading(text: str) -> bool:
    """
    Проверяет, является ли заголовок содержательной главой документа.

    Исключает служебные заголовки типа "Содержание", "Аннотация" и т.д.
    """
    text_lower = text.lower().strip()

    # Исключаем служебные разделы
    excluded_headings = {
        "аннотация",
        "содержание",
        "оглавление",
        "перечень сокращений",
        "список сокращений",
        "сокращение",
        "расшифровка",
        "пояснение",
        "список терминов",
        "термины",
        "глоссарий",
    }

    if text_lower in excluded_headings:
        return False

    # Исключаем заголовки таблиц
    if any(
        word in text_lower
        for word in [
            "версия ос",
            "операционная система",
            "процессор",
            "google chrome",
            "yandex browser",
            "mozilla firefox",
            "safari",
            "браузер",
        ]
    ):
        return False

    # Включаем только содержательные главы
    meaningful_patterns = [
        r"^общие сведения",
        r"^начало работы",
        r"^компоненты",
        r"^функции",
        r"^установка",
        r"^настройка",
        r"^управление",
        r"^администрирование",
        r"^использование",
        r"интерфейс",
        r"описание",
        r"руководство",
    ]

    for pattern in meaningful_patterns:
        if re.match(pattern, text_lower):
            return True

    # Если заголовок достаточно длинный (больше одного слова), скорее всего это содержательная глава
    return len(text.split()) > 1
