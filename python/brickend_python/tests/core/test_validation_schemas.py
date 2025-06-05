"""
test_validation_schemas.py

Unit tests for the Pydantic models in validation_schemas.py, covering:
1. A valid entities structure.
2. Missing required keys.
3. Invalid field type.
4. Entity name or field name format violations.
5. Entities list being empty.
"""

import pytest
from pydantic import ValidationError

from brickend_core.config.validation_schemas import EntitiesFile


def test_valid_entities_file():
    """
    A basic valid EntitiesFile where:
      - One entity named 'User'.
      - Two fields: 'id' (uuid, primary key) and 'email' (string, unique).
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
    When the top-level 'entities' key is missing, Pydantic should raise a ValidationError.
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
    If 'entities' is present but is an empty list, the validator should reject it.
    """
    payload = {"entities": []}

    with pytest.raises(ValidationError) as exc_info:
        EntitiesFile.model_validate(payload)

    assert "must contain at least one entity" in str(exc_info.value)


def test_entity_missing_name():
    """
    If an entity object is missing the 'name' key, Pydantic should raise a ValidationError.
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
    If an entity name does not match the regex, the validator should reject it.
    E.g., starting with a digit or containing invalid characters.
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
    If a field object is missing the 'name' key, Pydantic should raise a ValidationError.
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
    If a field name does not match the regex (e.g. starts with a digit or contains hyphens),
    the validator should reject it.
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
    If a field type is not in ALLOWED_FIELD_TYPES, the validator should reject it.
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
    If an entity has an empty 'fields' list, the validator should reject it.
    """
    payload = {
        "entities": [
            {"name": "EmptyEntity", "fields": []},
        ]
    }
    with pytest.raises(ValidationError) as exc_info:
        EntitiesFile.model_validate(payload)

    assert "must have at least one field defined" in str(exc_info.value)
