"""
yaml_loader.py

Loads an entities YAML file and validates it using Pydantic schemas defined in core.config.validation_schemas.
"""

from pathlib import Path
from typing import Any, Dict

import ruamel.yaml
from pydantic import ValidationError

from brickend_core.config.validation_schemas import EntitiesFile


def load_entities(path: Path) -> Dict[str, Any]:
    """
    Load and validate an entities YAML file using Pydantic.

    Steps:
    1. Verify that the given path exists.
    2. Parse the YAML content into a Python dict.
    3. Use EntitiesFile.parse_obj(...) to validate the structure and field constraints.
    4. Return the validated dictionary representation.

    Args:
        path (Path): Path to the YAML file that defines entities.

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
