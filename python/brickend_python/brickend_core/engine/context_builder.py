"""
context_builder.py

ContextBuilder transforms a validated entities dictionary into a richer context
suitable for rendering Jinja2 templates.
"""

from typing import Any, Dict, List

from brickend_core.utils.naming import (
    to_snake_case,
    to_pascal_case,
    to_kebab_case,
    validate_name,
)

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
    Build a template context from a validated entities' dictionary.

    The generated context includes:
      - A list of entities with name variations and field metadata.
      - The total entity count.
    """

    def __init__(self) -> None:
        """Initialize a ContextBuilder instance."""
        # No initialization parameters required at this time.
        pass

    def build_context(self, entities_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a context dictionary for code generation templates.

        Args:
            entities_dict (Dict[str, Any]): Dictionary matching the structure of
                EntitiesFile.dict(), e.g.
                {
                    "entities": [
                        { "name": "User", "fields": [ { ... }, ... ] },
                        ...
                    ]
                }

        Returns:
            Dict[str, Any]: A context dictionary containing:
                - "entities": List[Dict[str, Any]] where each dict contains:
                    * original_name (str)
                    * names (dict with snake, pascal, kebab)
                    * fields (list of field metadata dicts)
                    * primary_key_field (str or list of str)
                    * field_count (int)
                - "entity_count": Total number of entities.

        Raises:
            ValueError: If:
                - 'entities' is not a list.
                - Duplicate entity names are found.
                - Entity or field names are invalid.
                - Duplicate field names within an entity are found.
                - An entity has no primary key field.
                - A field type is not recognized in TYPE_MAPPING.
        """
        raw_entities = entities_dict.get("entities", [])
        if not isinstance(raw_entities, list):
            raise ValueError("Expected 'entities' to be a list.")

        seen_entity_names: set = set()
        for ent in raw_entities:
            ent_name = ent.get("name")
            if ent_name in seen_entity_names:
                raise ValueError(f"Duplicate entity name detected: '{ent_name}'")
            seen_entity_names.add(ent_name)

        entities_context: List[Dict[str, Any]] = []

        for ent in raw_entities:
            original_ent_name = ent.get("name")
            if not validate_name(original_ent_name):
                raise ValueError(
                    f"Invalid entity name '{original_ent_name}'. "
                    "Must start with a letter and contain only letters, digits, or underscores."
                )

            ent_snake = to_snake_case(original_ent_name)
            ent_pascal = to_pascal_case(original_ent_name)
            ent_kebab = to_kebab_case(original_ent_name)

            fields = ent.get("fields", [])
            if not isinstance(fields, list):
                raise ValueError(f"Expected 'fields' for entity '{original_ent_name}' to be a list.")

            seen_field_names: set = set()
            for fld in fields:
                fld_name = fld.get("name")
                if fld_name in seen_field_names:
                    raise ValueError(
                        f"Duplicate field name '{fld_name}' in entity '{original_ent_name}'"
                    )
                seen_field_names.add(fld_name)

            fields_context: List[Dict[str, Any]] = []
            primary_keys: List[str] = []

            for fld in fields:
                original_field_name = fld.get("name")
                if not validate_name(original_field_name):
                    raise ValueError(
                        f"Invalid field name '{original_field_name}' in entity '{original_ent_name}'. "
                        "Must start with a letter and contain only letters, digits, or underscores."
                    )

                fld_snake = to_snake_case(original_field_name)
                fld_pascal = to_pascal_case(original_field_name)
                fld_kebab = to_kebab_case(original_field_name)

                fld_type = fld.get("type")
                if fld_type not in TYPE_MAPPING:
                    raise ValueError(
                        f"Unknown field type '{fld_type}' for field '{original_field_name}' "
                        f"in entity '{original_ent_name}'."
                    )
                fld_sql_type = TYPE_MAPPING[fld_type]

                is_primary_key: bool = bool(fld.get("primary_key", False))
                is_unique: bool = bool(fld.get("unique", False))
                is_nullable: bool = bool(fld.get("nullable", True))
                default_val = fld.get("default")
                foreign_key = fld.get("foreign_key")
                constraints = fld.get("constraints", [])

                if is_primary_key:
                    primary_keys.append(fld_snake)

                fields_context.append({
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
                })

            if not primary_keys:
                raise ValueError(
                    f"Entity '{original_ent_name}' does not have any field marked as primary_key."
                )

            entities_context.append({
                "original_name": original_ent_name,
                "names": {
                    "snake": ent_snake,
                    "pascal": ent_pascal,
                    "kebab": ent_kebab,
                },
                "fields": fields_context,
                "primary_key_field": primary_keys[0] if len(primary_keys) == 1 else primary_keys,
                "field_count": len(fields_context),
            })

        return {
            "entities": entities_context,
            "entity_count": len(entities_context),
        }
