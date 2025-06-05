"""
test_context_builder.py

Unit tests for ContextBuilder in core.engine.context_builder.
Covers:
  1. Successful context creation for a valid single entity with two fields.
  2. Invalid entity name format.
  3. Entity without any primary key.
  4. Duplicate entity names in input.
  5. Duplicate field names within an entity.
"""

import pytest

from brickend_core.engine.context_builder import ContextBuilder


def make_simple_entities_dict() -> dict:
    """
    Helper to create a valid entities_dict for testing:
    - One entity named 'User'
    - Two fields: 'id' (uuid, primary_key=True) and 'email' (string, unique, nullable=False)
    """
    return {
        "entities": [
            {
                "name": "User",
                "fields": [
                    {
                        "name": "id",
                        "type": "uuid",
                        "primary_key": True,
                        "unique": False,
                        "nullable": False,
                        "default": None,
                        "foreign_key": None,
                        "constraints": [],
                    },
                    {
                        "name": "email",
                        "type": "string",
                        "primary_key": False,
                        "unique": True,
                        "nullable": False,
                        "default": None,
                        "foreign_key": None,
                        "constraints": [],
                    },
                ],
            }
        ]
    }


def test_build_context_success():
    """
    Given a valid entities dict with one entity and two fields,
    ContextBuilder.build_context should produce the correct structure.
    """
    builder = ContextBuilder()
    entities_dict = make_simple_entities_dict()

    ctx = builder.build_context(entities_dict)

    assert "entities" in ctx
    assert "entity_count" in ctx
    assert ctx["entity_count"] == 1

    entity_ctx = ctx["entities"][0]
    assert entity_ctx["original_name"] == "User"
    assert entity_ctx["names"]["snake"] == "user"
    assert entity_ctx["names"]["pascal"] == "User"
    assert entity_ctx["names"]["kebab"] == "user"

    assert entity_ctx["field_count"] == 2
    assert entity_ctx["primary_key_field"] == "id"

    fields = entity_ctx["fields"]
    assert len(fields) == 2

    id_field = next(f for f in fields if f["original_name"] == "id")
    assert id_field["names"]["snake"] == "id"
    assert id_field["names"]["pascal"] == "Id"
    assert id_field["names"]["kebab"] == "id"
    assert id_field["type"] == "uuid"
    assert id_field["sql_type"] == "UUID"
    assert id_field["is_primary_key"] is True
    assert id_field["is_unique"] is False
    assert id_field["is_nullable"] is False

    email_field = next(f for f in fields if f["original_name"] == "email")
    assert email_field["names"]["snake"] == "email"
    assert email_field["names"]["pascal"] == "Email"
    assert email_field["names"]["kebab"] == "email"
    assert email_field["type"] == "string"
    assert email_field["sql_type"] == "VARCHAR"
    assert email_field["is_primary_key"] is False
    assert email_field["is_unique"] is True
    assert email_field["is_nullable"] is False


def test_invalid_entity_name():
    """
    If an entity has a name that does not match the regex (e.g., starts with a digit),
    ContextBuilder.build_context should raise a ValueError.
    """
    builder = ContextBuilder()
    bad_entities = {
        "entities": [
            {
                "name": "123Invalid",
                "fields": [
                    {"name": "id", "type": "uuid", "primary_key": True, "unique": False, "nullable": False, "default": None, "foreign_key": None, "constraints": []}
                ],
            }
        ]
    }

    with pytest.raises(ValueError) as exc_info:
        builder.build_context(bad_entities)
    assert "Invalid entity name" in str(exc_info.value)


def test_entity_without_primary_key():
    """
    If an entity has no field marked as primary_key=True, build_context should raise a ValueError.
    """
    builder = ContextBuilder()
    no_pk_entities = {
        "entities": [
            {
                "name": "NoPKEntity",
                "fields": [
                    {"name": "field1", "type": "string", "primary_key": False, "unique": False, "nullable": True, "default": None, "foreign_key": None, "constraints": []}
                ],
            }
        ]
    }

    with pytest.raises(ValueError) as exc_info:
        builder.build_context(no_pk_entities)
    assert "does not have any field marked as primary_key" in str(exc_info.value)


def test_duplicate_entity_names():
    """
    If two entities share the same name, build_context should raise a ValueError.
    """
    builder = ContextBuilder()
    dup_entities = {
        "entities": [
            {
                "name": "Product",
                "fields": [
                    {"name": "id", "type": "uuid", "primary_key": True, "unique": False, "nullable": False, "default": None, "foreign_key": None, "constraints": []}
                ],
            },
            {
                "name": "Product",
                "fields": [
                    {"name": "code", "type": "string", "primary_key": True, "unique": False, "nullable": False, "default": None, "foreign_key": None, "constraints": []}
                ],
            },
        ]
    }

    with pytest.raises(ValueError) as exc_info:
        builder.build_context(dup_entities)
    assert "Duplicate entity name" in str(exc_info.value)


def test_duplicate_field_names_in_entity():
    """
    If an entity has two fields with the same name, build_context should raise a ValueError.
    """
    builder = ContextBuilder()
    dup_field_entities = {
        "entities": [
            {
                "name": "Order",
                "fields": [
                    {"name": "id", "type": "uuid", "primary_key": True, "unique": False, "nullable": False, "default": None, "foreign_key": None, "constraints": []},
                    {"name": "id", "type": "string", "primary_key": False, "unique": True, "nullable": False, "default": None, "foreign_key": None, "constraints": []},
                ],
            }
        ]
    }

    with pytest.raises(ValueError) as exc_info:
        builder.build_context(dup_field_entities)
    assert "Duplicate field name" in str(exc_info.value)
