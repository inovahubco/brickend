"""
generate_code.py

CLI command to generate application code based on hybrid project configuration.

This module provides a Typer command (`generate_code`) that:
  - Loads project configuration from brickend.yaml (with entities fallback).
  - Validates stack configuration and template availability.
  - Uses the new multi-stack CodeGenerator with template priority system.
  - Generates code for the configured stack (FastAPI, Django, etc.).
"""

import typer
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.table import Table

from brickend_core.utils.yaml_loader import load_project_config, load_entities
from brickend_core.engine.context_builder import ContextBuilder
from brickend_core.engine.template_registry import TemplateRegistry
from brickend_core.engine.template_engine import TemplateEngine
from brickend_core.engine.code_generator import CodeGenerator
from brickend_core.config.project_schema import BrickendProject

app = typer.Typer(add_completion=False)
console = Console()


def find_project_root() -> Path:
    """Locate the project root by searching for a `src/brickend_core` directory in parent paths.

    Returns:
        Path: Path to the directory containing `src/brickend_core`.

    Raises:
        FileNotFoundError: If no `src/brickend_core` directory is found in the current path or its ancestors.
    """
    current = Path(__file__).resolve()

    # First, try to find src/brickend_core (development structure)
    for parent in [current] + list(current.parents):
        if (parent / "src" / "brickend_core").is_dir():
            return parent / "src"
        if (parent / "brickend_core").is_dir():
            return parent

    # Check current working directory
    cwd = Path.cwd()
    if (cwd / "src" / "brickend_core").is_dir():
        return cwd / "src"
    if (cwd / "brickend_core").is_dir():
        return cwd

    raise FileNotFoundError("Could not find project root with brickend_core directory")


def validate_project_config(config: BrickendProject, project_root: Path) -> None:
    """Validate project configuration for code generation.

    Args:
        config: Project configuration
        project_root: Path to project root containing brickend_core

    Raises:
        ValueError: If configuration is invalid
        FileNotFoundError: If required templates don't exist
    """
    # Validate entities exist
    if not config.entities:
        raise ValueError("No entities defined. Add entities to your configuration before generating code.")

    # Validate stack is supported
    integrations_path = project_root / "brickend_core" / "integrations" / "back"
    if not integrations_path.exists():
        raise FileNotFoundError(f"Integrations directory not found: {integrations_path}")

    stack_path = integrations_path / config.stack.back
    if not stack_path.exists():
        available_stacks = [d.name for d in integrations_path.iterdir() if d.is_dir()]
        raise ValueError(
            f"Stack '{config.stack.back}' is not available. "
            f"Available stacks: {', '.join(available_stacks)}"
        )

    # Check if stack has required templates (basic validation)
    required_templates = ["models_template.j2"]  # Minimum required
    for template in required_templates:
        template_path = stack_path / template
        if not template_path.exists():
            raise FileNotFoundError(f"Required template not found: {template_path}")


def get_stack_output_structure(stack: str) -> dict:
    """Get the output file structure for a given stack.

    Args:
        stack: Backend stack name

    Returns:
        Dict mapping component names to output file paths
    """
    structures = {
        "fastapi": {
            "models": "app/models.py",
            "schemas": "app/schemas.py",
            "crud": "app/crud.py",
            "router": "app/routers.py",
            "main": "app/main.py",
            "db": "app/database.py"
        },
        "django": {
            "models": "apps/core/models.py",
            "serializers": "apps/core/serializers.py",
            "viewsets": "apps/core/viewsets.py",
            "urls": "apps/core/urls.py",
            "admin": "apps/core/admin.py"
        }
    }

    return structures.get(stack, structures["fastapi"])  # FastAPI as default


def generate_with_progress(generator: CodeGenerator, config: BrickendProject, output_dir: Path) -> dict:
    """Generate code with progress indication.

    Args:
        generator: CodeGenerator instance
        config: Project configuration
        output_dir: Output directory

    Returns:
        Dict with generation results
    """
    stack = config.stack.back
    output_structure = get_stack_output_structure(stack)
    generated_files = {}

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        console=console,
    ) as progress:

        total_components = len(output_structure)
        task = progress.add_task(f"Generating {stack} code...", total=total_components)

        for component, relative_path in output_structure.items():
            try:
                output_path = output_dir / relative_path

                template_path = generator.template_engine.get_template_path("back", stack, component)

                context = generator.context_builder.build_context(config.entities)

                # Add project-specific context
                context.update({
                    "project": config.project.model_dump(),
                    "stack": config.stack.model_dump(),
                    "settings": config.settings.model_dump(),
                })

                if hasattr(config.settings, 'database_url') and config.settings.database_url:
                    context["database_url"] = config.settings.database_url

                generator.template_engine.render_component_to_file(
                    "back", stack, component, context, output_path
                )

                generated_files[component] = output_path
                progress.advance(task)

            except FileNotFoundError:
                progress.console.print(f"[yellow]Skipping {component} (template not found)[/yellow]")
                progress.advance(task)
                continue
            except Exception as e:
                progress.console.print(f"[red]Error generating {component}: {e}[/red]")
                progress.advance(task)
                continue

    return generated_files


@app.command("code")
def generate_code(
    config_path: Optional[Path] = typer.Option(
        None, "--config", "-c", help="Path to brickend.yaml (default: auto-detect)"
    ),
    output_dir: Optional[Path] = typer.Option(
        None, "--output", "-o", help="Directory where generated code will be written (default: current directory)"
    ),
    # Legacy parameters for backward compatibility
    entities_path: Optional[Path] = typer.Option(
        None, "--entities", help="[LEGACY] Path to entities.yaml file"
    ),
    integration: Optional[str] = typer.Option(
        None, "--integration", "-i", help="[LEGACY] Integration key (use brickend.yaml instead)"
    ),
    database_url: Optional[str] = typer.Option(
        None, "--db-url", help="Database URL override"
    ),
    validate_only: bool = typer.Option(
        False, "--validate-only", help="Only validate configuration without generating code"
    ),
) -> None:
    """Generate code based on project configuration.

    NEW USAGE (recommended):
      brickend generate
      brickend generate --output ./generated

    LEGACY USAGE (backward compatibility):
      brickend generate --entities entities.yaml --integration fastapi --output ./app

    The command automatically detects your project configuration from brickend.yaml
    or falls back to entities.yaml. Generated code structure depends on the
    configured stack (FastAPI, Django, etc.).

    Args:
        config_path: Path to brickend.yaml (auto-detected if not provided)
        output_dir: Directory where generated code will be written
        entities_path: [LEGACY] Path to entities.yaml file
        integration: [LEGACY] Integration key
        database_url: Database URL override
        validate_only: Only validate configuration without generating
    """

    console.print(Panel(
        "[bold blue]Brickend Code Generator[/bold blue]\n"
        "Generating code from your project configuration...",
        title="🔧 Generate",
        border_style="blue"
    ))

    # Determine operation mode: hybrid config or legacy
    use_legacy_mode = entities_path is not None or integration is not None

    if use_legacy_mode:
        console.print("[yellow]Using legacy mode (consider migrating to brickend.yaml)[/yellow]")

        # Legacy mode validation
        if not entities_path:
            entities_path = Path("entities.yaml")
        if not integration:
            integration = "fastapi"
        if not output_dir:
            output_dir = Path("./app")

        try:
            # Load entities using legacy method
            raw_entities = load_entities(entities_path)

            # Create minimal config for compatibility
            from brickend_core.config.project_schema import ProjectInfo, StackConfig
            config = BrickendProject(
                project=ProjectInfo(name="legacy_project"),
                stack=StackConfig(back=integration),
                entities=raw_entities["entities"]
            )

        except FileNotFoundError as e:
            console.print(f"[red]Error: {e}[/red]")
            raise typer.Exit(code=1)
        except ValueError as e:
            console.print(f"[red]Error: {e}[/red]")
            raise typer.Exit(code=1)

    else:
        # Modern hybrid configuration mode
        try:
            config = load_project_config(config_path or Path("brickend.yaml"))

        except FileNotFoundError as e:
            console.print(f"[red]Error: {e}[/red]")
            console.print("[yellow]Hint: Run 'brickend init' to create a new project[/yellow]")
            raise typer.Exit(code=1)
        except ValueError as e:
            console.print(f"[red]Configuration error: {e}[/red]")
            raise typer.Exit(code=1)

    # Set default output directory based on stack
    if not output_dir:
        if config.stack.back == "django":
            output_dir = Path(".")  # Django generates in current directory
        else:
            output_dir = Path(".")  # FastAPI and others too

    # Override database URL if provided
    if database_url:
        if not hasattr(config.settings, 'database_url'):
            config.settings.database_url = database_url
        else:
            config.settings.database_url = database_url

    # Display configuration info
    info_table = Table(title="Project Configuration")
    info_table.add_column("Setting", style="cyan")
    info_table.add_column("Value", style="green")

    info_table.add_row("Project Name", config.project.name)
    info_table.add_row("Backend Stack", config.stack.back)
    info_table.add_row("Database", config.stack.database or "Not specified")
    info_table.add_row("Entities Count", str(len(config.entities)))
    info_table.add_row("Output Directory", str(output_dir.resolve()))

    console.print(info_table)

    try:
        # Find project root and validate
        project_root = find_project_root()
        validate_project_config(config, project_root)

        if validate_only:
            console.print(Panel(
                "[bold green]✅ Configuration is valid![/bold green]\n"
                "Ready for code generation.",
                title="Validation Result",
                border_style="green"
            ))
            return

    except (FileNotFoundError, ValueError) as e:
        console.print(f"[red]Validation error: {e}[/red]")
        raise typer.Exit(code=1)

    try:
        # Initialize components for new plugin mode
        base_path = project_root / "brickend_core"

        # Use new template engine with priority system
        template_engine = TemplateEngine(base_path=base_path)

        # Use new template registry with plugin discovery
        template_registry = TemplateRegistry(base_path=base_path)

        # Initialize context builder
        context_builder = ContextBuilder()

        # Create output directory
        output_dir.mkdir(parents=True, exist_ok=True)

        # Create CodeGenerator (need to update this to use new interface)
        generator = CodeGenerator(template_engine, template_registry, output_dir)
        generator.context_builder = context_builder  # Add context builder

    except Exception as e:
        console.print(f"[red]Setup error: {e}[/red]")
        raise typer.Exit(code=1)

    try:
        # Generate code with progress
        generated_files = generate_with_progress(generator, config, output_dir)

        if not generated_files:
            console.print("[yellow]Warning: No files were generated[/yellow]")
            raise typer.Exit(code=1)

        # Success summary
        success_table = Table(title="Generated Files")
        success_table.add_column("Component", style="cyan")
        success_table.add_column("File Path", style="green")

        for component, file_path in generated_files.items():
            success_table.add_row(component, str(file_path))

        console.print(success_table)

        console.print(Panel(
            f"[bold green]✅ Code generated successfully![/bold green]\n\n"
            f"[bold]Generated {len(generated_files)} files for {config.stack.back} stack[/bold]\n"
            f"Output directory: {output_dir.resolve()}\n\n"
            f"[bold]Next steps:[/bold]\n"
            f"  1. Review the generated code\n"
            f"  2. Install dependencies: pip install -r requirements.txt\n"
            f"  3. Run database migrations if needed\n"
            f"  4. Start your application",
            title="🎉 Success",
            border_style="green"
        ))

    except Exception as e:
        console.print(f"[red]Generation error: {e}[/red]")
        raise typer.Exit(code=1)
