"""
add_entity.py

CLI command to interactively add a new entity definition to project configuration.

This module provides a Typer command (`add_entity`):
  - Works with brickend.yaml (inline or external entities)

The command guides the user through:
  - Detecting project configuration mode
  - Prompting for a new entity name and its fields
  - Validating the updated entity list against Pydantic schemas
  - Writing the updated configuration back to the appropriate file
"""

import typer
from pathlib import Path
from typing import List, Optional

from pydantic import ValidationError
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm, IntPrompt

from brickend_core.config.validation_schemas import EntityConfig, FieldConfig
from brickend_core.utils.yaml_loader import load_project_config, save_project_config_preserving_mode
from brickend_core.utils.naming import validate_name

app = typer.Typer(add_completion=False)
console = Console()


def prompt_field_definitions(num_fields: int) -> List[FieldConfig]:
    """
    Interactively prompt the user to define each field for a new entity.

    Args:
        num_fields: Number of fields to prompt for

    Returns:
        List of FieldConfig objects
    """
    allowed_types = ["uuid", "string", "text", "integer", "float", "boolean", "datetime"]
    fields: List[FieldConfig] = []

    for i in range(1, num_fields + 1):
        console.print(f"\n[bold cyan]--- Field {i} ---[/bold cyan]")

        # Field name
        while True:
            field_name = Prompt.ask("Field name (snake_case)")
            if not validate_name(field_name):
                console.print(
                    "[red]Invalid field name. Must start with a letter and contain only letters, digits, or underscores.[/red]"
                )
                continue
            break

        # Field type
        while True:
            field_type = Prompt.ask(
                f"Field type",
                choices=allowed_types,
                default="string"
            ).lower()
            break

        is_primary_key = Confirm.ask("Is this field a primary key?", default=False)

        is_unique = Confirm.ask("Is this field unique?", default=False)

        if is_primary_key:
            is_nullable = False
            console.print("[yellow]Primary key fields are not nullable by default.[/yellow]")
        else:
            is_nullable = Confirm.ask("Is this field nullable?", default=True)

        default_value = Prompt.ask("Default value (leave blank for none)", default="")
        default_val = default_value if default_value.strip() != "" else None

        foreign_key = Prompt.ask(
            "Foreign key (format: OtherEntity.field, leave blank for none)",
            default=""
        )
        fk_val = foreign_key if foreign_key.strip() != "" else None

        constraints_input = Prompt.ask(
            "Constraints (comma-separated, leave blank for none)",
            default=""
        )
        constraints = (
            [c.strip() for c in constraints_input.split(",") if c.strip()]
            if constraints_input.strip()
            else []
        )

        try:
            field = FieldConfig(
                name=field_name,
                type=field_type,
                primary_key=is_primary_key,
                unique=is_unique,
                nullable=is_nullable,
                default=default_val,
                foreign_key=fk_val,
                constraints=constraints,
            )
            fields.append(field)

        except ValidationError as e:
            console.print(f"[red]Field validation error: {e}[/red]")
            console.print("[yellow]Please try again with valid values.[/yellow]")
            i -= 1
            continue

    return fields


def display_entity_preview(entity: EntityConfig) -> None:
    """Display a preview of the entity before saving."""
    table = Table(title=f"Entity: {entity.name}")
    table.add_column("Field", style="cyan")
    table.add_column("Type", style="green")
    table.add_column("Constraints", style="yellow")

    for field in entity.fields:
        constraints = []
        if field.primary_key:
            constraints.append("PK")
        if field.unique:
            constraints.append("UNIQUE")
        if not field.nullable:
            constraints.append("NOT NULL")
        if field.foreign_key:
            constraints.append(f"FK({field.foreign_key})")
        if field.default:
            constraints.append(f"DEFAULT({field.default})")

        table.add_row(
            field.name,
            field.type,
            ", ".join(constraints) if constraints else "—"
        )

    console.print(table)


@app.command("entity")
def add_entity(
        name: Optional[str] = typer.Option(None, "--name", "-n", help="Entity name (PascalCase)"),
        non_interactive: bool = typer.Option(False, "--non-interactive", help="Skip interactive prompts"),
) -> None:
    """
    Add a new entity to your Brickend project.

    The command automatically detects your project structure and updates the appropriate files.

    In interactive mode (default), you'll be guided through defining the entity and its fields.
    Use --non-interactive for scripted usage (requires --name and other parameters).

    Examples:
        brickend add entity                    # Interactive mode
        brickend add entity --name User        # Pre-fill entity name
    """

    console.print(Panel(
        "[bold blue]Add Entity to Brickend Project[/bold blue]\n"
        "Define a new data model for your application",
        title="🏗️ Entity Builder",
        border_style="blue"
    ))

    # Step 1: Load project configuration
    try:
        config = load_project_config()
    except FileNotFoundError as e:
        console.print(f"[red]Error: {e}[/red]")
        console.print("[yellow]Run 'brickend init' to create a new project[/yellow]")
        raise typer.Exit(code=1)
    except ValueError as e:
        console.print(f"[red]Configuration error: {e}[/red]")
        raise typer.Exit(code=1)

    # Display current mode
    if config._original_entities_path:
        console.print(f"[green]Project mode:[/green] External entities in {config._original_entities_path}")
        display_path = Path(config._original_entities_path)
    else:
        console.print(f"[green]Project mode:[/green] Inline entities in brickend.yaml")
        display_path = Path("brickend.yaml")

    # Step 2: Get entity name
    if not name:
        while True:
            name = Prompt.ask("\n[bold]Entity name[/bold] (PascalCase)")
            if not validate_name(name):
                console.print(
                    "[red]Invalid entity name. Must start with a letter and contain only letters, digits, or underscores.[/red]"
                )
                continue
            break

    # Check for existing entity
    existing_entities = [e.name for e in config.entities] if isinstance(config.entities, list) else []

    if name in existing_entities:
        if not Confirm.ask(f"\n[yellow]Entity '{name}' already exists. Overwrite?[/yellow]", default=False):
            console.print("[yellow]Cancelled.[/yellow]")
            raise typer.Exit(code=0)

    # Step 3: Get number of fields
    if non_interactive:
        console.print("[red]Non-interactive mode requires implementation of field specification via CLI args[/red]")
        console.print("[yellow]For now, please use interactive mode[/yellow]")
        raise typer.Exit(code=1)

    while True:
        try:
            num_fields = IntPrompt.ask("\n[bold]Number of fields[/bold]", default=1)
            if num_fields < 1:
                console.print("[red]Must have at least 1 field[/red]")
                continue
            break
        except ValueError:
            console.print("[red]Please enter a valid number[/red]")

    # Step 4: Define fields interactively
    try:
        fields = prompt_field_definitions(num_fields)
    except KeyboardInterrupt:
        console.print("\n[yellow]Cancelled by user.[/yellow]")
        raise typer.Exit(code=0)

    # Step 5: Create and validate entity
    try:
        entity = EntityConfig(name=name, fields=fields)
    except ValidationError as e:
        console.print(f"[red]Entity validation error: {e}[/red]")
        raise typer.Exit(code=1)

    # Step 6: Preview entity
    console.print("\n[bold green]Entity Preview:[/bold green]")
    display_entity_preview(entity)

    if not Confirm.ask("\n[bold]Save this entity?[/bold]", default=True):
        console.print("[yellow]Cancelled.[/yellow]")
        raise typer.Exit(code=0)

    # Step 7: Save entity
    try:
        # Ensure entities is a list
        if not isinstance(config.entities, list):
            config.entities = []

        # Remove existing entity with same name
        config.entities = [e for e in config.entities if e.name != entity.name]

        # Add new entity
        config.entities.append(entity)

        # Save using the function that preserves mode
        save_project_config_preserving_mode(config)

    except (ValueError, OSError) as e:
        console.print(f"[red]Error saving entity: {e}[/red]")
        raise typer.Exit(code=1)

    # Step 8: Success message
    console.print(Panel(
        f"[bold green]✅ Entity '{name}' added successfully![/bold green]\n\n"
        f"[bold]Configuration updated:[/bold] {display_path}\n"
        f"[bold]Fields added:[/bold] {len(fields)}\n\n"
        f"[bold]Next steps:[/bold]\n"
        f"  1. Run: brickend generate\n"
        f"  2. Review the generated code\n"
        f"  3. Run: brickend validate",
        title="🎉 Success",
        border_style="green"
    ))
