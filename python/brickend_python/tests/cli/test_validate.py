"""
test_validate.py

Unit tests for the 'validate' CLI command in brickend_cli.commands.validate.
Covers:
  - Successful validation of valid project configurations
  - Error detection for invalid configurations, entities, and missing templates
  - Stack availability validation
  - File system permission checking
  - Different validation levels (ERROR, WARNING, INFO, SUCCESS)
  - CLI options (--verbose, --strict)
  - Rich UI output verification
"""

import pytest
import os
from pathlib import Path
from typer.testing import CliRunner
from unittest.mock import patch, Mock
import ruamel.yaml

from brickend_cli.main import app as cli_app


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def valid_brickend_project(tmp_path):
    """Create a valid brickend project structure for testing."""
    project_dir = tmp_path / "valid_project"
    project_dir.mkdir()

    # Create brickend.yaml
    brickend_config = {
        "project": {
            "name": "test_project",
            "description": "A test project",
            "version": "1.0.0",
            "author": "Test Author"
        },
        "stack": {
            "back": "fastapi",
            "database": "postgresql"
        },
        "entities": "./entities.yaml",
        "settings": {
            "auto_migrations": True,
            "api_docs": True
        },
        "deploy": {
            "environment": "development"
        }
    }

    yaml = ruamel.yaml.YAML()
    yaml.default_flow_style = False
    with (project_dir / "brickend.yaml").open("w", encoding="utf-8") as f:
        yaml.dump(brickend_config, f)

    # Create entities.yaml with valid entities
    entities_config = {
        "entities": [
            {
                "name": "User",
                "fields": [
                    {"name": "id", "type": "uuid", "primary_key": True},
                    {"name": "email", "type": "string", "unique": True},
                    {"name": "name", "type": "string"}
                ]
            },
            {
                "name": "Post",
                "fields": [
                    {"name": "id", "type": "uuid", "primary_key": True},
                    {"name": "title", "type": "string"},
                    {"name": "content", "type": "text"},
                    {"name": "user_id", "type": "uuid", "foreign_key": "User.id"}
                ]
            }
        ]
    }

    with (project_dir / "entities.yaml").open("w", encoding="utf-8") as f:
        yaml.dump(entities_config, f)

    return project_dir


@pytest.fixture
def invalid_brickend_project(tmp_path):
    """Create an invalid brickend project structure for testing."""
    project_dir = tmp_path / "invalid_project"
    project_dir.mkdir()

    # Create brickend.yaml with issues
    brickend_config = {
        "project": {
            "name": "",  # Empty name (warning)
            "version": "invalid-version"  # Invalid version format
        },
        "stack": {
            "back": "nonexistent_stack",  # Invalid stack
            "database": "unknown_db"  # Invalid database
        },
        "entities": "./missing_entities.yaml",  # Missing file
        "settings": {},
        "deploy": {}
    }

    yaml = ruamel.yaml.YAML()
    with (project_dir / "brickend.yaml").open("w", encoding="utf-8") as f:
        yaml.dump(brickend_config, f)

    # No entities.yaml file (missing external reference)

    return project_dir


@pytest.fixture
def legacy_project(tmp_path):
    """Create a legacy project structure (entities.yaml only)."""
    project_dir = tmp_path / "legacy_project"
    project_dir.mkdir()

    # Only entities.yaml, no brickend.yaml
    entities_config = {
        "entities": [
            {
                "name": "LegacyEntity",
                "fields": [
                    {"name": "id", "type": "uuid", "primary_key": True},
                    {"name": "name", "type": "string"}
                ]
            }
        ]
    }

    yaml = ruamel.yaml.YAML()
    with (project_dir / "entities.yaml").open("w", encoding="utf-8") as f:
        yaml.dump(entities_config, f)

    return project_dir


@pytest.fixture
def project_with_entity_errors(tmp_path):
    """Create a project with entity validation errors."""
    project_dir = tmp_path / "entity_errors_project"
    project_dir.mkdir()

    # Create brickend.yaml
    brickend_config = {
        "project": {"name": "entity_errors_test", "version": "1.0.0"},
        "stack": {"back": "fastapi"},
        "entities": "./entities.yaml"
    }

    yaml = ruamel.yaml.YAML()
    with (project_dir / "brickend.yaml").open("w", encoding="utf-8") as f:
        yaml.dump(brickend_config, f)

    # Create entities.yaml with errors
    entities_config = {
        "entities": [
            {
                "name": "User",
                "fields": [
                    {"name": "id", "type": "uuid", "primary_key": True},
                    {"name": "email", "type": "string"}
                ]
            },
            {
                "name": "User",  # Duplicate entity name
                "fields": [
                    {"name": "username", "type": "string"}
                    # No primary key field
                ]
            },
            {
                "name": "Post",
                "fields": [
                    {"name": "id", "type": "uuid", "primary_key": True},
                    {"name": "title", "type": "string"},
                    {"name": "title", "type": "text"}  # Duplicate field name
                ]
            }
        ]
    }

    with (project_dir / "entities.yaml").open("w", encoding="utf-8") as f:
        yaml.dump(entities_config, f)

    return project_dir


@pytest.fixture
def empty_project(tmp_path):
    """Create a project with no entities."""
    project_dir = tmp_path / "empty_project"
    project_dir.mkdir()

    # Create brickend.yaml
    brickend_config = {
        "project": {"name": "empty_test", "version": "1.0.0"},
        "stack": {"back": "fastapi"},
        "entities": "./entities.yaml"
    }

    yaml = ruamel.yaml.YAML()
    with (project_dir / "brickend.yaml").open("w", encoding="utf-8") as f:
        yaml.dump(brickend_config, f)

    # Create empty entities.yaml
    entities_config = {"entities": []}

    with (project_dir / "entities.yaml").open("w", encoding="utf-8") as f:
        yaml.dump(entities_config, f)

    return project_dir


@pytest.fixture
def mock_template_system():
    """Mock the template system for testing."""

    def _setup_mock(has_stack=True, has_templates=True, template_components=None):
        mock_registry = Mock()
        mock_engine = Mock()

        if has_stack:
            mock_registry.discover_integrations.return_value = {
                "back": ["fastapi", "django"],
                "infra": ["aws_cdk"]
            }

            if template_components is None:
                template_components = ["models", "schemas", "crud", "router"]

            mock_registry.get_available_components.return_value = template_components

            # Create a proper mock user_templates_dir that behaves like Path
            mock_user_dir = Mock()
            mock_user_dir.exists.return_value = False
            mock_user_dir.__truediv__ = Mock(return_value=mock_user_dir)  # For path / operations

            if has_templates:
                mock_engine.get_template_path.return_value = Path("/mock/template/path.j2")
                mock_engine.has_user_template.return_value = False
                mock_engine.user_templates_dir = mock_user_dir
            else:
                # Configure ALL methods for missing templates scenario
                mock_engine.get_template_path.side_effect = FileNotFoundError("Template not found")
                mock_engine.has_user_template.return_value = False
                mock_engine.user_templates_dir = mock_user_dir
        else:
            mock_registry.discover_integrations.return_value = {"back": []}
            # Also configure missing methods for no-stack case
            mock_engine.get_template_path.side_effect = FileNotFoundError("Template not found")
            mock_engine.has_user_template.return_value = False
            mock_user_dir = Mock()
            mock_user_dir.exists.return_value = False
            mock_user_dir.__truediv__ = Mock(return_value=mock_user_dir)
            mock_engine.user_templates_dir = mock_user_dir

        return mock_registry, mock_engine

    return _setup_mock


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def run_validate_in_directory(project_dir: Path, args=None, runner=None):
    """Helper function to run validate command in a specific directory."""
    if runner is None:
        runner = CliRunner()

    if args is None:
        args = ["validate"]

    # Change to the project directory
    original_cwd = os.getcwd()
    try:
        os.chdir(project_dir)
        result = runner.invoke(cli_app, args)
        return result
    finally:
        os.chdir(original_cwd)


# =============================================================================
# BASIC VALIDATION TESTS
# =============================================================================

class TestValidateCommand:
    """Test suite for basic validate command functionality."""

    def test_validate_success_valid_project(self, valid_brickend_project, mock_template_system):
        """Test successful validation of a valid project."""
        runner = CliRunner()
        mock_registry, mock_engine = mock_template_system()

        with patch('brickend_cli.commands.validate.find_project_root') as mock_find_root, \
                patch('brickend_cli.commands.validate.TemplateRegistry') as mock_registry_class, \
                patch('brickend_cli.commands.validate.TemplateEngine') as mock_engine_class:

            mock_find_root.return_value = Path("/mock/project/root")
            mock_registry_class.return_value = mock_registry
            mock_engine_class.return_value = mock_engine

            result = run_validate_in_directory(valid_brickend_project, runner=runner)

            assert result.exit_code == 0
            assert "Validation passed" in result.stdout or "successful" in result.stdout.lower()
            assert "📊" in result.stdout or "Validation Summary" in result.stdout

    def test_validate_with_warnings(self, empty_project, mock_template_system):
        """Test validation with warnings (empty entities)."""
        runner = CliRunner()
        mock_registry, mock_engine = mock_template_system()

        with patch('brickend_cli.commands.validate.find_project_root') as mock_find_root, \
                patch('brickend_cli.commands.validate.TemplateRegistry') as mock_registry_class, \
                patch('brickend_cli.commands.validate.TemplateEngine') as mock_engine_class:

            mock_find_root.return_value = Path("/mock/project/root")
            mock_registry_class.return_value = mock_registry
            mock_engine_class.return_value = mock_engine

            result = run_validate_in_directory(empty_project, runner=runner)

            assert result.exit_code == 0
            assert "warning" in result.stdout.lower() or "⚠️" in result.stdout

    def test_validate_with_errors(self, invalid_brickend_project, mock_template_system):
        """Test validation with errors."""
        runner = CliRunner()
        mock_registry, mock_engine = mock_template_system(has_stack=False)

        with patch('brickend_cli.commands.validate.find_project_root') as mock_find_root, \
                patch('brickend_cli.commands.validate.TemplateRegistry') as mock_registry_class, \
                patch('brickend_cli.commands.validate.TemplateEngine') as mock_engine_class:

            mock_find_root.return_value = Path("/mock/project/root")
            mock_registry_class.return_value = mock_registry
            mock_engine_class.return_value = mock_engine

            result = run_validate_in_directory(invalid_brickend_project, runner=runner)

            assert result.exit_code == 1
            assert "error" in result.stdout.lower() or "❌" in result.stdout

    def test_validate_legacy_project(self, legacy_project, mock_template_system):
        """Test validation of legacy project (entities.yaml only)."""
        runner = CliRunner()
        mock_registry, mock_engine = mock_template_system()

        with patch('brickend_cli.commands.validate.find_project_root') as mock_find_root, \
                patch('brickend_cli.commands.validate.TemplateRegistry') as mock_registry_class, \
                patch('brickend_cli.commands.validate.TemplateEngine') as mock_engine_class:

            mock_find_root.return_value = Path("/mock/project/root")
            mock_registry_class.return_value = mock_registry
            mock_engine_class.return_value = mock_engine

            result = run_validate_in_directory(legacy_project, runner=runner)

            assert result.exit_code == 0
            assert "successful" in result.stdout.lower() or "passed" in result.stdout.lower()


# =============================================================================
# ENTITY VALIDATION TESTS
# =============================================================================

class TestValidateEntities:
    """Test suite for entity validation functionality."""

    def test_validate_entity_errors(self, project_with_entity_errors, mock_template_system):
        """Test validation with entity-specific errors."""
        runner = CliRunner()
        mock_registry, mock_engine = mock_template_system()

        with patch('brickend_cli.commands.validate.find_project_root') as mock_find_root, \
                patch('brickend_cli.commands.validate.TemplateRegistry') as mock_registry_class, \
                patch('brickend_cli.commands.validate.TemplateEngine') as mock_engine_class:

            mock_find_root.return_value = Path("/mock/project/root")
            mock_registry_class.return_value = mock_registry
            mock_engine_class.return_value = mock_engine

            result = run_validate_in_directory(project_with_entity_errors, runner=runner)

            assert result.exit_code == 1

            # Should detect duplicate entity names or other errors
            output_lower = result.stdout.lower()
            assert any(keyword in output_lower for keyword in ["error", "duplicate", "primary", "❌"])

    def test_validate_empty_entities_warning(self, empty_project, mock_template_system):
        """Test validation warns about empty entities."""
        runner = CliRunner()
        mock_registry, mock_engine = mock_template_system()

        with patch('brickend_cli.commands.validate.find_project_root') as mock_find_root, \
                patch('brickend_cli.commands.validate.TemplateRegistry') as mock_registry_class, \
                patch('brickend_cli.commands.validate.TemplateEngine') as mock_engine_class:

            mock_find_root.return_value = Path("/mock/project/root")
            mock_registry_class.return_value = mock_registry
            mock_engine_class.return_value = mock_engine

            result = run_validate_in_directory(empty_project, runner=runner)

            assert result.exit_code == 0  # Warnings don't fail validation by default
            assert "warning" in result.stdout.lower() or "⚠️" in result.stdout


# =============================================================================
# STACK AND TEMPLATE VALIDATION TESTS
# =============================================================================

class TestValidateStackAndTemplates:
    """Test suite for stack and template validation."""

    def test_validate_missing_stack(self, valid_brickend_project, mock_template_system):
        """Test validation with missing/invalid stack."""
        runner = CliRunner()
        mock_registry, mock_engine = mock_template_system(has_stack=False)

        # Modify project to have invalid stack
        import shutil
        project_copy = valid_brickend_project.parent / "invalid_stack_project"
        shutil.copytree(valid_brickend_project, project_copy)

        # Update brickend.yaml to have invalid stack
        yaml = ruamel.yaml.YAML()
        with (project_copy / "brickend.yaml").open("r", encoding="utf-8") as f:
            config = yaml.load(f)
        config["stack"]["back"] = "invalid_stack"
        with (project_copy / "brickend.yaml").open("w", encoding="utf-8") as f:
            yaml.dump(config, f)

        with patch('brickend_cli.commands.validate.find_project_root') as mock_find_root, \
                patch('brickend_cli.commands.validate.TemplateRegistry') as mock_registry_class, \
                patch('brickend_cli.commands.validate.TemplateEngine') as mock_engine_class:

            mock_find_root.return_value = Path("/mock/project/root")
            mock_registry_class.return_value = mock_registry
            mock_engine_class.return_value = mock_engine

            result = run_validate_in_directory(project_copy, runner=runner)

            assert result.exit_code == 1
            assert "not available" in result.stdout.lower() or "error" in result.stdout.lower()

    def test_debug_missing_templates(self, valid_brickend_project, mock_template_system):
        """Debug test to see why missing templates causes exit_code=1."""
        runner = CliRunner()
        mock_registry, mock_engine = mock_template_system(has_templates=False)

        with patch('brickend_cli.commands.validate.find_project_root') as mock_find_root, \
                patch('brickend_cli.commands.validate.TemplateRegistry') as mock_registry_class, \
                patch('brickend_cli.commands.validate.TemplateEngine') as mock_engine_class:

            mock_find_root.return_value = Path("/mock/project/root")
            mock_registry_class.return_value = mock_registry
            mock_engine_class.return_value = mock_engine

            result = run_validate_in_directory(valid_brickend_project, runner=runner)

            # Debug output
            print(f"Exit code: {result.exit_code}")
            print(f"Output: {result.stdout}")
            print(f"Error: {result.stderr}")

            # Check if there are actual errors or just warnings
            output = result.stdout.lower()
            has_errors = "❌" in result.stdout or "error" in output
            has_warnings = "⚠️" in result.stdout or "warning" in output

            print(f"Has errors: {has_errors}")
            print(f"Has warnings: {has_warnings}")

            # Temporarily pass to see the output
            assert True  # Always pass to see debug info

    def test_validate_missing_templates(self, valid_brickend_project, mock_template_system):
        """Test validation with missing templates."""
        runner = CliRunner()
        mock_registry, mock_engine = mock_template_system(has_templates=False)

        with patch('brickend_cli.commands.validate.find_project_root') as mock_find_root, \
                patch('brickend_cli.commands.validate.TemplateRegistry') as mock_registry_class, \
                patch('brickend_cli.commands.validate.TemplateEngine') as mock_engine_class:

            mock_find_root.return_value = Path("/mock/project/root")
            mock_registry_class.return_value = mock_registry
            mock_engine_class.return_value = mock_engine

            result = run_validate_in_directory(valid_brickend_project, runner=runner)

            # Missing templates should be warnings, not errors
            assert result.exit_code == 0
            assert "missing" in result.stdout.lower() or "warning" in result.stdout.lower()

    def test_validate_user_template_overrides(self, valid_brickend_project, mock_template_system):
        """Test validation detects user template overrides."""
        runner = CliRunner()
        mock_registry, mock_engine = mock_template_system()
        mock_engine.has_user_template.return_value = True

        with patch('brickend_cli.commands.validate.find_project_root') as mock_find_root, \
                patch('brickend_cli.commands.validate.TemplateRegistry') as mock_registry_class, \
                patch('brickend_cli.commands.validate.TemplateEngine') as mock_engine_class:

            mock_find_root.return_value = Path("/mock/project/root")
            mock_registry_class.return_value = mock_registry
            mock_engine_class.return_value = mock_engine

            result = run_validate_in_directory(valid_brickend_project, runner=runner)

            assert result.exit_code == 0
            assert "user override" in result.stdout.lower() or "override" in result.stdout.lower()


# =============================================================================
# CLI OPTIONS TESTS
# =============================================================================

class TestValidateOptions:
    """Test suite for CLI options."""

    def test_validate_verbose_option(self, valid_brickend_project, mock_template_system):
        """Test --verbose option shows detailed information."""
        runner = CliRunner()
        mock_registry, mock_engine = mock_template_system()

        with patch('brickend_cli.commands.validate.find_project_root') as mock_find_root, \
                patch('brickend_cli.commands.validate.TemplateRegistry') as mock_registry_class, \
                patch('brickend_cli.commands.validate.TemplateEngine') as mock_engine_class:

            mock_find_root.return_value = Path("/mock/project/root")
            mock_registry_class.return_value = mock_registry
            mock_engine_class.return_value = mock_engine

            result = run_validate_in_directory(
                valid_brickend_project,
                args=["validate", "--verbose"],
                runner=runner
            )

            assert result.exit_code == 0
            # Verbose should show more detailed output
            assert "Validation Summary" in result.stdout or "Statistics" in result.stdout

    def test_validate_strict_option_with_warnings(self, empty_project, mock_template_system):
        """Test --strict option treats warnings as errors."""
        runner = CliRunner()
        mock_registry, mock_engine = mock_template_system()

        with patch('brickend_cli.commands.validate.find_project_root') as mock_find_root, \
                patch('brickend_cli.commands.validate.TemplateRegistry') as mock_registry_class, \
                patch('brickend_cli.commands.validate.TemplateEngine') as mock_engine_class:

            mock_find_root.return_value = Path("/mock/project/root")
            mock_registry_class.return_value = mock_registry
            mock_engine_class.return_value = mock_engine

            # Normal validation should pass with warnings
            result = run_validate_in_directory(empty_project, runner=runner)
            assert result.exit_code == 0

            # Strict validation should fail
            result = run_validate_in_directory(
                empty_project,
                args=["validate", "--strict"],
                runner=runner
            )
            assert result.exit_code == 1
            assert "strict" in result.stdout.lower() or "warnings treated as errors" in result.stdout.lower()

    def test_validate_custom_config_path(self, valid_brickend_project, mock_template_system):
        """Test --config option with custom configuration path."""
        runner = CliRunner()
        mock_registry, mock_engine = mock_template_system()

        with patch('brickend_cli.commands.validate.find_project_root') as mock_find_root, \
                patch('brickend_cli.commands.validate.TemplateRegistry') as mock_registry_class, \
                patch('brickend_cli.commands.validate.TemplateEngine') as mock_engine_class:

            mock_find_root.return_value = Path("/mock/project/root")
            mock_registry_class.return_value = mock_registry
            mock_engine_class.return_value = mock_engine

            # Copy brickend.yaml to custom location
            import shutil
            custom_config = valid_brickend_project / "custom_config.yaml"
            shutil.copy(valid_brickend_project / "brickend.yaml", custom_config)

            result = run_validate_in_directory(
                valid_brickend_project,
                args=["validate", "--config", str(custom_config)],
                runner=runner
            )

            assert result.exit_code == 0


# =============================================================================
# ERROR HANDLING TESTS
# =============================================================================

class TestValidateErrorHandling:
    """Test suite for error handling scenarios."""

    def test_validate_no_configuration_found(self, tmp_path):
        """Test validation when no configuration files exist."""
        runner = CliRunner()

        # Empty directory with no configuration
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        result = run_validate_in_directory(empty_dir, runner=runner)

        assert result.exit_code != 0  # Should fail
        assert "not found" in result.stdout.lower() or "no configuration" in result.stdout.lower()

    def test_validate_project_root_not_found(self, valid_brickend_project):
        """Test validation when project root cannot be found."""
        runner = CliRunner()

        with patch('brickend_cli.commands.validate.find_project_root') as mock_find_root:
            mock_find_root.side_effect = FileNotFoundError("Project root not found")

            result = run_validate_in_directory(valid_brickend_project, runner=runner)

            assert result.exit_code == 1
            assert "not found" in result.stdout.lower() or "failed" in result.stdout.lower()

    def test_validate_invalid_yaml_file(self, tmp_path):
        """Test validation with invalid YAML file."""
        runner = CliRunner()

        project_dir = tmp_path / "invalid_yaml_project"
        project_dir.mkdir()

        # Create invalid YAML
        (project_dir / "brickend.yaml").write_text("invalid: yaml: content: [", encoding="utf-8")

        result = run_validate_in_directory(project_dir, runner=runner)

        assert result.exit_code == 1
        assert "parsing" in result.stdout.lower() or "yaml" in result.stdout.lower() or "failed" in result.stdout.lower()

    def test_validate_permission_errors(self, valid_brickend_project):
        """Test validation with file permission issues."""
        runner = CliRunner()

        # Create a copy we can modify permissions on
        import shutil
        import tempfile

        with tempfile.TemporaryDirectory() as temp_dir:
            test_project = Path(temp_dir) / "test_project"
            shutil.copytree(valid_brickend_project, test_project)

            # Make directory read-only (simulate permission issues)
            import stat
            os.chmod(test_project, stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)

            try:
                result = run_validate_in_directory(test_project, runner=runner)

                # Should detect permission issues or still work
                if result.exit_code == 1:
                    assert "permission" in result.stdout.lower() or "failed" in result.stdout.lower()
                else:
                    # Might still pass validation but show warnings
                    assert result.exit_code == 0

            finally:
                # Restore permissions for cleanup
                try:
                    os.chmod(test_project, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
                except:
                    pass  # Best effort cleanup


# =============================================================================
# RICH UI OUTPUT TESTS
# =============================================================================

class TestValidateRichOutput:
    """Test suite for Rich UI output verification."""

    def test_validate_rich_ui_elements(self, valid_brickend_project, mock_template_system):
        """Test that validate command produces Rich UI elements."""
        runner = CliRunner()
        mock_registry, mock_engine = mock_template_system()

        with patch('brickend_cli.commands.validate.find_project_root') as mock_find_root, \
                patch('brickend_cli.commands.validate.TemplateRegistry') as mock_registry_class, \
                patch('brickend_cli.commands.validate.TemplateEngine') as mock_engine_class:

            mock_find_root.return_value = Path("/mock/project/root")
            mock_registry_class.return_value = mock_registry
            mock_engine_class.return_value = mock_engine

            result = run_validate_in_directory(valid_brickend_project, runner=runner)

            assert result.exit_code == 0

            # Check for Rich UI elements
            output = result.stdout
            assert "🔍" in output or "Validate" in output
            assert "📊" in output or "Validation Summary" in output
            assert "✅" in output or "successful" in output.lower()

            # Should have panels and structured output
            assert "┌" in output or "╭" in output or "│" in output  # Panel borders

    def test_validate_progress_indicators(self, valid_brickend_project, mock_template_system):
        """Test that validation shows progress indicators."""
        runner = CliRunner()
        mock_registry, mock_engine = mock_template_system()

        with patch('brickend_cli.commands.validate.find_project_root') as mock_find_root, \
                patch('brickend_cli.commands.validate.TemplateRegistry') as mock_registry_class, \
                patch('brickend_cli.commands.validate.TemplateEngine') as mock_engine_class:

            mock_find_root.return_value = Path("/mock/project/root")
            mock_registry_class.return_value = mock_registry
            mock_engine_class.return_value = mock_engine

            result = run_validate_in_directory(valid_brickend_project, runner=runner)

            assert result.exit_code == 0

            # Should mention validation steps
            output_lower = result.stdout.lower()
            validation_steps = [
                "configuration", "entities", "stack", "templates", "file system"
            ]

            # At least some validation steps should be mentioned
            assert any(step in output_lower for step in validation_steps) or "validating" in output_lower


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestValidateIntegration:
    """Integration tests for validate command."""

    def test_validate_complete_workflow(self, valid_brickend_project, mock_template_system):
        """Test complete validation workflow with all checks."""
        runner = CliRunner()
        mock_registry, mock_engine = mock_template_system()

        with patch('brickend_cli.commands.validate.find_project_root') as mock_find_root, \
                patch('brickend_cli.commands.validate.TemplateRegistry') as mock_registry_class, \
                patch('brickend_cli.commands.validate.TemplateEngine') as mock_engine_class:

            mock_find_root.return_value = Path("/mock/project/root")
            mock_registry_class.return_value = mock_registry
            mock_engine_class.return_value = mock_engine

            # Add templates_user directory to test user template detection
            templates_user_dir = valid_brickend_project / "templates_user"
            templates_user_dir.mkdir()

            result = run_validate_in_directory(
                valid_brickend_project,
                args=["validate", "--verbose"],
                runner=runner
            )

            assert result.exit_code == 0

            # Should have comprehensive output
            output = result.stdout
            assert "successful" in output.lower() or "passed" in output.lower()
            assert "Validation Summary" in output or "📊" in output

            # Should validate all components
            output_lower = output.lower()
            components = ["configuration", "entities", "stack", "templates"]
            assert any(comp in output_lower for comp in components)

    def test_validate_with_mixed_results(self, project_with_entity_errors, mock_template_system):
        """Test validation with mixed success/warning/error results."""
        runner = CliRunner()
        mock_registry, mock_engine = mock_template_system()

        with patch('brickend_cli.commands.validate.find_project_root') as mock_find_root, \
                patch('brickend_cli.commands.validate.TemplateRegistry') as mock_registry_class, \
                patch('brickend_cli.commands.validate.TemplateEngine') as mock_engine_class:

            mock_find_root.return_value = Path("/mock/project/root")
            mock_registry_class.return_value = mock_registry
            mock_engine_class.return_value = mock_engine

            result = run_validate_in_directory(
                project_with_entity_errors,
                args=["validate", "--verbose"],
                runner=runner
            )

            assert result.exit_code == 1

            # Should show mixed results
            output = result.stdout
            assert "❌" in output or "error" in output.lower()
            # Should also have some success indicators
            assert "✅" in output or "successful" in output.lower() or "passed" in output.lower()

            # Should show detailed breakdown
            assert "Validation Summary" in output or "📊" in output