"""
yaml_loader.py

Load and validate YAML files using Pydantic schemas defined in
brickend_core.config.validation_schemas and brickend_core.config.project_schema.
"""

from pathlib import Path
from typing import Any, Dict

import ruamel.yaml
from pydantic import ValidationError

from brickend_core.config.validation_schemas import EntitiesFile
from brickend_core.config.project_schema import BrickendProject


def load_entities(path: Path) -> Dict[str, Any]:
    """
    Load and validate an entities YAML file.

    Steps:
      1. Verify that the given path exists.
      2. Parse the YAML content into a Python dict.
      3. Validate structure and constraints via EntitiesFile.
      4. Return the validated dictionary representation.

    Args:
        path (Path): Path to the YAML file defining entities.

    Returns:
        Dict[str, Any]: The validated content as a Python dict.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If YAML parsing fails or validation errors occur.
    """
    if not path.exists():
        raise FileNotFoundError(f"Entities file not found: {path}")

    yaml = ruamel.yaml.YAML(typ="safe")
    try:
        with path.open("r", encoding="utf-8") as f:
            raw_data = yaml.load(f)
    except ruamel.yaml.YAMLError as e:
        raise ValueError(f"Failed to parse YAML at {path}: {e}")

    try:
        entities_file = EntitiesFile.model_validate(raw_data)
    except ValidationError as e:
        raise ValueError(f"Validation error in '{path}': {e}")

    return entities_file.model_dump()


def load_project_config(path: Path = Path("brickend.yaml")) -> BrickendProject:
    """
    Load and validate a brickend.yaml project configuration file with fallback support.

    Supports hybrid entities configuration:
    - If brickend.yaml exists: Load it and handle inline/external entities
    - If brickend.yaml doesn't exist: Fallback to legacy entities.yaml mode

    Steps:
      1. Try to load brickend.yaml if it exists
      2. If entities field is a string (external file), load that file
      3. If brickend.yaml doesn't exist, fallback to entities.yaml legacy mode
      4. Validate all configurations using appropriate Pydantic models
      5. Return the validated BrickendProject instance

    Args:
        path (Path): Path to the brickend.yaml file. Defaults to "./brickend.yaml".

    Returns:
        BrickendProject: The validated project configuration.

    Raises:
        FileNotFoundError: If neither brickend.yaml nor entities.yaml exist,
                          or if referenced external entities file doesn't exist.
        ValueError: If YAML parsing fails or validation errors occur.
    """
    yaml = ruamel.yaml.YAML(typ="safe")

    if path.exists():
        try:
            with path.open("r", encoding="utf-8") as f:
                raw_data = yaml.load(f)
        except ruamel.yaml.YAMLError as e:
            raise ValueError(f"Failed to parse YAML at {path}: {e}")

        if raw_data is None:
            raise ValueError(f"Empty or invalid YAML file: {path}")

        try:
            # Parse as BrickendProject to get initial validation
            config = BrickendProject.model_validate(raw_data)
        except ValidationError as e:
            raise ValueError(f"Validation error in '{path}': {e}")

        # Handle external entities file if needed
        if config.is_entities_external():
            original_path = str(config.entities)
            entities_file_path = config.get_entities_file_path()

            # Resolve relative path based on brickend.yaml location
            if not entities_file_path.is_absolute():
                entities_file_path = path.parent / entities_file_path

            if not entities_file_path.exists():
                raise FileNotFoundError(
                    f"External entities file not found: {entities_file_path} "
                    f"(referenced from {path})"
                )

            # Load and validate external entities file
            try:
                with entities_file_path.open("r", encoding="utf-8") as f:
                    entities_raw_data = yaml.load(f)
            except ruamel.yaml.YAMLError as e:
                raise ValueError(f"Failed to parse entities YAML at {entities_file_path}: {e}")

            try:
                entities_file = EntitiesFile.model_validate(entities_raw_data)
            except ValidationError as e:
                raise ValueError(f"Validation error in entities file '{entities_file_path}': {e}")

            # Create new config with loaded entities but preserve original path
            config = BrickendProject(
                project=config.project,
                stack=config.stack,
                entities=entities_file.entities,
                settings=config.settings,
                deploy=config.deploy,
                plugins=config.plugins,
                custom=config.custom
            )
            config._original_entities_path = original_path

        return config

    raise FileNotFoundError(
        f"No configuration file found."
    )


def save_project_config(config: BrickendProject, path: Path = Path("brickend.yaml")) -> None:
    """
    Save a BrickendProject configuration to a YAML file.

    Preserves the hybrid entities configuration:
    - If entities were loaded from external file, keeps the file reference
    - If entities were inline, saves them inline

    Args:
        config (BrickendProject): The project configuration to save.
        path (Path): Output path for the brickend.yaml file. Defaults to "./brickend.yaml".

    Raises:
        ValueError: If YAML serialization fails.
        IOError: If file writing fails.
    """
    yaml = ruamel.yaml.YAML()
    yaml.default_flow_style = False
    yaml.width = 120
    yaml.indent(mapping=2, sequence=4, offset=2)

    try:
        config_dict = config.model_dump(exclude_none=True)

        with path.open("w", encoding="utf-8") as f:
            yaml.dump(config_dict, f)

    except Exception as e:
        raise ValueError(f"Failed to save project configuration to {path}: {e}")


def validate_entities_file_reference(entities_ref: str, base_path: Path = Path(".")) -> Path:
    """
    Validate and resolve an entities file reference.

    Args:
        entities_ref (str): String reference to entities file (e.g., "./entities.yaml").
        base_path (Path): Base path for resolving relative references.

    Returns:
        Path: Resolved absolute path to the entities file.

    Raises:
        FileNotFoundError: If the referenced file doesn't exist.
        ValueError: If the reference format is invalid.
    """
    if not entities_ref.strip():
        raise ValueError("Entities file reference cannot be empty")

    entities_path = Path(entities_ref.strip())

    # Resolve relative path
    if not entities_path.is_absolute():
        entities_path = base_path / entities_path

    # Normalize path
    entities_path = entities_path.resolve()

    if not entities_path.exists():
        raise FileNotFoundError(f"Entities file not found: {entities_path}")

    if not entities_path.is_file():
        raise ValueError(f"Entities reference must point to a file: {entities_path}")

    return entities_path


# En src/brickend_core/utils/yaml_loader.py

def save_project_config_preserving_mode(config: BrickendProject, path: Path = Path("brickend.yaml")) -> None:
    """
    Save a BrickendProject configuration preserving the original entities' mode.

    If entities were originally external, saves them to the external file and
    keeps the reference in brickend.yaml.
    """
    yaml = ruamel.yaml.YAML()
    yaml.default_flow_style = False
    yaml.width = 120
    yaml.indent(mapping=2, sequence=4, offset=2)

    try:
        # Check if entities were originally external
        if config._original_entities_path:
            # Save entities to external file
            entities_path = Path(config._original_entities_path)

            # Resolve relative to brickend.yaml location
            if not entities_path.is_absolute():
                entities_path = path.parent / entities_path

            # Save entities to external file
            entities_data = {
                "entities": [entity.model_dump() for entity in config.entities]
            }

            with entities_path.open("w", encoding="utf-8") as f:
                yaml.dump(entities_data, f)

            # Save brickend.yaml with external reference
            config_dict = config.model_dump(exclude_none=True)
            config_dict["entities"] = config._original_entities_path

            with path.open("w", encoding="utf-8") as f:
                yaml.dump(config_dict, f)
        else:
            # Save normally (inline mode)
            save_project_config(config, path)

    except Exception as e:
        raise ValueError(f"Failed to save project configuration: {e}")
