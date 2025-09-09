# Project Overview

This project is a command-line tool named "docling" for converting DOCX and PDF documents into a structured set of Markdown files. It is designed to handle complex documents by splitting them into chapters, processing images, and applying consistent formatting.

The tool offers two main conversion pipelines:

1.  **Deterministic Conversion:** A fast, rule-based approach that converts HTML to Markdown using predefined rules. This is suitable for well-structured documents where predictability is important.
2.  **LLM-based Formatting:** An advanced approach that uses a Large Language Model (LLM) to format the content, which can handle more nuanced and complex formatting requirements.

## Core Technologies

*   **Python:** The primary programming language.
*   **Typer:** Used for creating the command-line interface.
*   **Mammoth:** Used for converting DOCX files to HTML.
*   **Pandoc:** Used for extracting images from DOCX files.
*   **Docling:** An optional engine for PDF and DOCX conversion.
*   **Beautiful Soup (`bs4`):** For parsing and manipulating HTML.
*   **LLM Integration:** The tool can connect to LLM providers like OpenRouter or Mistral for advanced content formatting.

## Architecture

The conversion process follows these main steps:

1.  **Preprocessing:** The input DOCX or PDF is converted into HTML. Images are extracted and saved separately. The Table of Contents is removed from the HTML.
2.  **Splitting:** The HTML is split into chapters based on `<h1>` tags.
3.  **Formatting:** Each chapter is processed. This can be done either through the deterministic `html2md_rules.py` converter or by sending the content to an LLM with a specific prompt for formatting.
4.  **Post-processing:** After formatting, additional processing is applied to clean up the Markdown and ensure consistency.
5.  **Validation:** Validators are run to check for common formatting errors.
6.  **Navigation:** A table of contents and navigation links are generated for the final set of Markdown files.

# Building and Running

## Prerequisites

*   Python 3.x
*   Pandoc

## Installation

It is recommended to install the dependencies in a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
# It is not clear which dependency manager is used, so a requirements.txt may need to be generated.
# pip install -r requirements.txt 
```

## Running the tool

The main entry point is `cli.py`. You can run the tool using `typer`:

```bash
python -m cli run [DOCX_PATH] [OPTIONS]
```

### Example

```bash
python -m cli run my_document.docx -o ./output --engine mammoth
```

### Key Options

*   `--out` or `-o`: Specify the output directory for the Markdown files.
*   `--engine`: Choose the preprocessing engine (`mammoth` or `docling`). Defaults to `mammoth` for DOCX and `docling` for PDF.
*   `--model`: Specify the LLM model to use for formatting.
*   `--provider`: Specify the LLM provider (`openrouter` or `mistral`).
*   `--dry-run`: Run the pipeline without calling the LLM, saving intermediate HTML files instead.

# Development Conventions

*   **CLI:** The command-line interface is built using `typer`.
*   **Modular Structure:** The codebase is organized into modules with specific responsibilities (e.g., `preprocess`, `splitter`, `validators`).
*   **LLM Integration:** The `llm_client.py` module provides a factory for creating clients for different LLM providers.
*   **Configuration:** Configuration for LLM models and providers is managed in the `config.py` file.
*   **Formatting Rules:** The `formatting_rules.md` file defines the rules for the LLM-based formatting.
