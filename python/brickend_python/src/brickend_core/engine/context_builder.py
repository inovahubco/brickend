"""
context_builder.py

ContextBuilder transforms entity definitions into a richer context suitable for rendering Jinja2 templates.
Supports both legacy format (raw dictionaries) and new format (Pydantic EntityConfig objects).
"""

from typing import Any, Dict, List, Union

from brickend_core.utils.naming import (
    to_snake_case,
    to_pascal_case,
    to_kebab_case,
    validate_name,
)

# Import EntityConfig for type checking and new format support
try:
    from brickend_core.config.validation_schemas import EntityConfig, FieldConfig
    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False
    EntityConfig = Any
    FieldConfig = Any

TYPE_MAPPING: Dict[str, str] = {
    "uuid": "UUID",
    "string": "VARCHAR",
    "text": "TEXT",
    "integer": "INTEGER",
    "float": "FLOAT",
    "boolean": "BOOLEAN",
    "datetime": "TIMESTAMP",
}


class ContextBuilder:
    """
    Build a template context from entity definitions.

    Supports both formats:
    - Legacy: Dictionary with {"entities": [...]} structure
    - Modern: List of EntityConfig Pydantic objects

    The generated context includes:
      - A list of entities with name variations and field metadata.
      - The total entity count.
      - Stack-specific extensions for different backends.
    """

    def __init__(self) -> None:
        """Initialize a ContextBuilder instance."""
        pass

    def build_context(self, entities_input: Union[Dict[str, Any], List[EntityConfig], List[Dict[str, Any]]]) -> Dict[str, Any]:
        """
        Generate a context dictionary for code generation templates.

        Args:
            entities_input: One of:
                - Legacy dict: {"entities": [{"name": "User", "fields": [...]}]}
                - Modern list: [EntityConfig(...), EntityConfig(...)]
                - Raw list: [{"name": "User", "fields": [...]}]

        Returns:
            Dict[str, Any]: A context dictionary containing:
                - "entities": List[Dict[str, Any]] with entity metadata
                - "entity_count": Total number of entities
                - Additional context for template rendering

        Raises:
            ValueError: If input format is invalid or validation fails
        """
        # Normalize input to list of entities
        if isinstance(entities_input, dict):
            # Legacy format: {"entities": [...]}
            return self._build_context_legacy(entities_input)
        elif isinstance(entities_input, list):
            if not entities_input:
                # Empty list
                return {"entities": [], "entity_count": 0}

            # Check if it's a list of Pydantic objects or raw dicts
            first_item = entities_input[0]
            if PYDANTIC_AVAILABLE and hasattr(first_item, 'model_dump'):
                # List of EntityConfig objects (modern format)
                return self._build_context_pydantic(entities_input)
            else:
                # List of raw dictionaries
                return self._build_context_raw_list(entities_input)
        else:
            raise ValueError(f"Unsupported entities input type: {type(entities_input)}")

    def _build_context_legacy(self, entities_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Build context from legacy dictionary format (backward compatibility)."""
        raw_entities = entities_dict.get("entities", [])
        if not isinstance(raw_entities, list):
            raise ValueError("Expected 'entities' to be a list.")

        return self._build_context_from_raw_entities(raw_entities)

    def _build_context_pydantic(self, entities: List[EntityConfig]) -> Dict[str, Any]:
        """Build context from Pydantic EntityConfig objects (modern format)."""
        # Convert Pydantic objects to dictionaries for processing
        raw_entities = [entity.model_dump() for entity in entities]

        # Since Pydantic already validated, we can skip most validation
        return self._build_context_from_raw_entities(raw_entities, skip_validation=True)

    def _build_context_raw_list(self, entities: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Build context from list of raw dictionaries."""
        return self._build_context_from_raw_entities(entities)

    def _build_context_from_raw_entities(self, raw_entities: List[Dict[str, Any]], skip_validation: bool = False) -> Dict[str, Any]:
        """
        Core method to build context from raw entity dictionaries.

        Args:
            raw_entities: List of entity dictionaries
            skip_validation: Skip validation if data already validated by Pydantic
        """
        if not skip_validation:
            self._validate_entities(raw_entities)

        entities_context: List[Dict[str, Any]] = []

        for ent in raw_entities:
            entity_context = self._build_entity_context(ent, skip_validation)
            entities_context.append(entity_context)

        # Build final context with additional metadata
        context = {
            "entities": entities_context,
            "entity_count": len(entities_context),
        }

        # Add additional context for templates
        context.update(self._build_additional_context(entities_context))

        return context

    def _validate_entities(self, raw_entities: List[Dict[str, Any]]) -> None:
        """Validate entity list for duplicates and basic structure."""
        seen_entity_names: set = set()
        for ent in raw_entities:
            ent_name = ent.get("name")
            if ent_name in seen_entity_names:
                raise ValueError(f"Duplicate entity name detected: '{ent_name}'")
            seen_entity_names.add(ent_name)

    def _build_entity_context(self, ent: Dict[str, Any], skip_validation: bool = False) -> Dict[str, Any]:
        """Build context for a single entity."""
        original_ent_name = ent.get("name")

        if not skip_validation and not validate_name(original_ent_name):
            raise ValueError(
                f"Invalid entity name '{original_ent_name}'. "
                "Must start with a letter and contain only letters, digits, or underscores."
            )

        # Generate name variations
        ent_snake = to_snake_case(original_ent_name)
        ent_pascal = to_pascal_case(original_ent_name)
        ent_kebab = to_kebab_case(original_ent_name)

        fields = ent.get("fields", [])
        if not isinstance(fields, list):
            raise ValueError(f"Expected 'fields' for entity '{original_ent_name}' to be a list.")

        # Build fields context
        fields_context, primary_keys = self._build_fields_context(
            fields, original_ent_name, skip_validation
        )

        if not skip_validation and not primary_keys:
            raise ValueError(
                f"Entity '{original_ent_name}' does not have any field marked as primary_key."
            )

        # Build entity context with additional metadata
        entity_context = {
            "original_name": original_ent_name,
            "names": {
                "snake": ent_snake,
                "pascal": ent_pascal,
                "kebab": ent_kebab,
            },
            "fields": fields_context,
            "primary_key_field": primary_keys[0] if len(primary_keys) == 1 else primary_keys,
            "field_count": len(fields_context),
            # Additional metadata for templates
            "table_name": ent_snake,  # Default table name
            "class_name": ent_pascal,  # Default class name
            "has_relationships": any(f.get("foreign_key") for f in fields_context),
            "required_fields": [f for f in fields_context if not f["is_nullable"] and not f["is_primary_key"]],
            "optional_fields": [f for f in fields_context if f["is_nullable"] and not f["is_primary_key"]],
            "unique_fields": [f for f in fields_context if f["is_unique"]],
        }

        return entity_context

    def _build_fields_context(
        self,
        fields: List[Dict[str, Any]],
        entity_name: str,
        skip_validation: bool = False
    ) -> tuple[List[Dict[str, Any]], List[str]]:
        """Build context for entity fields."""
        if not skip_validation:
            self._validate_fields(fields, entity_name)

        fields_context: List[Dict[str, Any]] = []
        primary_keys: List[str] = []

        for fld in fields:
            field_context = self._build_field_context(fld, entity_name, skip_validation)
            fields_context.append(field_context)

            if field_context["is_primary_key"]:
                primary_keys.append(field_context["names"]["snake"])

        return fields_context, primary_keys

    def _validate_fields(self, fields: List[Dict[str, Any]], entity_name: str) -> None:
        """Validate fields for duplicates."""
        seen_field_names: set = set()
        for fld in fields:
            fld_name = fld.get("name")
            if fld_name in seen_field_names:
                raise ValueError(
                    f"Duplicate field name '{fld_name}' in entity '{entity_name}'"
                )
            seen_field_names.add(fld_name)

    def _build_field_context(
        self,
        fld: Dict[str, Any],
        entity_name: str,
        skip_validation: bool = False
    ) -> Dict[str, Any]:
        """Build context for a single field."""
        original_field_name = fld.get("name")

        if not skip_validation and not validate_name(original_field_name):
            raise ValueError(
                f"Invalid field name '{original_field_name}' in entity '{entity_name}'. "
                "Must start with a letter and contain only letters, digits, or underscores."
            )

        # Generate name variations
        fld_snake = to_snake_case(original_field_name)
        fld_pascal = to_pascal_case(original_field_name)
        fld_kebab = to_kebab_case(original_field_name)

        fld_type = fld.get("type")
        if not skip_validation and fld_type not in TYPE_MAPPING:
            raise ValueError(
                f"Unknown field type '{fld_type}' for field '{original_field_name}' "
                f"in entity '{entity_name}'."
            )

        fld_sql_type = TYPE_MAPPING.get(fld_type, "VARCHAR")

        # Extract field properties
        is_primary_key: bool = bool(fld.get("primary_key", False))
        is_unique: bool = bool(fld.get("unique", False))
        is_nullable: bool = bool(fld.get("nullable", True))
        default_val = fld.get("default")
        foreign_key = fld.get("foreign_key")
        constraints = fld.get("constraints", [])

        # Build field context with additional metadata
        field_context = {
            "original_name": original_field_name,
            "names": {
                "snake": fld_snake,
                "pascal": fld_pascal,
                "kebab": fld_kebab,
            },
            "type": fld_type,
            "sql_type": fld_sql_type,
            "is_primary_key": is_primary_key,
            "is_unique": is_unique,
            "is_nullable": is_nullable,
            "default": default_val,
            "foreign_key": foreign_key,
            "constraints": constraints.copy() if isinstance(constraints, list) else [],
            # Additional metadata for templates
            "is_required": not is_nullable and not is_primary_key,
            "has_default": default_val is not None,
            "is_relationship": foreign_key is not None,
            "python_type": self._get_python_type(fld_type, is_nullable),
            "typescript_type": self._get_typescript_type(fld_type, is_nullable),
        }

        return field_context

    def _get_python_type(self, field_type: str, is_nullable: bool) -> str:
        """Get Python type annotation for field."""
        type_mapping = {
            "uuid": "UUID",
            "string": "str",
            "text": "str",
            "integer": "int",
            "float": "float",
            "boolean": "bool",
            "datetime": "datetime",
        }

        base_type = type_mapping.get(field_type, "str")
        return f"Optional[{base_type}]" if is_nullable else base_type

    def _get_typescript_type(self, field_type: str, is_nullable: bool) -> str:
        """Get TypeScript type for field."""
        type_mapping = {
            "uuid": "string",
            "string": "string",
            "text": "string",
            "integer": "number",
            "float": "number",
            "boolean": "boolean",
            "datetime": "Date",
        }

        base_type = type_mapping.get(field_type, "string")
        return f"{base_type} | null" if is_nullable else base_type

    def _build_additional_context(self, entities_context: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Build additional context metadata for templates."""
        return {
            # Summary statistics
            "has_entities": len(entities_context) > 0,
            "total_fields": sum(e["field_count"] for e in entities_context),
            "entities_with_relationships": [
                e for e in entities_context if e["has_relationships"]
            ],

            # Import helpers
            "needs_uuid_import": any(
                any(f["type"] == "uuid" for f in e["fields"])
                for e in entities_context
            ),
            "needs_datetime_import": any(
                any(f["type"] == "datetime" for f in e["fields"])
                for e in entities_context
            ),

            # Entity lists for different use cases
            "entity_names": [e["names"]["snake"] for e in entities_context],
            "entity_classes": [e["names"]["pascal"] for e in entities_context],
            "table_names": [e["table_name"] for e in entities_context],
        }


class FastAPIContextBuilder(ContextBuilder):
    """
    Specialized ContextBuilder for FastAPI projects.
    Adds FastAPI-specific context and metadata.
    """

    def _build_additional_context(self, entities_context: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Build FastAPI-specific additional context."""
        base_context = super()._build_additional_context(entities_context)

        # FastAPI-specific context
        fastapi_context = {
            # Router information
            "router_tags": [e["names"]["kebab"] for e in entities_context],
            "api_routes": [f"/{e['names']['kebab']}" for e in entities_context],

            # Schema information
            "create_schemas": [f"{e['names']['pascal']}Create" for e in entities_context],
            "update_schemas": [f"{e['names']['pascal']}Update" for e in entities_context],
            "response_schemas": [f"{e['names']['pascal']}Response" for e in entities_context],

            # CRUD information
            "crud_classes": [f"{e['names']['pascal']}CRUD" for e in entities_context],
        }

        base_context.update(fastapi_context)
        return base_context


class DjangoContextBuilder(ContextBuilder):
    """
    Specialized ContextBuilder for Django projects.
    Adds Django-specific context and metadata.
    """

    def _build_additional_context(self, entities_context: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Build Django-specific additional context."""
        base_context = super()._build_additional_context(entities_context)

        # Django-specific context
        django_context = {
            # Model information
            "model_classes": [f"{e['names']['pascal']}" for e in entities_context],
            "app_name": "core",  # Default app name

            # Admin information
            "admin_classes": [f"{e['names']['pascal']}Admin" for e in entities_context],

            # Serializer information
            "serializer_classes": [f"{e['names']['pascal']}Serializer" for e in entities_context],

            # ViewSet information
            "viewset_classes": [f"{e['names']['pascal']}ViewSet" for e in entities_context],

            # URL patterns
            "url_patterns": [e['names']['kebab'] for e in entities_context],
        }

        base_context.update(django_context)
        return base_context
