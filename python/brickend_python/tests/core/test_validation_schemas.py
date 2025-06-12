"""
test_validation_schemas.py

Unit tests for the Pydantic models in validation_schemas.py.
Covers:
  - A valid entities structure.
  - Missing required keys.
  - Invalid field type.
  - Entity name or field name format violations.
  - Entities list being empty.
"""

import pytest
from pydantic import ValidationError

from brickend_core.config.validation_schemas import EntitiesFile


def test_valid_entities_file():
    """
    Test successful validation of a basic EntitiesFile payload.

    Verifies:
      - One entity named 'User'.
      - Two fields: 'id' (uuid, primary_key=True) and 'email' (string, unique=True, nullable=False).
    """
    payload = {
        "entities": [
            {
                "name": "User",
                "fields": [
                    {"name": "id", "type": "uuid", "primary_key": True, "nullable": False},
                    {"name": "email", "type": "string", "unique": True, "nullable": False},
                ],
            }
        ]
    }

    ef = EntitiesFile.model_validate(payload)
    assert len(ef.entities) == 1
    entity = ef.entities[0]
    assert entity.name == "User"
    assert entity.fields[0].name == "id"
    assert entity.fields[0].type == "uuid"
    assert entity.fields[1].name == "email"
    assert entity.fields[1].type == "string"


def test_missing_entities_key():
    """
    Test that omission of the top-level 'entities' key raises a ValidationError.

    Verifies error message mentions 'entities' and indicates a missing required field.
    """
    payload = {
        "models": [
            {
                "name": "Product",
                "fields": [{"name": "id", "type": "uuid"}],
            }
        ]
    }

    with pytest.raises(ValidationError) as exc_info:
        EntitiesFile.model_validate(payload)

    assert "Field required" in str(exc_info.value)
    assert "entities" in str(exc_info.value)


def test_empty_entities_list():
    """
    Test that an empty 'entities' list is rejected by the validator.

    Verifies the ValidationError message indicates the list must contain at least one entity.
    """
    payload = {"entities": []}

    with pytest.raises(ValidationError) as exc_info:
        EntitiesFile.model_validate(payload)

    assert "must contain at least one entity" in str(exc_info.value)


def test_entity_missing_name():
    """
    Test that an entity object missing the 'name' key raises a ValidationError.

    Verifies the error message indicates 'name' is required.
    """
    payload = {
        "entities": [
            {
                # "name" is missing here
                "fields": [{"name": "id", "type": "uuid"}],
            }
        ]
    }

    with pytest.raises(ValidationError) as exc_info:
        EntitiesFile.model_validate(payload)

    assert "Field required" in str(exc_info.value)
    assert "name" in str(exc_info.value)


def test_entity_invalid_name_format():
    """
    Test that an entity name violating the naming regex is rejected.

    Scenario:
      - Name starts with a digit ('123Invalid').

    Verifies the error message describes the naming requirement.
    """
    payload = {
        "entities": [
            {
                "name": "123Invalid",
                "fields": [{"name": "id", "type": "uuid"}],
            }
        ]
    }
    with pytest.raises(ValidationError) as exc_info:
        EntitiesFile.model_validate(payload)

    assert "Entity name must start with a letter" in str(exc_info.value)


def test_field_missing_name():
    """
    Test that a field object missing the 'name' key raises a ValidationError.

    Verifies the error message indicates 'name' is required for fields.
    """
    payload = {
        "entities": [
            {
                "name": "Order",
                "fields": [
                    {
                        # 'name' is missing here
                        "type": "uuid"
                    }
                ],
            }
        ]
    }
    with pytest.raises(ValidationError) as exc_info:
        EntitiesFile.model_validate(payload)

    assert "Field required" in str(exc_info.value)
    assert "name" in str(exc_info.value)


def test_field_invalid_name_format():
    """
    Test that a field name violating the naming regex is rejected.

    Scenario:
      - Name starts with a digit ('1st_field').

    Verifies the error message describes the naming requirement for fields.
    """
    payload = {
        "entities": [
            {
                "name": "Invoice",
                "fields": [
                    {"name": "1st_field", "type": "string"}  # invalid: starts with digit
                ],
            }
        ]
    }
    with pytest.raises(ValidationError) as exc_info:
        EntitiesFile.model_validate(payload)

    assert "Field name must start with a letter" in str(exc_info.value)


def test_field_invalid_type():
    """
    Test that a field type not in ALLOWED_FIELD_TYPES is rejected.

    Scenario:
      - Field 'age' with type 'int32'.

    Verifies the error message lists allowed field types.
    """
    payload = {
        "entities": [
            {
                "name": "Customer",
                "fields": [
                    {"name": "id", "type": "uuid"},
                    {"name": "age", "type": "int32"},
                ],
            }
        ]
    }
    with pytest.raises(ValidationError) as exc_info:
        EntitiesFile.model_validate(payload)

    assert "Invalid field type 'int32'" in str(exc_info.value)
    assert "Must be one of" in str(exc_info.value)


def test_entity_with_no_fields():
    """
    Test that an entity with an empty 'fields' list is rejected by the validator.

    Verifies the ValidationError message indicates each entity must have at least one field.
    """
    payload = {
        "entities": [
            {"name": "EmptyEntity", "fields": []},
        ]
    }
    with pytest.raises(ValidationError) as exc_info:
        EntitiesFile.model_validate(payload)

    assert "must have at least one field defined" in str(exc_info.value)
