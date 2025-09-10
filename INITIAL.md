## FEATURE:

- A command-line tool to convert DOCX documents into a structured set of Markdown files.
- The core of the tool is a pipeline architecture that uses a universal parser to create an intermediate Abstract Syntax Tree (AST) called `InternalDoc`.
- This decouples the parsing logic from the output generation, making the process robust, testable, and extensible.
- The pipeline processes the `InternalDoc` through several stages:
  1.  **Adapter:** Parses the source file into the `InternalDoc` AST.
  2.  **Transforms:** Normalizes content and fixes structural issues.
  3.  **Splitting:** Splits the document into chapters.
  4.  **Asset Exporting:** Extracts and saves binary assets like images.
  5.  **Rendering:** Renders the `InternalDoc` for each chapter into Markdown.
  6.  **Output Generation:** Writes Markdown files, an `index.md` table of contents, and a `manifest.json`.

## EXAMPLES:

The `samples/` folder contains examples of the expected output structure. These demonstrate how a source document is broken down into individual Markdown files for chapters.

- `samples/admin/`
- `samples/user/`

Use these as a reference for the target output format.

## DOCUMENTATION:

Internal project documentation provides the necessary context for development:

- `GEMINI.md`, `AGENTS.md`: Contains a high-level overview of the project, its core technologies (Python, Pydantic, Typer, Pytest), and the Test-Driven Development (TDD) approach.
- `architecture.md`: Provides a detailed breakdown of the target architecture, data flow, module responsibilities, and design decisions.

## OTHER CONSIDERATIONS:

- The new architecture is being implemented within the `core/` directory.
- The project follows a TDD approach; tests are crucial and should be developed alongside features.
- Existing scripts (`splitter.py`, `preprocess.py`, etc.) are being deprecated and their logic migrated into the new `core/` modules to work with the `InternalDoc` AST.
- The old `cli.py` is deprecated and will be replaced by a new CLI entry point, `doc2chapmd.py`.
- The system is designed to be idempotent, meaning the same input should always produce the same output.