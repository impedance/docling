#!/usr/bin/env python3
"""
Document to Chapter Markdown Converter

CLI tool to convert DOCX documents into structured Markdown chapters using docling.
"""

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from core.model.config import load_config, PipelineConfig
from core.pipeline import DocumentPipeline


app = typer.Typer(
    name="doc2chapmd",
    help="Convert DOCX documents to structured Markdown chapters"
)
console = Console()


@app.command()
def convert(
    input_file: Path = typer.Argument(..., help="Path to input DOCX file"),
    output_dir: Path = typer.Option(
        Path("out"), 
        "--output", "-o",
        help="Output directory for generated files"
    ),
    config_file: Optional[Path] = typer.Option(
        None,
        "--config", "-c",
        help="Path to configuration YAML file"
    ),
    split_level: Optional[int] = typer.Option(
        None,
        "--split-level", "-s",
        help="Heading level at which to split into chapters",
        min=1, max=6
    ),
    assets_dir: Optional[str] = typer.Option(
        None,
        "--assets-dir", "-a",
        help="Directory name for assets (relative to output)"
    ),
    locale: Optional[str] = typer.Option(
        None,
        "--locale", "-l",
        help="Language/locale for processing"
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose", "-v",
        help="Enable verbose output"
    )
):
    """
    Convert a document file to structured Markdown chapters.
    
    This tool uses docling to parse DOCX files and converts them into
    a structured set of Markdown files with extracted assets.
    """
    
    # Validate input file
    if not input_file.exists():
        console.print(f"[red]Error: Input file '{input_file}' does not exist[/red]")
        raise typer.Exit(1)
    
    if input_file.suffix.lower() != '.docx':
        console.print(f"[red]Error: Unsupported file format '{input_file.suffix}'. Supported: .docx[/red]")
        raise typer.Exit(1)
    
    try:
        # Load configuration
        config = load_config(config_file)
        
        # Override config with command line arguments
        config_overrides = {}
        if split_level is not None:
            config_overrides['split_level'] = split_level
        if assets_dir is not None:
            config_overrides['assets_dir'] = assets_dir
        if locale is not None:
            config_overrides['locale'] = locale
        
        if config_overrides:
            config_dict = config.model_dump()
            config_dict.update(config_overrides)
            config = PipelineConfig.from_dict(config_dict)
        
        if verbose:
            console.print(f"[blue]Input file:[/blue] {input_file}")
            console.print(f"[blue]Output directory:[/blue] {output_dir}")
            console.print(f"[blue]Split level:[/blue] {config.split_level}")
            console.print(f"[blue]Assets directory:[/blue] {config.assets_dir}")
            console.print(f"[blue]Locale:[/blue] {config.locale}")
            console.print()
        
        # Create pipeline
        pipeline = DocumentPipeline(config)
        
        # Process document with progress indicator
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True
        ) as progress:
            progress.add_task("Processing document...", total=None)
            
            result = pipeline.process(str(input_file), str(output_dir))
        
        # Report results
        if result.success:
            console.print("[green]✓[/green] Document processed successfully!")
            console.print("[blue]Generated files:[/blue]")
            console.print(f"  • Table of contents: {result.index_file}")
            console.print(f"  • Manifest: {result.manifest_file}")
            console.print(f"  • Chapters: {len(result.chapter_files)} files")
            console.print(f"  • Assets: {len(result.asset_files)} files")
            
            if verbose:
                console.print("\n[blue]Chapter files:[/blue]")
                for chapter_file in result.chapter_files:
                    console.print(f"  • {chapter_file}")
                
                if result.asset_files:
                    console.print("\n[blue]Asset files:[/blue]")
                    for asset_file in result.asset_files:
                        console.print(f"  • {asset_file}")
        else:
            console.print("[red]✗ Error processing document:[/red]")
            console.print(f"[red]{result.error_message}[/red]")
            raise typer.Exit(1)
            
    except Exception as e:
        console.print("[red]✗ Unexpected error:[/red]")
        console.print(f"[red]{str(e)}[/red]")
        if verbose:
            import traceback
            console.print(f"[red]{traceback.format_exc()}[/red]")
        raise typer.Exit(1)


@app.command()
def config_show(
    config_file: Optional[Path] = typer.Option(
        None,
        "--config", "-c",
        help="Path to configuration file"
    )
):
    """Show current configuration values."""
    try:
        config = load_config(config_file)
        console.print("[blue]Current configuration:[/blue]")
        for field_name, field_info in config.model_fields.items():
            value = getattr(config, field_name)
            description = field_info.description or "No description"
            console.print(f"  {field_name}: {value} ({description})")
    except Exception as e:
        console.print(f"[red]Error loading configuration:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def config_create(
    output_file: Path = typer.Option(
        Path("config.yaml"),
        "--output", "-o", 
        help="Path for new configuration file"
    ),
    force: bool = typer.Option(
        False,
        "--force", "-f",
        help="Overwrite existing configuration file"
    )
):
    """Create a default configuration file."""
    if output_file.exists() and not force:
        console.print(f"[red]Configuration file '{output_file}' already exists. Use --force to overwrite.[/red]")
        raise typer.Exit(1)
    
    try:
        config = PipelineConfig()
        config.to_yaml(output_file)
        console.print(f"[green]✓[/green] Created configuration file: {output_file}")
    except Exception as e:
        console.print(f"[red]Error creating configuration file:[/red] {e}")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()