# Цель

С одного входного файла (DOCX) получать:

* Папку `/out/<basename>/chapters/` с файлами Markdown, разрезанными по главам.
* Папку `/out/<basename>/assets/` с изображениями и встроенными медиа.
* `index.md` (оглавление + метаданные + карта глав) и `manifest.json` (машиночитаемая сборка результата).

---

# Ключевые идеи

1. **Docling как универсальный парсер** → единый внутренний формат (структурированное дерево документа + позиции, роли, ссылки на бинарные ресурсы).
2. **Единый «внутренний AST»** → минимизация связки на конкретную версию docling. Маппим docling → `InternalDoc` (наши dataclass’ы), а дальше работаем только с ним.
3. **Правила разбиения по главам** → по уровню заголовков (по умолчанию H1), с настраиваемыми исключениями (предисловие, приложения, титульная и т.п.).
4. **Детерминированные имена файлов** → `NN-title-slug.md` и `assets/img-XXXX.ext` для стабильных ссылок в diff’ах.
5. **Идempoтентность** → одинаковый вход → одинаковый вывод (хеши контента, кэш изображений, одинаковые слуги).

---

# Архитектура (модули)

```
/ core
  ├─ adapters/
  │   ├─ docling_adapter.py        # чтение через docling, извлечение AST и бинарей
  │   └─ mime_guesser.py
  ├─ model/
  │   ├─ internal_doc.py           # AST: Block, Inline, Heading, Paragraph, List, Table, Image, Footnote, etc.
  │   ├─ resource_ref.py
  │   └─ metadata.py               # title, authors, lang, toc entries
  ├─ transforms/
  │   ├─ normalize.py              # нормализация: пробелы, мягкие переносы, слияние разорванных абзацев
  │   ├─ structure_fixes.py        # восстановление нумерации заголовков, уровни, роли разделов
  │   └─ figure_numbering.py       # авто-нумерация рисунков/таблиц (опционально)
  ├─ split/
  │   ├─ chapter_rules.py          # правила: какой уровень → новая глава (по умолчанию level=1)
  │   └─ chapter_splitter.py       # режет InternalDoc на InternalDoc[Chapter]
  ├─ render/
  │   ├─ markdown_renderer.py      # InternalDoc → GFM markdown (+сноски, код, таблицы)
  │   └─ assets_exporter.py        # бинарники → /assets, возвращает маппу id → относительный путь
  ├─ output/
  │   ├─ file_naming.py            # slugify, префиксы NN, расширения
  │   ├─ toc_builder.py            # формирует index.md и manifest.json
  │   └─ writer.py                 # запись на диск, проверка коллизий
  └─ pipeline.py                   # оркестрация этапов

/ cli
  └─ doc2chapmd.py                 # CLI интерфейс

/ tests
  └─ ...
```

> Примечание: можно переиспользовать части вашего текущего проекта (`splitter.py`, `heading_numbering.py`, `preprocess.py`, `validators.py`) — мигрируя их к работе с `InternalDoc`.

---

# Поток данных

1. **Вход**: путь к файлу (`.docx`).
2. **Адаптер** (`docling_adapter`):

   * Определяет mime → вызывает docling.
   * Получает структурированное представление + извлекает бинарные объекты (изображения, вложения).
   * Маппит в `InternalDoc + resources` (без Markdown-специфики).
3. **Трансформации**: `normalize` → `structure_fixes` (правка уровней и нумерации) → опциональные плагины.
4. **Сплиттер**: применяет `chapter_rules` → список `ChapterDoc` (каждая — поддерево с собственными метаданными).
5. **Экспорт ассетов**: сохраняет изображения в `/assets`, возвращает `resource_id → relpath`.
6. **Рендер**: каждый `ChapterDoc` → Markdown (с уже подставленными путями к ассетам).
7. **TOC/манифест**: строит `index.md` и `manifest.json`.
8. **Запись**: все файлы в `/out/<basename>/`.

---

# Правила разбиения по главам

* По умолчанию: **новая глава на `Heading(level==1)`**.
* Настройки:

  * `split.level`: 1|2|3
  * `split.keep_prefix_sections`: \["Титульная", "Аннотация", "Предисловие"] → объединять с первой главой или вынести как `00-frontmatter.md`.
  * `split.appendices_level`: если есть `Приложение` → отдельные файлы `ZZ-appendix-*.md`.
* Алгоритм:

  1. Однопроходно сканируем блоки; при встрече подходящего заголовка — закрываем текущую главу и открываем новую.
  2. Перенумеровываем «NN-» префиксы в финальном списке глав.

---

# Изображения и медиа

* Все бинарные объекты → `/assets/`.
* Имена: `img-0001.png`, `table-0003.png`, `eq-0002.svg` (если docling отдаёт формулы картинками), расширение по исходным данным.
* Внутренние ссылки обновляются на относительные: `![caption](../assets/img-0001.png)`.
* Дедубликация: по SHA256 содержимого; повторно не копируем, ссылку даём на существующий файл.

---

# Сноски, ссылки, перекрёстные ссылки

* Сноски рендерим в GFM `[^id]` с блоком внизу главы.
* Внутренние «ссылка на рисунок X» → плоский текст, либо (опционально) метки с автоссылками, если целевые узлы в той же главе.
* Межглавные ссылки: через `index.md` (TOC) и якоря в названиях, но по умолчанию безопаснее оставить текст без кликабельности (или сделать относительные пути на `NN-title.md#anchor`).

---

# Конфигурация (config.yaml)

```yaml
split:
  level: 1           # 1 → главы по H1
  frontmatter:       # что считать передними материями
    enabled: true
    titles:
      - Аннотация
      - Предисловие
render:
  markdown:
    gfm: true
    wrap: 100
    code_block_style: fenced
assets:
  folder: assets
  prefix: img-
  dedupe: sha256
naming:
  chapter_pattern: "{index:02d}-{slug}.md"
  slug_maxlen: 60
locale: ru
```

---

# CLI

```bash
# базовый прогон
$ doc2chapmd input.docx -o out/

# явный уровень разбиения
$ doc2chapmd input.docx -o out/ --split-level 2

# без frontmatter
$ doc2chapmd input.docx -o out/ --no-frontmatter
```

Опции:

* `--split-level {1,2,3}`
* `--assets-dir assets`
* `--chapter-pattern "{index:02d}-{slug}.md"`
* `--locale ru` / `en`
* `--keep-toc` (включать сгенерированное `index.md`)

---

# Псевдокод оркестрации

```python
from core.adapters.docling_adapter import parse_with_docling
from core.transforms import normalize, structure_fixes
from core.split.chapter_splitter import split_into_chapters
from core.render.assets_exporter import export_assets
from core.render.markdown_renderer import render_markdown
from core.output import toc_builder, writer

internal_doc, resources = parse_with_docling(path)
internal_doc = normalize.run(internal_doc)
internal_doc = structure_fixes.run(internal_doc)
chapters = split_into_chapters(internal_doc, level=cfg.split.level)
asset_map = export_assets(resources, out_assets_dir)

outputs = []
for i, ch in enumerate(chapters, start=1):
    md = render_markdown(ch, asset_map)
    relpath = writer.write_chapter(md, i, ch.title)
    outputs.append({"index": i, "title": ch.title, "path": relpath})

index_md = toc_builder.build_index(outputs, meta=internal_doc.meta)
manifest = toc_builder.build_manifest(outputs, asset_map, meta=internal_doc.meta)
writer.write_aux(index_md, manifest)
```

---

# Интеграция с текущим проектом

* **`heading_numbering.py`** → перенести логику в `transforms/structure_fixes.py` (работать на AST, не на HTML).
* **`splitter.py`** → станет `chapter_splitter.py`, источник заголовков — узлы AST.
* **`preprocess.py`** → часть логики переедет в `normalize.py` (мягкие переносы, пробелы, cleanup).
* **`validators.py`** → верификация структуры (есть ли хотя бы один заголовок H1, нет ли пустых глав, дубликатов slug’ов).
* **`mammoth_style_map.map`** больше не нужен (docling берёт на себя парсинг).

---

# Качество и регрессия

* Набор эталонных входов (`/samples`) и снапшоты вывода (`/snapshots`).
* Golden-тесты: сравнение `manifest.json` и структуры каталогов.
* Логи: на каждом этапе фиксируем размеры, число блоков, кол-во изображений, обнаруженные аномалии.

---

# Расширяемость (плагины)

* Хуки: `after_parse`, `before_split`, `after_split`, `before_render`, `after_render`.
* Плагины могут модифицировать AST (например, объединять оторванные заголовки).

---

# Риск‑зоны и решения

* **Сломанные списки/таблицы** → нормализаторы.
* **Формулы** → если docling отдаёт MathML/LaTeX — рендерить в `$...$`, иначе — как изображения с alt-текстом.
* **Межглавные перекрёстные ссылки** → минимально поддержать, не ломать текст; улучшать итеративно.

---

# Вывод

Архитектура изолирует docling на уровне адаптера и обеспечивает стабильный, детерминированный вывод: чистые Markdown‑главы и аккуратная папка ассетов. Следующий шаг — зафиксировать формат `InternalDoc` и поднять минимальный рабочий прототип (DOCX → 2–3 главы с картинками).
