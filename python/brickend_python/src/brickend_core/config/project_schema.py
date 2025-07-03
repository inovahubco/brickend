"""
project_schema.py

Define Pydantic models for validating the structure of a brickend.yaml file.
Supports hybrid configuration with inline entities or external entities file reference.
"""

import re
from pathlib import Path
from typing import Dict, List, Optional, Union, Any
from pydantic import BaseModel, Field, field_validator

from .validation_schemas import EntityConfig


class ProjectInfo(BaseModel):
    """Represents project metadata and basic information."""

    name: str
    description: Optional[str] = None
    version: str = "1.0.0"
    author: Optional[str] = None
    license: Optional[str] = "MIT"
    repository_url: Optional[str] = None

    @field_validator("name")
    @classmethod
    def validate_project_name(cls, v: str) -> str:
        """Ensure project name follows standard naming conventions."""
        if not re.match(r"^[a-zA-Z][a-zA-Z0-9_-]*$", v):
            raise ValueError(
                "Project name must start with a letter and contain only letters, digits, hyphens, or underscores."
            )
        if len(v) < 2:
            raise ValueError("Project name must be at least 2 characters long.")
        return v

    @field_validator("version")
    @classmethod
    def validate_version_format(cls, v: str) -> str:
        """Ensure version follows semantic versioning pattern (basic validation)."""
        if not re.match(r"^\d+\.\d+\.\d+", v):
            raise ValueError(
                "Version must follow semantic versioning format (e.g., '1.0.0', '1.2.3-beta')."
            )
        return v


class StackConfig(BaseModel):
    """Represents the technology stack configuration for the project."""

    back: str = "fastapi"
    database: Optional[str] = "postgresql"
    infra: Optional[str] = None
    frontend: Optional[str] = None
    cache: Optional[str] = None
    message_queue: Optional[str] = None

    @field_validator("back")
    @classmethod
    def validate_backend_stack(cls, v: str) -> str:
        """Ensure backend stack name is valid."""
        if not re.match(r"^[a-zA-Z][a-zA-Z0-9_-]*$", v):
            raise ValueError(
                "Backend stack name must start with a letter and contain only letters, digits, hyphens, or underscores."
            )
        return v.lower()

    @field_validator("database")
    @classmethod
    def validate_database_type(cls, v: Optional[str]) -> Optional[str]:
        """Ensure database type is valid if specified."""
        if v is None:
            return v

        allowed_databases = {
            "postgresql", "postgres", "mysql", "sqlite", "mongodb", "redis"
        }

        if v.lower() not in allowed_databases:
            allowed = ", ".join(sorted(allowed_databases))
            raise ValueError(f"Invalid database type '{v}'. Must be one of: {allowed}")

        return v.lower()


class DeployConfig(BaseModel):
    """Represents deployment configuration settings."""

    environment: str = "development"
    region: Optional[str] = None
    auto_deploy: bool = False
    monitoring: bool = True
    logging: bool = True
    ssl: bool = True
    custom_domain: Optional[str] = None
    scaling: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """Ensure environment is a valid deployment environment."""
        allowed_envs = {"development", "staging", "production", "test"}
        if v.lower() not in allowed_envs:
            allowed = ", ".join(sorted(allowed_envs))
            raise ValueError(f"Invalid environment '{v}'. Must be one of: {allowed}")
        return v.lower()


class ProjectSettings(BaseModel):
    """Represents project-specific settings and configurations."""

    auto_migrations: bool = True
    api_docs: bool = True
    cors_enabled: bool = True
    rate_limiting: bool = False
    authentication: bool = False
    authorization: bool = False
    file_uploads: bool = False
    email_service: bool = False
    database_url: Optional[str] = None
    custom_middleware: List[str] = Field(default_factory=list)
    feature_flags: Dict[str, bool] = Field(default_factory=dict)
    integrations: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        extra = "allow"

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, v: Optional[str]) -> Optional[str]:
        """Validate database URL format if provided."""
        if v is None:
            return v

        # Basic URL validation
        if not v.strip():
            return None

        # Check common database URL patterns
        url_patterns = [
            r"^sqlite:///.*\.db$",  # SQLite: sqlite:///./test.db
            r"^postgresql://.*",    # PostgreSQL: postgresql://user:pass@host:port/db
            r"^mysql://.*",         # MySQL: mysql://user:pass@host:port/db
            r"^mongodb://.*",       # MongoDB: mongodb://host:port/db
        ]

        url = v.strip()
        if not any(re.match(pattern, url) for pattern in url_patterns):
            raise ValueError(
                "Invalid database URL format. Examples: "
                "'sqlite:///./test.db', 'postgresql://user:pass@host:port/db'"
            )

        return url


class BrickendProject(BaseModel):
    """
    Main configuration model for brickend.yaml file.

    Supports hybrid entities configuration:
    - Inline: entities as a list of EntityConfig objects
    - External: entities as a string path to external entities.yaml file
    """

    project: ProjectInfo
    stack: StackConfig
    entities: Union[List[EntityConfig], str] = Field(
        description="Either inline entities list or path to entities file (e.g., './entities.yaml')"
    )
    settings: ProjectSettings = Field(default_factory=ProjectSettings)
    deploy: DeployConfig = Field(default_factory=DeployConfig)

    # Additional custom sections
    plugins: Dict[str, Any] = Field(default_factory=dict)
    custom: Dict[str, Any] = Field(default_factory=dict)

    # Internal field to track original entities mode
    _original_entities_path: Optional[str] = None

    class Config:
        extra = "allow"
        underscore_attrs_are_private = True

    @field_validator("entities")
    @classmethod
    def validate_entities_configuration(cls, v: Union[List[EntityConfig], str]) -> Union[List[EntityConfig], str]:
        """Validate entities configuration (inline or external file reference)."""
        if isinstance(v, str):
            # External file path validation
            if not v.strip():
                raise ValueError("Entities file path cannot be empty.")

            # Basic path validation (file existence will be checked at load time)
            if not re.match(r"^[./\\]?[\w\-./\\]+\.ya?ml$", v):
                raise ValueError(
                    "Entities file path must be a valid YAML file path (e.g., './entities.yaml', 'config/entities.yml')."
                )

            return v.strip()

        elif isinstance(v, list):
            # Inline entities
            return v

        else:
            raise ValueError(
                "Entities must be either a list of entity configurations or a string path to entities file."
            )

    def is_entities_external(self) -> bool:
        """Check if entities configuration uses external file."""
        return isinstance(self.entities, str)

    def get_entities_file_path(self) -> Optional[Path]:
        """Get Path object for external entities file, or None if inline."""
        if self.is_entities_external():
            return Path(self.entities)
        return None

    def get_entities_list(self) -> List[EntityConfig]:
        """Get entities list (only works for inline configuration)."""
        if not self.is_entities_external():
            return self.entities
        raise ValueError("Cannot get entities list from external file reference. Use load_project_config() instead.")


# Convenience type aliases
EntitiesConfig = Union[List[EntityConfig], str]
ProjectConfigDict = Dict[str, Any]
