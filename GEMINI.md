# Project Overview

This project, "docling", is a command-line tool designed to convert DOCX documents into a structured set of Markdown files, complete with chapters and extracted assets. The core principle of the new architecture is to use a universal parser (`docling`) to create a structured Abstract Syntax Tree (AST), referred to as `InternalDoc`. This intermediate representation decouples the parsing logic from the output generation, making the pipeline more robust, testable, and extensible.

The project follows a Test-Driven Development (TDD) approach.

## Core Technologies

*   **Python:** The primary programming language.
*   **Pydantic:** Used for defining the strongly-typed `InternalDoc` AST models.
*   **Typer:** Used for creating the command-line interface.
*   **Pytest:** The testing framework.

## Target Architecture (`architecture.md`)

The conversion process is designed as a multi-stage pipeline that operates on the `InternalDoc` AST.

1.  **Adapter (`docling_adapter`):** The input file (DOCX) is parsed by an external engine (like `docling`). The output is then mapped into our internal `InternalDoc` models and a list of binary `ResourceRef` objects (e.g., images). This is the only layer that interacts with the parser, isolating the rest of the system from it.
2.  **Transforms:** A series of transformations can be applied to the `InternalDoc` AST to normalize content, fix structural issues (e.g., heading levels), or add numbering.
3.  **Splitting (`chapter_splitter`):** The single `InternalDoc` is split into multiple `InternalDoc` objects, each representing a chapter, based on configurable rules (e.g., split on H1 headings).
4.  **Asset Exporting (`assets_exporter`):** Binary resources are saved to an output directory. This process handles deduplication by checking content hashes (SHA256). It returns a map of resource IDs to their new relative paths.
5.  **Rendering (`markdown_renderer`):** Each chapter's `InternalDoc` is traversed, and a Markdown string is generated. The asset map from the previous step is used to insert correct image paths.
6.  **Output Generation:** The final Markdown files are written to disk, along with an `index.md` table of contents and a machine-readable `manifest.json`.

## Project Structure

The new architecture is being built inside the `core/` directory, with a clear separation of concerns:

*   `core/model/`: Defines the `InternalDoc`, `ResourceRef`, and `Metadata` Pydantic models.
*   `core/adapters/`: Handles parsing source files and mapping them to the `InternalDoc` AST.
*   `core/render/`: Contains logic for rendering the AST to Markdown and exporting assets.
*   `core/split/`: Logic for splitting the document into chapters.
*   `core/transforms/`: Modules for modifying the AST.
*   `core/output/`: Handles file writing and TOC generation.
*   `tests/`: Contains all unit and integration tests.

## Building and Running

The project uses a virtual environment and manages dependencies via `requirements.txt`.

### Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Testing

Tests are run using `pytest`:

```bash
pytest
```

### Running the (future) tool

A new CLI (`doc2chapmd.py`) will be created to orchestrate the pipeline. The old `cli.py` is considered deprecated and will be removed.

```bash
# Example of the target command
python -m doc2chapmd input.docx -o out/
```