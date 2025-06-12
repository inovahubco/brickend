"""
test_context_builder.py

Unit tests for ContextBuilder in brickend_core.engine.context_builder.
Covers:
  - Successful context creation for a valid single entity with two fields.
  - Invalid entity name format triggers ValueError.
  - Entity without a primary key triggers ValueError.
  - Duplicate entity names triggers ValueError.
  - Duplicate field names within an entity triggers ValueError.
"""

import pytest

from brickend_core.engine.context_builder import ContextBuilder


def make_simple_entities_dict() -> dict:
    """
    Helper to create a valid entities dictionary for testing.

    Creates:
      - One entity named 'User'.
      - Two fields:
          * 'id': type 'uuid', primary_key=True, unique=False, nullable=False.
          * 'email': type 'string', primary_key=False, unique=True, nullable=False.

    Returns:
        dict: Dictionary representing the entities configuration.
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
    Test successful context creation for a valid single entity with two fields.

    Verifies:
      - 'entities' and 'entity_count' keys in the returned context.
      - Correct naming variations (snake, pascal, kebab) for the entity.
      - Field count and primary_key_field value.
      - Each field's metadata, including SQL type and flags (is_primary_key, is_unique, is_nullable).
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
    Test that ContextBuilder.build_context raises ValueError on invalid entity name.

    Scenario:
      - Entity name starts with a digit ('123Invalid'), which violates naming rules.
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
    Test that ContextBuilder.build_context raises ValueError when no field is marked as primary_key.

    Scenario:
      - Entity has fields defined but none with primary_key=True.
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
    Test that ContextBuilder.build_context raises ValueError on duplicate entity names.

    Scenario:
      - Two entities share the same 'name' value.
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
    Test that ContextBuilder.build_context raises ValueError on duplicate field names within an entity.

    Scenario:
      - An entity defines two fields with identical 'name' values.
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
