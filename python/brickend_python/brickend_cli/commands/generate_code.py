"""
generate_code.py
"""

import typer
from pathlib import Path
from typing import Optional

from brickend_core.utils.yaml_loader import load_entities
from brickend_core.engine.context_builder import ContextBuilder
from brickend_core.engine.template_registry import TemplateRegistry
from brickend_core.engine.template_engine import TemplateEngine
from brickend_core.engine.code_generator import CodeGenerator

app = typer.Typer(add_completion=False)


def find_project_root() -> Path:
    """
    Find the project root by looking for brickend_core directory.
    This is more robust than using hardcoded parent levels.
    """
    current = Path(__file__).resolve()

    for parent in [current] + list(current.parents):
        brickend_core = parent / "brickend_core"
        if brickend_core.exists() and brickend_core.is_dir():
            return parent

    cwd = Path.cwd()
    brickend_core = cwd / "brickend_core"
    if brickend_core.exists() and brickend_core.is_dir():
        return cwd

    raise FileNotFoundError("Could not find project root with brickend_core directory")


@app.command("code")
def generate_code(
    entities_path: Path = typer.Argument(
        ..., help="Path to the entities.yaml file defining your entities"
    ),
    output_dir: Path = typer.Option(
        ..., "--output", "-o", help="Directory where generated code will be written"
    ),
    integration: str = typer.Option(
        "fastapi", "--integration", "-i", help="Integration key (e.g., 'fastapi')"
    ),
    database_url: Optional[str] = typer.Option(
        "", "--db-url", help="Database URL for db.py (e.g., 'sqlite:///./test.db')"
    ),
) -> None:
    """
    Generate code (models, schemas, CRUD, routers, main, db) for the specified
    integration using the entities defined in entities.yaml.
    """
    try:
        raw = load_entities(entities_path)
    except FileNotFoundError as fnf_err:
        typer.echo(f"Error: {fnf_err}")
        raise typer.Exit(code=1)
    except ValueError as val_err:
        typer.echo(f"Error: {val_err}")
        raise typer.Exit(code=1)

    try:
        builder = ContextBuilder()
        context = builder.build_context(raw)
    except ValueError as ctx_err:
        typer.echo(f"Context error: {ctx_err}")
        raise typer.Exit(code=1)

    if database_url:
        context["database_url"] = database_url
    else:
        typer.echo("Warning: No database_url provided; db.py may be incomplete.")

    try:
        project_root = find_project_root()
    except FileNotFoundError as e:
        typer.echo(f"Error: {e}")
        raise typer.Exit(code=1)

    templates_base = project_root / "brickend_core" / "integrations" / "back"

    integration_dir = templates_base / integration
    if not integration_dir.exists() or not integration_dir.is_dir():
        typer.echo(f"Generation error: Integration '{integration}' not found.")
        raise typer.Exit(code=1)

    registry = TemplateRegistry([integration_dir])
    engine = TemplateEngine([integration_dir], auto_reload=False)

    try:
        output_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        typer.echo(f"Error: Cannot create output directory '{output_dir}': {e}")
        raise typer.Exit(code=1)

    try:
        generator = CodeGenerator(engine, registry, output_dir)
        generator.generate_project(context, integration)
    except ValueError as ve:
        typer.echo(f"Generation error: {ve}")
        raise typer.Exit(code=1)
    except FileNotFoundError as fnf:
        typer.echo(f"Generation error: {fnf}")
        raise typer.Exit(code=1)
    except Exception as e:
        typer.echo(f"Unexpected error during generation: {e}")
        raise typer.Exit(code=1)

    typer.echo(f"✅ Code generated successfully in '{output_dir}'")
