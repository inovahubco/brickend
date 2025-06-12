"""
test_yaml_loader.py

Unit tests for the `load_entities` function in brickend_core.utils.yaml_loader.
Covers:
  - Successful load of a valid entities YAML.
  - FileNotFoundError when the file is missing.
  - ValueError when the top-level 'entities' key is missing.
  - ValueError when 'entities' is not a list.
  - ValueError for an invalid field type.
  - ValueError when an entity has an empty 'fields' list.
"""

import pytest
from pathlib import Path

from brickend_core.utils.yaml_loader import load_entities


@pytest.fixture
def valid_entities_yaml(tmp_path):
    """
    Create a minimal valid entities YAML file for testing.

    Args:
        tmp_path (Path): Temporary directory provided by pytest.

    Returns:
        Path: Path to the created valid entities YAML file.
    """
    content = """
    entities:
      - name: User
        fields:
          - name: id
            type: uuid
          - name: email
            type: string
    """
    file_path = tmp_path / "entities_valid.yaml"
    file_path.write_text(content, encoding="utf-8")
    return file_path


@pytest.fixture
def missing_entities_key(tmp_path):
    """
    Create a YAML file that does not contain the 'entities' key to trigger a missing-key error.

    Args:
        tmp_path (Path): Temporary directory provided by pytest.

    Returns:
        Path: Path to the YAML file without the 'entities' key.
    """
    content = """
    models:
      - name: Product
        fields:
          - name: id
            type: uuid
    """
    file_path = tmp_path / "no_entities.yaml"
    file_path.write_text(content, encoding="utf-8")
    return file_path


@pytest.fixture
def entities_not_list(tmp_path):
    """
    Create a YAML file where 'entities' is not a list to trigger a type error.

    Args:
        tmp_path (Path): Temporary directory provided by pytest.

    Returns:
        Path: Path to the malformed entities YAML file.
    """
    content = """
    entities: "this should be a list, not a string"
    """
    file_path = tmp_path / "entities_not_list.yaml"
    file_path.write_text(content, encoding="utf-8")
    return file_path


@pytest.fixture
def invalid_field_type(tmp_path):
    """
    Create a YAML file where one field has an invalid type not in ALLOWED_FIELD_TYPES.

    Args:
        tmp_path (Path): Temporary directory provided by pytest.

    Returns:
        Path: Path to the YAML file with invalid field type.
    """
    content = """
    entities:
      - name: Customer
        fields:
          - name: id
            type: uuid
          - name: age
            type: int32  # not in ALLOWED_FIELD_TYPES
    """
    file_path = tmp_path / "invalid_field_type.yaml"
    file_path.write_text(content, encoding="utf-8")
    return file_path


@pytest.fixture
def entity_with_no_fields(tmp_path):
    """
    Create a YAML file where an entity has an empty 'fields' list to trigger a validation error.

    Args:
        tmp_path (Path): Temporary directory provided by pytest.

    Returns:
        Path: Path to the YAML file with an entity missing fields.
    """
    content = """
    entities:
      - name: EmptyEntity
        fields: []
    """
    file_path = tmp_path / "entity_no_fields.yaml"
    file_path.write_text(content, encoding="utf-8")
    return file_path


def test_load_entities_success(valid_entities_yaml):
    """
    Test loading a valid entities YAML file.

    Verifies:
      - Returns a dict containing a non-empty 'entities' list.
      - The first entity has correct 'name' and 'fields' entries.

    Args:
        valid_entities_yaml (Path): Path to a valid entities YAML file.
    """
    data = load_entities(valid_entities_yaml)
    assert isinstance(data, dict)
    assert "entities" in data
    assert isinstance(data["entities"], list)
    first_entity = data["entities"][0]
    assert first_entity["name"] == "User"
    assert isinstance(first_entity["fields"], list)
    assert first_entity["fields"][0]["name"] == "id"
    assert first_entity["fields"][0]["type"] == "uuid"


def test_load_entities_file_not_found():
    """
    Test that load_entities raises FileNotFoundError when the file does not exist.

    Attempts to load from a non-existent path and expects FileNotFoundError.
    """
    fake_path = Path("/does/not/exist/entities.yaml")
    with pytest.raises(FileNotFoundError) as exc_info:
        load_entities(fake_path)
    assert "Entities file not found" in str(exc_info.value)


def test_load_entities_missing_key(missing_entities_key):
    """
    Test that load_entities raises ValueError for a YAML missing the 'entities' key.

    Args:
        missing_entities_key (Path): Path to a YAML file lacking the 'entities' key.
    """
    with pytest.raises(ValueError) as exc_info:
        load_entities(missing_entities_key)
    msg = str(exc_info.value)
    assert "Field required" in msg and "entities" in msg


def test_load_entities_entities_not_list(entities_not_list):
    """
    Test that load_entities raises ValueError when 'entities' is not a list.

    Args:
        entities_not_list (Path): Path to a YAML file where 'entities' is a string.
    """
    with pytest.raises(ValueError) as exc_info:
        load_entities(entities_not_list)
    msg = str(exc_info.value)
    assert ("Input should be a valid list" in msg or
            "value is not a valid list" in msg or
            "must be a list" in msg)


def test_load_entities_invalid_field_type(invalid_field_type):
    """
    Test that load_entities raises ValueError for an invalid field type in the YAML.

    Args:
        invalid_field_type (Path): Path to a YAML file containing an invalid field type.
    """
    with pytest.raises(ValueError) as exc_info:
        load_entities(invalid_field_type)
    msg = str(exc_info.value)
    assert "Invalid field type 'int32'" in msg


def test_load_entities_entity_with_no_fields(entity_with_no_fields):
    """
    Test that load_entities raises ValueError when an entity has no fields defined.

    Args:
        entity_with_no_fields (Path): Path to a YAML file where an entity's 'fields' list is empty.
    """
    with pytest.raises(ValueError) as exc_info:
        load_entities(entity_with_no_fields)
    msg = str(exc_info.value)
    assert "at least one field defined" in msg
