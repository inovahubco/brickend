"""
test_yaml_loader.py

Unit tests for yaml_loader functions in brickend_core.utils.yaml_loader.
Covers:
  - load_project_config function (hybrid configuration)
  - save_project_config function
  - validate_entities_file_reference utility
"""

import pytest
from pathlib import Path

from brickend_core.utils.yaml_loader import (
    load_project_config,
    save_project_config,
    validate_entities_file_reference
)
from brickend_core.config.project_schema import BrickendProject, ProjectInfo, StackConfig


# =============================================================================
# FIXTURES FOR PROJECT CONFIG FUNCTIONALITY
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


@pytest.fixture
def valid_entities_for_validation(tmp_path):
    """
    Create a valid entities.yaml file for validation testing.

    Returns:
        Path: Path to valid entities.yaml
    """
    content = """
entities:
  - name: TestEntity
    fields:
      - name: id
        type: uuid
        primary_key: true
      - name: name
        type: string
"""

    file_path = tmp_path / "test_entities.yaml"
    file_path.write_text(content, encoding="utf-8")
    return file_path


# =============================================================================
# PROJECT CONFIG TESTS
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

            error_msg = str(exc_info.value).lower()
            assert "configuration" in error_msg
            assert "found" in error_msg

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

    def test_default_brickend_yaml_loading(self, tmp_path):
        """Test loading default brickend.yaml from current directory."""
        # Create brickend.yaml in temp directory
        brickend_content = """
project:
  name: default_project

stack:
  back: fastapi

entities:
  - name: DefaultEntity
    fields:
      - name: id
        type: uuid
        primary_key: true
"""
        brickend_path = tmp_path / "brickend.yaml"
        brickend_path.write_text(brickend_content, encoding="utf-8")

        import os
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)

            # Load without specifying path - should find brickend.yaml in current dir
            config = load_project_config()

            assert config.project.name == "default_project"
            assert len(config.entities) == 1
            assert config.entities[0].name == "DefaultEntity"

        finally:
            os.chdir(original_cwd)


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

    def test_save_with_default_path(self, tmp_path):
        """Test saving with default brickend.yaml path."""
        config = BrickendProject(
            project=ProjectInfo(name="default_save", version="1.0.0"),
            stack=StackConfig(back="django"),
            entities=[]
        )

        import os
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)

            # Save without specifying path
            save_project_config(config)

            # Verify file was created in current directory
            default_path = tmp_path / "brickend.yaml"
            assert default_path.exists()

            # Load and verify
            loaded_config = load_project_config()
            assert loaded_config.project.name == "default_save"

        finally:
            os.chdir(original_cwd)


class TestValidateEntitiesFileReference:
    """Test suite for entities file reference validation."""

    def test_validate_existing_file(self, valid_entities_for_validation):
        """Test validation of existing entities file."""
        resolved_path = validate_entities_file_reference(str(valid_entities_for_validation))
        assert resolved_path.exists()
        assert resolved_path.is_file()

    def test_validate_relative_path(self, valid_entities_for_validation, tmp_path):
        """Test validation with relative path."""
        import os
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)

            # Test relative path
            relative_name = valid_entities_for_validation.name
            resolved_path = validate_entities_file_reference(f"./{relative_name}")
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

    def test_validate_absolute_path(self, valid_entities_for_validation):
        """Test validation with absolute path."""
        absolute_path = str(valid_entities_for_validation.absolute())
        resolved_path = validate_entities_file_reference(absolute_path)
        assert resolved_path.exists()
        assert resolved_path.is_absolute()


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

    def test_external_entities_workflow(self, tmp_path):
        """Test workflow with external entities file management."""
        import os
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)

            # 1. Create brickend.yaml with external entities reference
            brickend_content = """
project:
  name: external_workflow

stack:
  back: fastapi

entities: "./custom_entities.yaml"
"""
            brickend_path = tmp_path / "brickend.yaml"
            brickend_path.write_text(brickend_content, encoding="utf-8")

            # 2. Create entities file
            entities_content = """
entities:
  - name: WorkflowEntity
    fields:
      - name: id
        type: uuid
        primary_key: true
      - name: status
        type: string
"""
            entities_path = tmp_path / "custom_entities.yaml"
            entities_path.write_text(entities_content, encoding="utf-8")

            # 3. Load project config
            config = load_project_config()

            # 4. Verify external entities were loaded
            assert config.project.name == "external_workflow"
            assert len(config.entities) == 1
            assert config.entities[0].name == "WorkflowEntity"

            # 5. Validate entities file reference
            validated_path = validate_entities_file_reference("./custom_entities.yaml")
            assert validated_path.exists()

        finally:
            os.chdir(original_cwd)
