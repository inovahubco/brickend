"""
add_entity.py
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
    """
    Locate 'entities.yaml' in the current working directory.
    Raise FileNotFoundError if not found.
    """
    entities_path = Path.cwd() / "entities.yaml"
    if not entities_path.exists():
        raise FileNotFoundError("entities.yaml not found in the current directory.")
    return entities_path


def prompt_field_definitions(num_fields: int) -> List[Dict[str, Any]]:
    """
    Prompt the user for field definitions.

    Args:
        num_fields (int): Number of fields to prompt.

    Returns:
        List[Dict[str, Any]]: List of field dictionaries as required by EntitiesFile.
    """
    allowed_types = ["uuid", "string", "text", "integer", "float", "boolean", "datetime"]
    fields: List[Dict[str, Any]] = []

    for i in range(1, num_fields + 1):
        typer.echo(f"\n--- Field {i} ---")
        while True:
            field_name = typer.prompt("Field name (snake_case)")
            if not validate_name(field_name):
                typer.echo(
                    "Invalid field name. Must start with a letter and contain only letters, digits, or underscores."
                )
                continue
            break

        while True:
            field_type = typer.prompt(
                f"Field type (choose from {', '.join(allowed_types)})"
            ).lower()
            if field_type not in allowed_types:
                typer.echo(f"Invalid type. Please choose one of: {', '.join(allowed_types)}")
                continue
            break

        pk_input = typer.prompt("Is this field a primary key? [y/N]").lower()
        is_primary_key = pk_input.startswith("y")

        unique_input = typer.prompt("Is this field unique? [y/N]").lower()
        is_unique = unique_input.startswith("y")

        if is_primary_key:
            is_nullable = False
            typer.echo("Primary key fields are not nullable by default.")
        else:
            nullable_input = typer.prompt("Is this field nullable? [Y/n]").lower()
            is_nullable = not nullable_input.startswith("n")

        default_value = typer.prompt("Default value (leave blank for none)", default="")
        default_val = default_value if default_value.strip() != "" else None

        foreign_key = typer.prompt(
            "Foreign key (format: OtherEntity.field, leave blank for none)", default=""
        )
        fk_val = foreign_key if foreign_key.strip() != "" else None

        constraints_input = typer.prompt(
            "Constraints (comma-separated, leave blank for none)", default=""
        )
        if constraints_input.strip():
            constraints = [c.strip() for c in constraints_input.split(",") if c.strip()]
        else:
            constraints = []

        field_dict: Dict[str, Any] = {
            "name": field_name,
            "type": field_type,
            "primary_key": is_primary_key,
            "unique": is_unique,
            "nullable": is_nullable,
            "default": default_val,
            "foreign_key": fk_val,
            "constraints": constraints,
        }
        fields.append(field_dict)

    return fields


@app.command("add_entity")
def add_entity() -> None:
    """
    Prompt the user to add a new entity to 'entities.yaml' in the current directory.
    """
    try:
        entities_path = find_entities_file()
    except FileNotFoundError as e:
        typer.echo(f"Error: {e}")
        raise typer.Exit(code=1)

    yaml = ruamel.yaml.YAML()
    try:
        with entities_path.open("r", encoding="utf-8") as f:
            data = yaml.load(f) or {}
    except ruamel.yaml.YAMLError as ye:
        typer.echo(f"Error parsing entities.yaml: {ye}")
        raise typer.Exit(code=1)

    entities_list = data.get("entities")
    if entities_list is None:
        entities_list = []
        data["entities"] = entities_list
    elif not isinstance(entities_list, list):
        typer.echo("Error: 'entities' key exists but is not a list.")
        raise typer.Exit(code=1)

    while True:
        entity_name = typer.prompt("\nEntity name (PascalCase)")
        if not validate_name(entity_name):
            typer.echo(
                "Invalid entity name. Must start with a letter and contain only letters, digits, or underscores."
            )
            continue
        break

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

    while True:
        try:
            num_fields = int(typer.prompt("\nNumber of fields (integer >= 1)"))
            if num_fields < 1:
                raise ValueError()
            break
        except ValueError:
            typer.echo("Please enter a valid integer >= 1.")

    fields = prompt_field_definitions(num_fields)

    new_entity: Dict[str, Any] = {"name": entity_name, "fields": fields}

    updated_entities = entities_list + [new_entity]
    try:
        EntitiesFile.model_validate({"entities": updated_entities})
    except ValidationError as ve:
        typer.echo(f"Validation error: {ve}")
        raise typer.Exit(code=1)

    data["entities"] = updated_entities
    try:
        with entities_path.open("w", encoding="utf-8") as f:
            yaml.dump(data, f)
    except Exception as e:
        typer.echo(f"Error writing to entities.yaml: {e}")
        raise typer.Exit(code=1)

    typer.echo(f"\n✅ Entity '{entity_name}' added to entities.yaml.")
