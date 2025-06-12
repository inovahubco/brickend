"""
validation_schemas.py

Defines Pydantic models for validating the structure of an entities.yaml file.
Each entity must have a valid name and a list of fields. Each field must
include a valid type and optional flags (primary_key, unique, nullable, etc.).
"""

import re
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


ALLOWED_FIELD_TYPES = {
    "uuid",
    "string",
    "text",
    "integer",
    "float",
    "boolean",
    "datetime",
}


class FieldConfig(BaseModel):
    """Represents a single field in an entity definition."""

    name: str
    type: str
    primary_key: Optional[bool] = False
    unique: Optional[bool] = False
    nullable: Optional[bool] = True
    default: Optional[str] = None
    foreign_key: Optional[str] = None
    constraints: Optional[List[str]] = Field(default_factory=list)

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        """Ensure that `type` is one of the allowed field types."""
        if v not in ALLOWED_FIELD_TYPES:
            allowed = ", ".join(sorted(ALLOWED_FIELD_TYPES))
            raise ValueError(f"Invalid field type '{v}'. Must be one of: {allowed}")
        return v

    @field_validator("name")
    @classmethod
    def validate_field_name(cls, v: str) -> str:
        """Ensure `name` follows snake_case: starts with a letter, uses letters, digits, or underscores."""
        if not re.match(r"^[A-Za-z][A-Za-z0-9_]*$", v):
            raise ValueError(
                "Field name must start with a letter and contain only letters, digits, or underscores."
            )
        return v


class EntityConfig(BaseModel):
    """Represents a single entity definition with a name and its fields."""

    name: str
    fields: List[FieldConfig]

    @field_validator("name")
    @classmethod
    def validate_entity_name(cls, v: str) -> str:
        """Ensure `name` follows PascalCase or CamelCase: starts with a letter, uses letters, digits, or underscores."""
        if not re.match(r"^[A-Za-z][A-Za-z0-9_]*$", v):
            raise ValueError(
                "Entity name must start with a letter and contain only letters, digits, or underscores."
            )
        return v

    @field_validator("fields")
    @classmethod
    def validate_fields_non_empty(cls, v: List[FieldConfig]) -> List[FieldConfig]:
        """Ensure that at least one field is defined for the entity."""
        if not v:
            raise ValueError("Each entity must have at least one field defined.")
        return v


class EntitiesFile(BaseModel):
    """Represents the top-level structure of the entities file, requiring at least one entity."""

    entities: List[EntityConfig]

    @field_validator("entities")
    @classmethod
    def validate_entities_non_empty(cls, v: List[EntityConfig]) -> List[EntityConfig]:
        """Ensure that the `entities` list contains at least one entity."""
        if not v:
            raise ValueError("The 'entities' list must contain at least one entity.")
        return v
