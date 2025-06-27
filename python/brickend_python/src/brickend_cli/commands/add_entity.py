"""
add_entity.py

CLI command to interactively add a new entity definition to project configuration.

This module provides a Typer command (`add_entity`) that supports hybrid configuration:
  - Modern mode: Works with brickend.yaml (inline or external entities)
  - Legacy mode: Works directly with entities.yaml

The command guides the user through:
  - Detecting project configuration mode
  - Prompting for a new entity name and its fields
  - Validating the updated entity list against Pydantic schemas
  - Writing the updated configuration back to the appropriate file
"""

import typer
from pathlib import Path
from typing import List, Optional

import ruamel.yaml
from pydantic import ValidationError
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm, IntPrompt

from brickend_core.config.validation_schemas import EntitiesFile, EntityConfig, FieldConfig
from brickend_core.config.project_schema import BrickendProject
from brickend_core.utils.yaml_loader import load_project_config, save_project_config
from brickend_core.utils.naming import validate_name

app = typer.Typer(add_completion=False)
console = Console()


def detect_project_mode() -> tuple[str, Path, Optional[BrickendProject]]:
    """
    Detect project configuration mode and return appropriate information.

    Returns:
        Tuple of (mode, file_path, config):
        - mode: "hybrid_external", "hybrid_inline", or "legacy"
        - file_path: Path to file that should be modified
        - config: BrickendProject object (None for legacy mode)
    """
    try:
        # Try to load modern configuration
        config = load_project_config()

        if config.is_entities_external():
            # External entities mode
            entities_file_path = config.get_entities_file_path()
            return "hybrid_external", entities_file_path, config
        else:
            # Inline entities mode
            return "hybrid_inline", Path("brickend.yaml"), config

    except FileNotFoundError:
        # No brickend.yaml found, try legacy mode
        entities_path = Path("entities.yaml")
        if entities_path.exists():
            return "legacy", entities_path, None
        else:
            # No configuration found
            raise FileNotFoundError(
                "No project configuration found. "
                "Run 'brickend init' to create a new project or ensure you're in a Brickend project directory."
            )


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


def save_entity_hybrid_external(entity: EntityConfig, entities_file_path: Path) -> None:
    """Save entity to external entities file."""
    # Load existing entities file
    yaml = ruamel.yaml.YAML()
    yaml.default_flow_style = False
    yaml.width = 120
    yaml.indent(mapping=2, sequence=4, offset=2)

    try:
        if entities_file_path.exists():
            with entities_file_path.open("r", encoding="utf-8") as f:
                data = yaml.load(f) or {}
        else:
            data = {}
    except ruamel.yaml.YAMLError as e:
        raise ValueError(f"Error parsing entities file: {e}")

    # Ensure entities list exists
    entities_list = data.get("entities", [])
    if not isinstance(entities_list, list):
        entities_list = []

    # Remove existing entity with same name
    entities_list = [e for e in entities_list if e.get("name") != entity.name]

    # Add new entity
    entities_list.append(entity.model_dump())
    data["entities"] = entities_list

    # Validate complete file
    try:
        EntitiesFile.model_validate(data)
    except ValidationError as e:
        raise ValueError(f"Entities file validation error: {e}")

    # Save file
    try:
        with entities_file_path.open("w", encoding="utf-8") as f:
            yaml.dump(data, f)
    except Exception as e:
        raise OSError(f"Error writing entities file: {e}")


def save_entity_hybrid_inline(entity: EntityConfig, config: BrickendProject) -> None:
    """Save entity to inline entities in brickend.yaml."""
    # Add entity to inline list
    if not isinstance(config.entities, list):
        config.entities = []

    # Remove existing entity with same name
    config.entities = [e for e in config.entities if e.name != entity.name]

    # Add new entity
    config.entities.append(entity)

    # Save updated config
    try:
        save_project_config(config)
    except Exception as e:
        raise OSError(f"Error saving project configuration: {e}")


def save_entity_legacy(entity: EntityConfig, entities_path: Path) -> None:
    """Save entity using legacy mode (direct entities.yaml)."""
    yaml = ruamel.yaml.YAML()
    yaml.default_flow_style = False

    try:
        if entities_path.exists():
            with entities_path.open("r", encoding="utf-8") as f:
                data = yaml.load(f) or {}
        else:
            data = {}
    except ruamel.yaml.YAMLError as e:
        raise ValueError(f"Error parsing entities.yaml: {e}")

    # Ensure entities list
    entities_list = data.get("entities", [])
    if not isinstance(entities_list, list):
        entities_list = []

    # Remove existing entity with same name
    entities_list = [e for e in entities_list if e.get("name") != entity.name]

    # Add new entity
    entities_list.append(entity.model_dump())
    data["entities"] = entities_list

    # Validate
    try:
        EntitiesFile.model_validate(data)
    except ValidationError as e:
        raise ValueError(f"Validation error: {e}")

    # Save
    try:
        with entities_path.open("w", encoding="utf-8") as f:
            yaml.dump(data, f)
    except Exception as e:
        raise OSError(f"Error writing to entities.yaml: {e}")


@app.command("entity")
def add_entity(
    name: Optional[str] = typer.Option(None, "--name", "-n", help="Entity name (PascalCase)"),
    non_interactive: bool = typer.Option(False, "--non-interactive", help="Skip interactive prompts"),
) -> None:
    """
    Add a new entity to your Brickend project.

    Supports both modern (brickend.yaml) and legacy (entities.yaml) project configurations.
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

    # Step 1: Detect project configuration mode
    try:
        mode, file_path, config = detect_project_mode()
    except FileNotFoundError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(code=1)

    # Display current mode
    mode_info = {
        "hybrid_external": f"Modern project (external entities in {file_path.name})",
        "hybrid_inline": "Modern project (inline entities in brickend.yaml)",
        "legacy": "Legacy project (entities.yaml)"
    }

    console.print(f"[green]Project mode:[/green] {mode_info[mode]}")
    console.print(f"[green]Target file:[/green] {file_path}")

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
    existing_entities = []
    if mode == "hybrid_external":
        try:
            if file_path.exists():
                yaml = ruamel.yaml.YAML()
                with file_path.open("r", encoding="utf-8") as f:
                    data = yaml.load(f) or {}
                existing_entities = [e.get("name") for e in data.get("entities", [])]
        except Exception:
            pass
    elif mode == "hybrid_inline":
        existing_entities = [e.name for e in config.entities]
    elif mode == "legacy":
        try:
            if file_path.exists():
                yaml = ruamel.yaml.YAML()
                with file_path.open("r", encoding="utf-8") as f:
                    data = yaml.load(f) or {}
                existing_entities = [e.get("name") for e in data.get("entities", [])]
        except Exception:
            pass

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

    # Step 7: Save entity based on mode
    try:
        if mode == "hybrid_external":
            save_entity_hybrid_external(entity, file_path)
        elif mode == "hybrid_inline":
            save_entity_hybrid_inline(entity, config)
        elif mode == "legacy":
            save_entity_legacy(entity, file_path)

    except (ValueError, OSError) as e:
        console.print(f"[red]Error saving entity: {e}[/red]")
        raise typer.Exit(code=1)

    # Step 8: Success message
    console.print(Panel(
        f"[bold green]✅ Entity '{name}' added successfully![/bold green]\n\n"
        f"[bold]Configuration updated:[/bold] {file_path}\n"
        f"[bold]Fields added:[/bold] {len(fields)}\n\n"
        f"[bold]Next steps:[/bold]\n"
        f"  1. Run: brickend generate\n"
        f"  2. Review the generated code\n"
        f"  3. Run: brickend validate",
        title="🎉 Success",
        border_style="green"
    ))
