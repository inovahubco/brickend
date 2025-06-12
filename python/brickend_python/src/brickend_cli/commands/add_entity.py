"""
add_entity.py

CLI command to interactively add a new entity definition to entities.yaml.

This module provides a Typer command (`add_entity`) that guides the user through:
  - Locating or creating an `entities.yaml` file in the current directory.
  - Prompting for a new entity name and its fields.
  - Validating the updated entity list against the Pydantic schema.
  - Writing the updated configuration back to `entities.yaml`.
"""

import typer
from pathlib import Path
from typing import Dict, Any, List

import ruamel.yaml
from pydantic import ValidationError

from brickend_core.config.validation_schemas import EntitiesFile
from brickend_core.utils.naming import validate_name

app = typer.Typer(add_completion=False)


def find_entities_file() -> Path:
    """Locate the `entities.yaml` file in the current working directory.

    Returns:
        Path: Path object pointing to `entities.yaml`.

    Raises:
        FileNotFoundError: If `entities.yaml` is not present in the cwd.
    """
    entities_path = Path.cwd() / "entities.yaml"
    if not entities_path.exists():
        raise FileNotFoundError("entities.yaml not found in the current directory.")
    return entities_path


def prompt_field_definitions(num_fields: int) -> List[Dict[str, Any]]:
    """Interactively prompt the user to define each field for a new entity.

    Args:
        num_fields (int): Number of fields to prompt for.

    Returns:
        List[Dict[str, Any]]: A list of field-definition dictionaries, each containing:
            - name (str)
            - type (str)
            - primary_key (bool)
            - unique (bool)
            - nullable (bool)
            - default (Optional[str])
            - foreign_key (Optional[str])
            - constraints (List[str])
    """
    allowed_types = ["uuid", "string", "text", "integer", "float", "boolean", "datetime"]
    fields: List[Dict[str, Any]] = []

    for i in range(1, num_fields + 1):
        typer.echo(f"\n--- Field {i} ---")
        # Name
        while True:
            field_name = typer.prompt("Field name (snake_case)")
            if not validate_name(field_name):
                typer.echo(
                    "Invalid field name. Must start with a letter and contain only letters, digits, or underscores."
                )
                continue
            break

        # Type
        while True:
            field_type = typer.prompt(f"Field type (choose from {', '.join(allowed_types)})").lower()
            if field_type not in allowed_types:
                typer.echo(f"Invalid type. Please choose one of: {', '.join(allowed_types)}")
                continue
            break

        # Primary key?
        pk_input = typer.prompt("Is this field a primary key? [y/N]").lower()
        is_primary_key = pk_input.startswith("y")

        # Unique?
        unique_input = typer.prompt("Is this field unique? [y/N]").lower()
        is_unique = unique_input.startswith("y")

        # Nullable (non-nullable if primary key)
        if is_primary_key:
            is_nullable = False
            typer.echo("Primary key fields are not nullable by default.")
        else:
            nullable_input = typer.prompt("Is this field nullable? [Y/n]").lower()
            is_nullable = not nullable_input.startswith("n")

        # Default value
        default_value = typer.prompt("Default value (leave blank for none)", default="")
        default_val = default_value if default_value.strip() != "" else None

        # Foreign key
        foreign_key = typer.prompt(
            "Foreign key (format: OtherEntity.field, leave blank for none)", default=""
        )
        fk_val = foreign_key if foreign_key.strip() != "" else None

        # Additional constraints
        constraints_input = typer.prompt(
            "Constraints (comma-separated, leave blank for none)", default=""
        )
        constraints = (
            [c.strip() for c in constraints_input.split(",") if c.strip()]
            if constraints_input.strip()
            else []
        )

        fields.append(
            {
                "name": field_name,
                "type": field_type,
                "primary_key": is_primary_key,
                "unique": is_unique,
                "nullable": is_nullable,
                "default": default_val,
                "foreign_key": fk_val,
                "constraints": constraints,
            }
        )

    return fields


@app.command("entity")
def add_entity() -> None:
    """Typer command to add a new entity entry to `entities.yaml`.

    This command will:
      1. Locate an existing `entities.yaml` (or abort if not found).
      2. Load and parse its content.
      3. Prompt for a unique entity name (PascalCase).
      4. Prompt for the number of fields and their definitions.
      5. Validate the updated entities against the Pydantic schema.
      6. Write the updated configuration back to disk.

    Raises:
        typer.Exit: On any error (file not found, parse error, validation error, or write error),
                    exits with non-zero status after displaying an error message.
    """
    # Step 1: find or abort
    try:
        entities_path = find_entities_file()
    except FileNotFoundError as e:
        typer.echo(f"Error: {e}")
        raise typer.Exit(code=1)

    # Step 2: load YAML
    yaml = ruamel.yaml.YAML()
    try:
        with entities_path.open("r", encoding="utf-8") as f:
            data = yaml.load(f) or {}
    except ruamel.yaml.YAMLError as ye:
        typer.echo(f"Error parsing entities.yaml: {ye}")
        raise typer.Exit(code=1)

    # Ensure 'entities' key
    entities_list = data.get("entities")
    if entities_list is None:
        entities_list = []
        data["entities"] = entities_list
    elif not isinstance(entities_list, list):
        typer.echo("Error: 'entities' key exists but is not a list.")
        raise typer.Exit(code=1)

    # Step 3: prompt entity name
    while True:
        entity_name = typer.prompt("\nEntity name (PascalCase)")
        if not validate_name(entity_name):
            typer.echo(
                "Invalid entity name. Must start with a letter and contain only letters, digits, or underscores."
            )
            continue
        break

    # Handle overwrite if exists
    existing = next((e for e in entities_list if e.get("name") == entity_name), None)
    if existing:
        overwrite = typer.prompt(
            f"Entity '{entity_name}' already exists. Overwrite? [y/N]"
        ).lower()
        if not overwrite.startswith("y"):
            typer.echo("Aborting without changes.")
            raise typer.Exit(code=0)
        entities_list = [e for e in entities_list if e.get("name") != entity_name]
        data["entities"] = entities_list

    # Step 4: number of fields
    while True:
        try:
            num_fields = int(typer.prompt("\nNumber of fields (integer >= 1)"))
            if num_fields < 1:
                raise ValueError()
            break
        except ValueError:
            typer.echo("Please enter a valid integer >= 1.")

    # Step 5: prompt field definitions
    fields = prompt_field_definitions(num_fields)
    new_entity: Dict[str, Any] = {"name": entity_name, "fields": fields}

    updated_entities = entities_list + [new_entity]

    # Step 6: validate against Pydantic schema
    try:
        EntitiesFile.model_validate({"entities": updated_entities})
    except ValidationError as ve:
        typer.echo(f"Validation error: {ve}")
        raise typer.Exit(code=1)

    data["entities"] = updated_entities

    # Step 7: write file
    try:
        with entities_path.open("w", encoding="utf-8") as f:
            yaml.dump(data, f)
    except Exception as e:
        typer.echo(f"Error writing to entities.yaml: {e}")
        raise typer.Exit(code=1)

    typer.echo(f"\n✅ Entity '{entity_name}' added to entities.yaml.")
