# Docling Document Processing Pipeline

A powerful document conversion tool that transforms DOCX files into structured Markdown chapters with extracted assets, using the [docling](https://github.com/docling-project/docling) library.

## Features

- 📄 **DOCX Document Support**: Process DOCX files
- 📚 **Chapter-based Splitting**: Automatically split documents by heading levels
- 🖼️ **Asset Extraction**: Extract and organize images and media files
- 🗂️ **Structured Output**: Generate table of contents and machine-readable manifests
- ⚙️ **Configurable Pipeline**: Flexible configuration via YAML files and CLI options
- 🎯 **Deterministic Results**: Same input always produces identical output

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd docling
   ```

2. **Set up virtual environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Quick Start

### Basic Usage

Convert a document to structured Markdown chapters:

```bash
# Activate virtual environment
source .venv/bin/activate

# Convert DOCX file
python doc2chapmd.py convert your-document.docx

# Convert DOCX file with custom output directory
python doc2chapmd.py convert document.docx -o output/

# Verbose output to see processing details
python doc2chapmd.py convert document.docx -o output/ --verbose
```

### Example with Included Sample

```bash
# Test with included sample document
source .venv/bin/activate
python doc2chapmd.py convert docx-s/cu-admin-install.docx -o output_demo --verbose
```

**Expected Output:**
```
✓ Document processed successfully!
Generated files:
  • Table of contents: output_demo/cu-admin-install/index.md
  • Manifest: output_demo/cu-admin-install/manifest.json
  • Chapters: 1 files
  • Assets: 56 files
```

**Output Structure:**
```
output_demo/cu-admin-install/
├── chapters/
│   └── 01-ao-ntts-it-rosa.md     # Chapter files with meaningful names
├── assets/
│   ├── img_001.png               # Extracted images
│   ├── img_002.png
│   └── ...                       # Additional assets
├── index.md                      # Table of contents
└── manifest.json                 # Machine-readable metadata
```

## CLI Commands

### Convert Command

Convert documents with various options:

```bash
# Basic conversion
python doc2chapmd.py convert input.docx

# All available options
python doc2chapmd.py convert input.docx \
  --output custom_output/ \
  --split-level 2 \
  --assets-dir images/ \
  --locale ru \
  --verbose
```

**Options:**
- `--output, -o`: Output directory (default: `out/`)
- `--config, -c`: Path to custom configuration YAML file
- `--split-level, -s`: Heading level for chapter splitting (1-6, default: 1)
- `--assets-dir, -a`: Directory name for assets (default: `assets/`)
- `--locale, -l`: Language/locale for processing (default: `en`)
- `--verbose, -v`: Enable detailed output

### Configuration Commands

```bash
# Show current configuration
python doc2chapmd.py config-show

# Create custom configuration file
python doc2chapmd.py config-create --output my-config.yaml
```

## Configuration

### Default Configuration

The system uses these default settings:

```yaml
# config.yaml
split_level: 1                    # Split on H1 headings
assets_dir: "assets"              # Asset directory name
chapter_pattern: "{index:02d}-{slug}.md"  # Chapter file naming
frontmatter_enabled: true         # Include YAML frontmatter
locale: "en"                      # Processing locale
```

### Custom Configuration

Create a custom configuration file:

```bash
python doc2chapmd.py config-create --output my-config.yaml
```

Then use it:

```bash
python doc2chapmd.py convert document.docx --config my-config.yaml
```

## Advanced Examples

### Different Split Levels

```bash
# Split on H1 headings (default)
python doc2chapmd.py convert document.docx --split-level 1

# Split on H2 headings for finer granularity
python doc2chapmd.py convert document.docx --split-level 2

# Split on H3 headings for maximum granularity
python doc2chapmd.py convert document.docx --split-level 3
```

### Custom Asset Organization

```bash
# Put assets in 'images' folder instead of 'assets'
python doc2chapmd.py convert document.docx --assets-dir images

# Custom output structure
python doc2chapmd.py convert document.docx \
  --output /path/to/output \
  --assets-dir media \
  --split-level 2
```

### Multilingual Documents

```bash
# Process Russian document
python doc2chapmd.py convert russian-doc.docx --locale ru

# Process with custom locale
python doc2chapmd.py convert document.docx --locale de
```

## Output Files

### Chapter Files
- **Location**: `output/<document-name>/chapters/`
- **Format**: `NN-title-slug.md` (e.g., `01-introduction.md`)
- **Content**: Clean Markdown with proper heading structure

### Assets
- **Location**: `output/<document-name>/assets/`
- **Format**: `img_NNN.png/jpg/gif` with SHA256 deduplication
- **References**: Automatically updated in Markdown files

### Index File (`index.md`)
- Table of contents with chapter links
- Document metadata in YAML frontmatter
- Navigation structure

### Manifest File (`manifest.json`)
- Machine-readable document metadata
- Chapter information with titles and paths
- Asset inventory with file details
- Processing configuration used

## Development

### Running Tests

```bash
source .venv/bin/activate
pytest tests/ -v
```

### Code Quality

```bash
# Linting
ruff check .

# Type checking (if configured)
mypy .
```

### Project Structure

```
docling/
├── core/                         # Core processing modules
│   ├── adapters/                 # Document parsers (docling integration)
│   ├── model/                    # Data models and configuration
│   ├── output/                   # File writing and naming
│   ├── render/                   # Markdown rendering and asset export
│   ├── split/                    # Chapter splitting logic
│   ├── transforms/               # Document transformations
│   └── pipeline.py               # Main orchestrator
├── tests/                        # Test suite
├── doc2chapmd.py                 # CLI entry point
├── config.yaml                   # Default configuration
└── requirements.txt              # Dependencies
```

## Troubleshooting

### Common Issues

**"ModuleNotFoundError: No module named 'docling'"**
```bash
# Make sure virtual environment is activated and dependencies installed
source .venv/bin/activate
pip install -r requirements.txt
```

**"No such file or directory"**
```bash
# Use absolute paths or verify file exists
python doc2chapmd.py convert /full/path/to/document.docx
```

**Empty output or no chapters**
```bash
# Try different split levels or check document structure
python doc2chapmd.py convert document.docx --split-level 2 --verbose
```

### Getting Help

```bash
# General help
python doc2chapmd.py --help

# Command-specific help  
python doc2chapmd.py convert --help
python doc2chapmd.py config-show --help
```

## License

This project uses the [docling](https://github.com/docling-project/docling) library for document processing.