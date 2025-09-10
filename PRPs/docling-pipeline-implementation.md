name: "Docling Document Processing Pipeline Implementation"
description: |
  Complete implementation of a document conversion tool that transforms DOCX files 
  into structured Markdown chapters with assets, using docling library and pipeline architecture.

---

## Goal
Implement a complete, working document conversion pipeline that:
- Takes DOCX input files and converts them to structured Markdown chapters
- Uses docling library for universal document parsing 
- Extracts and manages binary assets (images, etc.)
- Generates table of contents and manifest files
- Provides a CLI interface for end-to-end document processing
- Follows the established pipeline architecture with AST-based transformations

## Why
- **User Value**: Enables conversion of complex documents into readable, structured Markdown format
- **AI Integration**: Prepares documents for AI/RAG workflows by creating consistent structure
- **Scalability**: Pipeline architecture allows easy addition of new transforms and output formats
- **Maintainability**: Clean separation between parsing, transformation, and rendering layers

## What
A complete document processing pipeline with:
- CLI tool (`doc2chapmd.py`) for document conversion
- Pipeline orchestrator integrating all processing stages
- Real docling integration (replacing mock implementation)
- Output generation with deterministic file naming
- Configuration system supporting YAML configs
- Comprehensive test coverage

### Success Criteria
- [ ] CLI processes DOCX files and generates chapter markdown files
- [ ] Images and assets are extracted and properly referenced
- [ ] Generated `index.md` provides complete table of contents
- [ ] Generated `manifest.json` contains machine-readable document metadata
- [ ] All tests pass with >90% coverage
- [ ] Tool handles edge cases gracefully (missing images, malformed docs)
- [ ] Generated output matches expected sample format

## All Needed Context

### Documentation & References
```yaml
# MUST READ - Include these in your context window
- url: https://github.com/docling-project/docling
  why: Official docling library documentation and API patterns
  
- url: https://pypi.org/project/docling/
  why: Installation and basic usage examples
  
- file: /home/spec/work/rosa/docling/core/model/internal_doc.py
  why: Existing AST model structure to maintain compatibility
  
- file: /home/spec/work/rosa/docling/core/adapters/docling_adapter.py
  why: Current mock implementation that needs real docling integration
  
- file: /home/spec/work/rosa/docling/architecture.md
  why: Complete pipeline architecture and module responsibilities
  
- file: /home/spec/work/rosa/docling/GEMINI.md
  why: Core technologies and development approach (TDD, Python, Pydantic, Typer)
  
- file: /home/spec/work/rosa/docling/samples/user/0.index.md
  why: Expected output format for table of contents with frontmatter
  
- file: /home/spec/work/rosa/docling/samples/user/1.common (3).md
  why: Expected chapter format with markdown structure
```

### Current Codebase Tree (UPDATED)
```bash
/home/spec/work/rosa/docling/
├── core/
│   ├── adapters/
│   │   ├── docling_adapter.py        # ✅ Real docling integration
│   │   └── docx_parser.py            # ✅ Specialized DOCX parser with numbering
│   ├── model/
│   │   ├── config.py                 # ✅ Configuration models
│   │   ├── internal_doc.py           # ✅ Complete AST models
│   │   ├── metadata.py               # ✅ Document metadata
│   │   └── resource_ref.py           # ✅ Binary resource handling
│   ├── transforms/
│   │   ├── normalize.py              # ✅ Content normalization
│   │   └── structure_fixes.py        # ✅ Structure fixes
│   ├── split/
│   │   └── chapter_splitter.py       # ✅ Chapter splitting logic
│   ├── render/
│   │   ├── markdown_renderer.py      # ✅ AST to Markdown rendering
│   │   └── assets_exporter.py        # ✅ Asset extraction and saving
│   ├── output/
│   │   ├── file_naming.py            # ✅ Deterministic file naming
│   │   ├── toc_builder.py            # ✅ TOC and manifest generation
│   │   └── writer.py                 # ✅ File writing operations
│   ├── numbering/
│   │   ├── auto_numberer.py          # ✅ Automatic heading numbering
│   │   └── __init__.py               # ✅ Package init
│   └── pipeline.py                   # ✅ Pipeline orchestrator
├── tests/
│   ├── test_adapter.py               # ✅ Adapter tests
│   ├── test_integration.py           # ✅ End-to-end integration tests
│   ├── test_model.py                 # ✅ Model tests
│   ├── test_render.py                # ✅ Rendering tests
│   ├── test_splitter.py              # ✅ Chapter splitting tests
│   └── test_toc_builder.py           # ✅ TOC builder tests
├── samples/                          # ✅ Expected output examples
├── doc2chapmd.py                     # ✅ CLI entry point
├── config.yaml                       # ✅ Default configuration
└── requirements.txt                  # ✅ Dependencies defined
```

### Implementation Status Summary
**ALL MAJOR COMPONENTS ARE NOW IMPLEMENTED**
- ✅ Real docling integration (not mock)
- ✅ DOCX parser with numbering preservation
- ✅ Complete pipeline orchestrator
- ✅ File writing operations
- ✅ CLI entry point with typer
- ✅ Configuration system
- ✅ Comprehensive test suite
- ✅ Automatic numbering system

### Known Gotchas & Library Quirks
```python
# CRITICAL: Docling requires specific installation
# pip install docling
# Supports local and remote files (URLs)

# CRITICAL: Docling returns rich document structure
# Use result.document.export_to_markdown() for basic markdown
# Use result.document for structured access to elements

# CRITICAL: Our AST models use discriminated unions
# All models have `type` field with Literal types
# Use isinstance() checks for type narrowing

# CRITICAL: Asset handling requires SHA256 deduplication
# See core/render/assets_exporter.py for existing pattern

# CRITICAL: Tests must use .venv environment
# Run: source .venv/bin/activate && pytest

# CRITICAL: Follow existing pydantic patterns
# All models inherit from BaseModel
# Use Field() for validation and defaults
```

## Implementation Blueprint

### Data Models and Structure
Core AST models are already complete in `core/model/internal_doc.py`. Need to add configuration model:

```python
# Configuration model to add to core/model/
class PipelineConfig(BaseModel):
    split_level: int = 1
    assets_dir: str = "assets"
    chapter_pattern: str = "{index:02d}-{slug}.md"
    frontmatter_enabled: bool = True
    locale: str = "en"
```

### List of Tasks to Complete the PRP (In Order) - STATUS: COMPLETED ✅

```yaml
Task 1: Integrate docx_xml_split for better DOCX chapter extraction ✅ COMPLETED
INTEGRATE docx_xml_split.py:
  - MOVE: docx_xml_split.py to core/adapters/docx_parser.py ✅
  - MODIFY: core/adapters/docling_adapter.py to use DOCX parser for .docx files ✅
  - PRESERVE: Existing docling integration ✅
  - PATTERN: Detect file type and route to appropriate parser ✅
  - BENEFIT: Proper chapter extraction with numbering preservation ✅

Task 2: Create pipeline orchestrator ✅ COMPLETED
CREATE core/pipeline.py:
  - MIRROR: Pseudocode from architecture.md lines 160-182 ✅
  - INTEGRATE: All existing core modules ✅
  - HANDLE: Error propagation and logging ✅
  - RETURN: Structured results with file paths ✅

Task 3: Create output writer module ✅ COMPLETED
CREATE core/output/writer.py:
  - HANDLE: File system operations for chapters ✅
  - IMPLEMENT: Directory creation and cleanup ✅
  - PATTERN: Follow existing file_naming.py conventions ✅
  - ENSURE: Atomic operations and error handling ✅

Task 4: Create CLI entry point ✅ COMPLETED
CREATE doc2chapmd.py:
  - USE: typer for CLI framework (see GEMINI.md) ✅
  - INTEGRATE: core/pipeline.py orchestrator ✅
  - PATTERN: Follow existing CLI patterns if any ✅
  - SUPPORT: All configuration options from architecture.md ✅

Task 5: Add configuration system ✅ COMPLETED
CREATE core/model/config.py:
  - IMPLEMENT: YAML configuration loading ✅
  - USE: pyyaml for parsing (already in requirements) ✅
  - PROVIDE: Default values and validation ✅
  - INTEGRATE: With CLI argument parsing ✅

Task 6: Create comprehensive integration tests ✅ COMPLETED
CREATE tests/test_integration.py:
  - TEST: End-to-end document processing ✅
  - USE: Real sample DOCX files ✅
  - VERIFY: Output matches expected structure ✅
  - PATTERN: Follow existing test patterns in tests/ ✅

Task 7: Update docling adapter tests ✅ COMPLETED
MODIFY tests/test_adapter.py:
  - REPLACE: Mock-based tests with real docling tests ✅
  - ADD: Error handling test cases ✅
  - VERIFY: Resource extraction works correctly ✅
  - MAINTAIN: Existing test structure and patterns ✅

BONUS Task 8: Add automatic numbering system ✅ COMPLETED
CREATE core/numbering/auto_numberer.py:
  - IMPLEMENT: Heading numbering preservation and restoration ✅
  - INTEGRATE: With DOCX parser and chapter splitting ✅
  - ENSURE: Consistent numbering across chapters ✅
```

### Per Task Pseudocode

```python
# Task 1: DOCX-specific Parser Integration
def detect_file_type(file_path: str) -> str:
    # PATTERN: Route to appropriate parser based on file extension
    if file_path.lower().endswith('.docx'):
        return 'docx'
    else:
        return 'unknown'

def parse_with_adapter(file_path: str) -> Tuple[InternalDoc, List[ResourceRef]]:
    # CRITICAL: Use specialized parsers for better results
    file_type = detect_file_type(file_path)
    
    if file_type == 'docx':
        # Use docx_xml_split for proper chapter extraction
        return parse_docx_with_xml_split(file_path)
    else:
        # Use docling for other formats (currently unsupported)
        return parse_with_docling(file_path)

# Task 2: Pipeline Orchestrator  
class DocumentPipeline:
    def __init__(self, config: PipelineConfig):
        self.config = config
    
    def process(self, input_path: str, output_dir: str) -> PipelineResult:
        # PATTERN: Follow exact sequence from architecture.md
        # 1. Parse with docling adapter
        # 2. Apply transforms (normalize, structure_fixes)
        # 3. Split into chapters
        # 4. Export assets  
        # 5. Render markdown for each chapter
        # 6. Generate TOC and manifest
        # 7. Write all files
        
        # CRITICAL: Error handling at each stage
        # Return structured results with file paths

# Task 4: CLI Implementation
import typer
app = typer.Typer()

@app.command()
def convert(
    input_file: str,
    output_dir: str = "out",
    split_level: int = 1,
    assets_dir: str = "assets"
):
    # PATTERN: Load config, create pipeline, process
    # Handle all CLI options from architecture.md
    # Provide progress feedback to user
```

### Integration Points
```yaml
DEPENDENCIES:
  - Add: docling to requirements.txt
  - Ensure: All existing dependencies remain compatible
  
CONFIGURATION:
  - Create: Default config.yaml with all pipeline options
  - Support: CLI argument overrides
  
FILE_STRUCTURE:
  - Output: /out/<basename>/chapters/ for markdown files
  - Output: /out/<basename>/assets/ for images
  - Output: /out/<basename>/index.md for table of contents
  - Output: /out/<basename>/manifest.json for metadata
```

## Validation Loop

### Level 1: Syntax & Style  
```bash
# Run these FIRST - fix any errors before proceeding
source .venv/bin/activate
ruff check --fix .
# mypy .  # Optional since not currently used

# Expected: No errors. If errors exist, READ and fix them.
```

### Level 2: Unit Tests
```python
# UPDATE existing tests and CREATE new ones:

def test_real_docling_parsing():
    """Test actual docling integration works"""
    # Use small test DOCX file
    doc, resources = parse_with_docling("test_files/simple.docx")
    assert len(doc.blocks) > 0
    assert all(isinstance(block, Block) for block in doc.blocks)

def test_pipeline_end_to_end():
    """Test complete pipeline processing"""
    pipeline = DocumentPipeline(PipelineConfig())
    result = pipeline.process("test_files/sample.docx", "/tmp/test_output")
    
    assert result.success is True
    assert len(result.chapter_files) > 0
    assert os.path.exists(result.index_file)
    assert os.path.exists(result.manifest_file)

def test_cli_command():
    """Test CLI interface works correctly"""
    # Use typer testing utilities
    # Verify all command line options work
```

```bash
# Run and iterate until passing:
source .venv/bin/activate
pytest tests/ -v

# If failing: Read error carefully, fix root cause, re-run
# NEVER mock failures - fix the actual implementation
```

### Level 3: Integration Test
```bash
# Test the complete CLI workflow
source .venv/bin/activate

# Test with a real document
python doc2chapmd.py samples/test-document.docx -o /tmp/test_output

# Expected output structure:
# /tmp/test_output/test-document/
# ├── chapters/
# │   ├── 01-introduction.md
# │   ├── 02-main-content.md
# │   └── ...
# ├── assets/
# │   └── img-001.png
# ├── index.md
# └── manifest.json

# Verify: Generated files match samples/ structure
# Check: All images are properly referenced
# Validate: index.md has correct frontmatter and TOC
```

## Final Validation Checklist - STATUS: ✅ ALL COMPLETED
- [✅] All tests pass: `pytest tests/ -v`
- [✅] No linting errors: `ruff check .`
- [✅] CLI processes sample documents successfully
- [✅] Generated output matches samples/ structure
- [✅] Images are extracted and properly referenced
- [✅] TOC generation works correctly
- [✅] Manifest JSON contains expected metadata
- [✅] Error handling works for malformed documents
- [✅] Pipeline is idempotent (same input → same output)
- [✅] BONUS: Automatic numbering preservation and restoration implemented

---

## Anti-Patterns to Avoid
- ❌ Don't break existing AST model compatibility
- ❌ Don't skip TDD - write tests first per CLAUDE.md
- ❌ Don't hardcode file paths - use configuration
- ❌ Don't ignore error cases - handle gracefully
- ❌ Don't create files >500 lines - modularize per CLAUDE.md
- ❌ Don't use sync operations in async contexts
- ❌ Don't skip asset deduplication - use SHA256 hashing

## PRP Quality Score: 10/10 - IMPLEMENTATION COMPLETE ✅
**Confidence Level**: Maximum - All implementation completed successfully with:
- ✅ Complete existing codebase analysis and implementation
- ✅ Real library documentation and working integration  
- ✅ All implementation tasks completed with working patterns
- ✅ All validation loops passed successfully
- ✅ All integration points working and edge cases handled
- ✅ Generated output matches expected structure from samples
- ✅ Bonus features added (automatic numbering system)
- ✅ Comprehensive test coverage with real document processing