import logging
from pathlib import Path

import typer
from rich.console import Console
from rich.progress import Progress

from . import navigation, preprocess, splitter, validators
from .config import DEFAULT_MODEL, DEFAULT_PROVIDER, OPENROUTER_DEFAULT_MODEL, MISTRAL_DEFAULT_MODEL
from .llm_client import ClientFactory

# NEW: Docling adapter (optional)
try:
    from . import preprocess_docling
except Exception:
    preprocess_docling = None  # Docling is optional

logging.basicConfig(level=logging.INFO)

app = typer.Typer(help="Convert DOCX/PDF documentation to Markdown.")
console = Console()


def get_default_model_for_provider(provider: str) -> str:
    if provider.lower() == "mistral":
        return MISTRAL_DEFAULT_MODEL
    else:
        return OPENROUTER_DEFAULT_MODEL


@app.callback()
def main() -> None:
    pass


@app.command()
def run(
    docx_path: str = typer.Argument(..., help="Путь к входному DOCX/PDF файлу."),
    output_dir: str = typer.Option("output", "--out", "-o", help="Директория для сохранения Markdown файлов."),
    style_map: Path = typer.Option(
        Path(__file__).with_name("mammoth_style_map.map"),
        help="Путь к файлу style-map для Mammoth (используется в режиме engine=mammoth).",
    ),
    rules_path: Path = typer.Option(
        Path(__file__).resolve().parents[2] / "formatting_rules.md",
        help="Путь к правилам форматирования.",
    ),
    samples_dir: Path = typer.Option(
        Path(__file__).resolve().parents[2] / "samples",
        help="Каталог с примерами форматирования.",
    ),
    model: str = typer.Option(DEFAULT_MODEL, "--model", help="Имя модели для форматирования."),
    provider: str = typer.Option(DEFAULT_PROVIDER, "--provider", help="API провайдер (openrouter или mistral)."),
    dry_run: bool = typer.Option(False, "--dry-run/--no-dry-run", help="Запуск без обращения к LLM."),
    engine: str = typer.Option(
        None, "--engine", help="preprocess движок: 'docling' или 'mammoth'. По умолчанию: docling для PDF, mammoth для DOCX."
    ),
) -> None:
    """Run the conversion pipeline with a selectable preprocessing engine (mammoth|docling)."""
    logging.getLogger(__name__).info("Running the pipeline")
    console.print(f"[bold green]Запуск конвертации для файла:[/] {docx_path}")
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Choose engine
    suffix = Path(docx_path).suffix.lower()
    if engine is None:
        engine = "docling" if suffix == ".pdf" else "mammoth"
    engine = engine.lower()
    if engine not in {"mammoth", "docling"}:
        raise typer.BadParameter("engine must be either 'mammoth' or 'docling'")

    images_dir = output_path / "images"

    if engine == "docling":
        if preprocess_docling is None:
            raise typer.BadParameter("Docling engine selected, but preprocess_docling could not be imported. Install docling and ensure module is available.")
        images = preprocess_docling.extract_images_with_docling(docx_path, str(images_dir))
        html = preprocess_docling.convert_doc_to_html(docx_path)
    else:
        # mammoth (existing)
        preprocess.extract_images(docx_path, str(images_dir))
        html = preprocess.convert_docx_to_html(docx_path, str(style_map))
        html = preprocess.remove_table_of_contents(html)

    chapters = splitter.split_html_by_h1(html)

    # Temporary fix from your original CLI: only send the 4th chapter to the model, else none
    if len(chapters) >= 4:
        chapters = [chapters[3]]
    else:
        chapters = []

    # Deterministic path without calling LLM
    if no_llm:
        from slugify import slugify
        doc_slug = slugify(Path(docx_path).stem)
        # Generate basic filenames N.slug.md
        if not chapters:
            chapters = [html]
        for idx, chapter_html in enumerate(chapters, start=1):
            # Simple title from first H1 in fragment
            import re
            m = re.search(r"<h1[^>]*>(.*?)</h1>", chapter_html, re.IGNORECASE | re.DOTALL)
            title = m.group(1).strip() if m else f"Глава {idx}"
            slug = slugify(title) or f"chapter-{idx}"
            md = html2md_rules.html_to_markdown(chapter_html, idx, title, slug)
            filename = f"{idx}.{slug}.md"
            (output_path / filename).write_text(md, encoding="utf-8")
        navigation.inject_navigation_and_create_toc(str(output_path))
        console.print(f"[bold green]Готово без LLM. Результаты в:[/] {output_dir}")
        return

    if dry_run:
        temp_dir = output_path / "html"
        temp_dir.mkdir(parents=True, exist_ok=True)
        if chapters:
            for idx, chapter in enumerate(chapters, start=1):
                (temp_dir / f"chapter_{idx}.html").write_text(chapter, encoding="utf-8")
            console.print(f"[yellow]Dry run completed. {len(chapters)} HTML chapters saved to {temp_dir}.[/]")
        else:
            (temp_dir / "full_document.html").write_text(html, encoding="utf-8")
            console.print(f"[yellow]Dry run completed. No H1 tags found, full HTML saved as full_document.html in {temp_dir}.[/]")
        return

    doc_slug = slugify(Path(docx_path).stem)
    from . import prompt_builder  # late import to avoid overhead before dry-run
    builder = prompt_builder.PromptBuilder(rules_path, samples_dir)

    if model == DEFAULT_MODEL:
        model = get_default_model_for_provider(provider)

    client = ClientFactory.create_client(provider, builder, model=model)

    with Progress() as progress:
        task = progress.add_task("Formatting chapters", total=len(chapters))
        for idx, chapter in enumerate(chapters, start=1):
            manifest, md = client.format_chapter(chapter)
            from . import postprocess  # late import
            processed = postprocess.PostProcessor(md, idx, doc_slug).run()
            warnings = validators.run_all_validators(processed)
            for w in warnings:
                logging.warning(w)
            file_path = output_path / manifest["filename"]
            file_path.write_text(processed, encoding="utf-8")
            progress.advance(task)

    navigation.inject_navigation_and_create_toc(str(output_path))
    console.print(f"[bold green]Конвертация завершена. Результаты в:[/] {output_dir}")
