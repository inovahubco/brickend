"""
test_yaml_loader.py

Unit tests for yaml_loader functions in brickend_core.utils.yaml_loader.
Covers:
  - LEGACY: load_entities function (existing functionality)
  - NEW: load_project_config function (hybrid configuration)
  - NEW: save_project_config function
  - NEW: validate_entities_file_reference utility
"""

import pytest
from pathlib import Path

from brickend_core.utils.yaml_loader import (
    load_entities,
    load_project_config,
    save_project_config,
    validate_entities_file_reference
)
from brickend_core.config.project_schema import BrickendProject, ProjectInfo, StackConfig


# =============================================================================
# FIXTURES FOR EXISTING FUNCTIONALITY
# =============================================================================

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


# =============================================================================
# FIXTURES FOR NEW PROJECT CONFIG FUNCTIONALITY
# =============================================================================

@pytest.fixture
def brickend_yaml_inline_entities(tmp_path):
    """
    Create a brickend.yaml file with inline entities' configuration.

    Returns:
        Path: Path to brickend.yaml with inline entities
    """
    content = """
project:
  name: test_project
  description: A test project
  version: 1.0.0
  author: Test Author

stack:
  back: fastapi
  database: postgresql
  infra: aws_cdk

entities:
  - name: User
    fields:
      - name: id
        type: uuid
        primary_key: true
      - name: email
        type: string
        unique: true
      - name: name
        type: string
  - name: Post
    fields:
      - name: id
        type: uuid
        primary_key: true
      - name: title
        type: string
      - name: content
        type: text
      - name: user_id
        type: uuid
        foreign_key: User.id

settings:
  auto_migrations: true
  api_docs: true
  cors_enabled: true

deploy:
  environment: development
  region: us-east-1
  monitoring: true
"""

    file_path = tmp_path / "brickend.yaml"
    file_path.write_text(content, encoding="utf-8")
    return file_path


@pytest.fixture
def brickend_yaml_external_entities(tmp_path):
    """
    Create a brickend.yaml file with external entities reference.

    Returns:
        Tuple[Path, Path]: (brickend.yaml path, entities.yaml path)
    """
    # Create brickend.yaml with external reference
    brickend_content = """
project:
  name: external_project
  description: Project with external entities
  version: 2.0.0

stack:
  back: django
  database: mysql

entities: "./entities.yaml"

settings:
  auto_migrations: false
  authentication: true

deploy:
  environment: production
  auto_deploy: true
"""

    # Create entities.yaml
    entities_content = """
entities:
  - name: Product
    fields:
      - name: id
        type: uuid
        primary_key: true
      - name: name
        type: string
      - name: price
        type: float
      - name: description
        type: text
        nullable: true
  - name: Category
    fields:
      - name: id
        type: uuid
        primary_key: true
      - name: name
        type: string
        unique: true
"""

    brickend_path = tmp_path / "brickend.yaml"
    entities_path = tmp_path / "entities.yaml"

    brickend_path.write_text(brickend_content, encoding="utf-8")
    entities_path.write_text(entities_content, encoding="utf-8")

    return brickend_path, entities_path


@pytest.fixture
def legacy_entities_only(tmp_path):
    """
    Create only entities.yaml file (no brickend.yaml) for legacy fallback testing.

    Returns:
        Path: Path to entities.yaml
    """
    content = """
entities:
  - name: LegacyModel
    fields:
      - name: id
        type: uuid
        primary_key: true
      - name: legacy_field
        type: string
"""

    file_path = tmp_path / "entities.yaml"
    file_path.write_text(content, encoding="utf-8")
    return file_path


@pytest.fixture
def brickend_yaml_missing_external_entities(tmp_path):
    """
    Create brickend.yaml that references non-existent entities file.

    Returns:
        Path: Path to brickend.yaml with broken reference
    """
    content = """
project:
  name: broken_project
  
stack:
  back: fastapi
  
entities: "./missing_entities.yaml"
"""

    file_path = tmp_path / "brickend.yaml"
    file_path.write_text(content, encoding="utf-8")
    return file_path


@pytest.fixture
def invalid_brickend_yaml(tmp_path):
    """
    Create an invalid brickend.yaml file for error testing.

    Returns:
        Path: Path to invalid brickend.yaml
    """
    content = """
project:
  name: ""  # Empty name should fail validation
  version: "invalid-version"  # Invalid version format

stack:
  back: invalid_backend  # Invalid backend
  database: unknown_db   # Invalid database

entities: []  # Empty entities should fail

settings:
  auto_migrations: "not_a_boolean"  # Wrong type
"""

    file_path = tmp_path / "brickend.yaml"
    file_path.write_text(content, encoding="utf-8")
    return file_path


# =============================================================================
# EXISTING TESTS (maintain backward compatibility)
# =============================================================================

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


# =============================================================================
# NEW TESTS FOR PROJECT CONFIG (hybrid configuration)
# =============================================================================

class TestProjectConfig:
    """Test suite for project configuration loading functionality."""

    def test_load_brickend_yaml_inline_entities(self, brickend_yaml_inline_entities, tmp_path):
        """Test loading brickend.yaml with inline entities' configuration."""
        # Change to temp directory for relative path resolution
        import os
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)

            config = load_project_config(brickend_yaml_inline_entities)

            # Verify project info
            assert config.project.name == "test_project"
            assert config.project.description == "A test project"
            assert config.project.version == "1.0.0"
            assert config.project.author == "Test Author"

            # Verify stack config
            assert config.stack.back == "fastapi"
            assert config.stack.database == "postgresql"
            assert config.stack.infra == "aws_cdk"

            # Verify entities (should be list, not string)
            assert isinstance(config.entities, list)
            assert len(config.entities) == 2
            assert config.entities[0].name == "User"
            assert config.entities[1].name == "Post"

            # Verify settings
            assert config.settings.auto_migrations is True
            assert config.settings.api_docs is True
            assert config.settings.cors_enabled is True

            # Verify deploy config
            assert config.deploy.environment == "development"
            assert config.deploy.region == "us-east-1"
            assert config.deploy.monitoring is True

            # Verify helper methods
            assert not config.is_entities_external()
            assert config.get_entities_file_path() is None

        finally:
            os.chdir(original_cwd)

    def test_load_brickend_yaml_external_entities(self, brickend_yaml_external_entities, tmp_path):
        """Test loading brickend.yaml with external entities file reference."""
        brickend_path, entities_path = brickend_yaml_external_entities

        import os
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)

            config = load_project_config(brickend_path)

            # Verify project info
            assert config.project.name == "external_project"
            assert config.project.description == "Project with external entities"
            assert config.project.version == "2.0.0"

            # Verify stack config
            assert config.stack.back == "django"
            assert config.stack.database == "mysql"

            # Verify entities were loaded from external file
            assert isinstance(config.entities, list)
            assert len(config.entities) == 2
            assert config.entities[0].name == "Product"
            assert config.entities[1].name == "Category"

            # Verify specific entity fields
            product_entity = config.entities[0]
            assert len(product_entity.fields) == 4
            assert product_entity.fields[0].name == "id"
            assert product_entity.fields[0].type == "uuid"
            assert product_entity.fields[0].primary_key is True

            # Verify settings
            assert config.settings.auto_migrations is False
            assert config.settings.authentication is True

            # Verify deploy config
            assert config.deploy.environment == "production"
            assert config.deploy.auto_deploy is True

        finally:
            os.chdir(original_cwd)

    def test_fallback_to_entities_yaml(self, legacy_entities_only, tmp_path):
        """Test fallback to legacy entities.yaml when brickend.yaml doesn't exist."""
        import os
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)

            # Try to load brickend.yaml (doesn't exist), should fall back to entities.yaml
            config = load_project_config()

            # Verify legacy project defaults
            assert config.project.name == "legacy_project"
            assert config.project.description == "Legacy project migrated from entities.yaml"
            assert config.project.version == "1.0.0"

            # Verify default stack config
            assert config.stack.back == "fastapi"
            assert config.stack.database == "postgresql"

            # Verify entities were loaded from legacy file
            assert isinstance(config.entities, list)
            assert len(config.entities) == 1
            assert config.entities[0].name == "LegacyModel"

            # Verify default settings
            assert config.settings.auto_migrations is True
            assert config.settings.api_docs is True

        finally:
            os.chdir(original_cwd)

    def test_missing_entities_file_raises_error(self, brickend_yaml_missing_external_entities, tmp_path):
        """Test error when external entities file referenced in brickend.yaml doesn't exist."""
        import os
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)

            with pytest.raises(FileNotFoundError) as exc_info:
                load_project_config(brickend_yaml_missing_external_entities)

            error_msg = str(exc_info.value)
            assert "External entities file not found" in error_msg
            assert "missing_entities.yaml" in error_msg

        finally:
            os.chdir(original_cwd)

    def test_no_configuration_found_raises_error(self, tmp_path):
        """Test error when neither brickend.yaml nor entities.yaml exist."""
        import os
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)

            with pytest.raises(FileNotFoundError) as exc_info:
                load_project_config()

            error_msg = str(exc_info.value)
            assert "No configuration found" in error_msg
            assert "brickend.yaml" in error_msg
            assert "entities.yaml" in error_msg

        finally:
            os.chdir(original_cwd)

    def test_invalid_brickend_yaml_raises_validation_error(self, invalid_brickend_yaml, tmp_path):
        """Test validation errors in brickend.yaml configuration."""
        import os
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)

            with pytest.raises(ValueError) as exc_info:
                load_project_config(invalid_brickend_yaml)

            error_msg = str(exc_info.value)
            assert "Validation error" in error_msg

        finally:
            os.chdir(original_cwd)

    def test_relative_path_resolution(self, tmp_path):
        """Test that relative paths in entities reference are resolved correctly."""
        # Create nested directory structure
        config_dir = tmp_path / "config"
        config_dir.mkdir()

        # Create brickend.yaml in config/ directory
        brickend_content = """
project:
  name: nested_project

stack:
  back: fastapi

entities: "../entities.yaml"
"""
        brickend_path = config_dir / "brickend.yaml"
        brickend_path.write_text(brickend_content, encoding="utf-8")

        # Create entities.yaml in parent directory
        entities_content = """
entities:
  - name: NestedEntity
    fields:
      - name: id
        type: uuid
        primary_key: true
"""
        entities_path = tmp_path / "entities.yaml"
        entities_path.write_text(entities_content, encoding="utf-8")

        # Load config - should resolve relative path correctly
        config = load_project_config(brickend_path)

        assert config.project.name == "nested_project"
        assert len(config.entities) == 1
        assert config.entities[0].name == "NestedEntity"


class TestSaveProjectConfig:
    """Test suite for saving project configuration."""

    def test_save_project_config_basic(self, tmp_path):
        """Test basic save functionality."""
        # Create a simple config
        config = BrickendProject(
            project=ProjectInfo(name="save_test", version="1.0.0"),
            stack=StackConfig(back="fastapi", database="sqlite"),
            entities=[]
        )

        output_path = tmp_path / "output_brickend.yaml"
        save_project_config(config, output_path)

        # Verify file was created
        assert output_path.exists()

        # Verify content by loading it back
        loaded_config = load_project_config(output_path)
        assert loaded_config.project.name == "save_test"
        assert loaded_config.stack.back == "fastapi"
        assert loaded_config.stack.database == "sqlite"

    def test_save_preserves_structure(self, brickend_yaml_inline_entities, tmp_path):
        """Test that save preserves complex configuration structure."""
        import os
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)

            # Load complex config
            original_config = load_project_config(brickend_yaml_inline_entities)

            # Save to new location
            output_path = tmp_path / "saved_config.yaml"
            save_project_config(original_config, output_path)

            # Load saved config
            loaded_config = load_project_config(output_path)

            # Verify everything matches
            assert loaded_config.project.name == original_config.project.name
            assert loaded_config.stack.back == original_config.stack.back
            assert len(loaded_config.entities) == len(original_config.entities)
            assert loaded_config.settings.auto_migrations == original_config.settings.auto_migrations

        finally:
            os.chdir(original_cwd)


class TestValidateEntitiesFileReference:
    """Test suite for entities file reference validation."""

    def test_validate_existing_file(self, valid_entities_yaml):
        """Test validation of existing entities file."""
        resolved_path = validate_entities_file_reference(str(valid_entities_yaml))
        assert resolved_path.exists()
        assert resolved_path.is_file()

    def test_validate_relative_path(self, tmp_path):
        """Test validation with relative path."""
        # Create entities file
        entities_path = tmp_path / "test_entities.yaml"
        entities_path.write_text("entities: []", encoding="utf-8")

        import os
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)

            # Test relative path
            resolved_path = validate_entities_file_reference("./test_entities.yaml")
            assert resolved_path.exists()

        finally:
            os.chdir(original_cwd)

    def test_validate_missing_file_raises_error(self):
        """Test error when referenced file doesn't exist."""
        with pytest.raises(FileNotFoundError) as exc_info:
            validate_entities_file_reference("./nonexistent.yaml")

        assert "Entities file not found" in str(exc_info.value)

    def test_validate_empty_reference_raises_error(self):
        """Test error when reference is empty."""
        with pytest.raises(ValueError) as exc_info:
            validate_entities_file_reference("")

        assert "cannot be empty" in str(exc_info.value)

    def test_validate_directory_raises_error(self, tmp_path):
        """Test error when reference points to directory instead of file."""
        test_dir = tmp_path / "test_directory"
        test_dir.mkdir()

        with pytest.raises(ValueError) as exc_info:
            validate_entities_file_reference(str(test_dir))

        assert "must point to a file" in str(exc_info.value)


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestIntegration:
    """Integration tests combining multiple functions."""

    def test_round_trip_save_load(self, tmp_path):
        """Test complete round trip: create config -> save -> load -> verify."""
        from brickend_core.config.validation_schemas import EntityConfig, FieldConfig

        # Create complete configuration
        original_config = BrickendProject(
            project=ProjectInfo(
                name="roundtrip_test",
                description="Integration test project",
                version="2.1.0",
                author="Test Suite"
            ),
            stack=StackConfig(
                back="django",
                database="mysql",
                infra="terraform"
            ),
            entities=[
                EntityConfig(
                    name="TestEntity",
                    fields=[
                        FieldConfig(name="id", type="uuid", primary_key=True),
                        FieldConfig(name="name", type="string", unique=True),
                        FieldConfig(name="created_at", type="datetime")
                    ]
                )
            ]
        )

        # Save configuration
        config_path = tmp_path / "roundtrip.yaml"
        save_project_config(original_config, config_path)

        # Load configuration
        loaded_config = load_project_config(config_path)

        # Verify everything matches
        assert loaded_config.project.name == "roundtrip_test"
        assert loaded_config.project.description == "Integration test project"
        assert loaded_config.project.version == "2.1.0"
        assert loaded_config.project.author == "Test Suite"

        assert loaded_config.stack.back == "django"
        assert loaded_config.stack.database == "mysql"
        assert loaded_config.stack.infra == "terraform"

        assert len(loaded_config.entities) == 1
        entity = loaded_config.entities[0]
        assert entity.name == "TestEntity"
        assert len(entity.fields) == 3
        assert entity.fields[0].name == "id"
        assert entity.fields[0].primary_key is True
