"""
test_template_engine.py

Unit tests for the TemplateEngine class in brickend_core.engine.template_engine.
Covers:
  - Plugin mode with priority system (templates_user/ > core_templates)
  - Template discovery and triplet-based access
  - Component rendering and template info methods
  - Error handling and edge cases
"""

import pytest
from pathlib import Path

from brickend_core.engine.template_engine import TemplateEngine


# =============================================================================
# FIXTURES FOR PLUGIN MODE FUNCTIONALITY
# =============================================================================

@pytest.fixture
def plugin_template_structure(tmp_path):
    """
    Create a complete plugin-style template structure with core and user templates.

    Structure:
        tmp_path/
        ├── integrations/           # Core templates
        │   ├── back/
        │   │   ├── fastapi/
        │   │   │   ├── models_template.j2
        │   │   │   ├── schemas_template.j2
        │   │   │   └── router_template.j2
        │   │   └── django/
        │   │       ├── models_template.j2
        │   │       └── serializers_template.j2
        │   └── infra/
        │       └── aws_cdk/
        │           └── stack_template.j2
        └── templates_user/         # User override templates
            └── back/
                └── fastapi/
                    └── models_template.j2  # Overrides core template

    Returns:
        Dict with base_path, user_templates_dir, and template contents for testing
    """
    base_path = tmp_path

    # Create core integrations structure
    integrations_dir = base_path / "integrations"

    # FastAPI core templates
    fastapi_dir = integrations_dir / "back" / "fastapi"
    fastapi_dir.mkdir(parents=True)

    (fastapi_dir / "models_template.j2").write_text(
        "# Core FastAPI Models\nclass {{ entity.name }}(BaseModel):\n    pass",
        encoding="utf-8"
    )
    (fastapi_dir / "schemas_template.j2").write_text(
        "# Core FastAPI Schemas\nclass {{ entity.name }}Schema(BaseModel):\n    pass",
        encoding="utf-8"
    )
    (fastapi_dir / "router_template.j2").write_text(
        "# Core FastAPI Router\nrouter = APIRouter()",
        encoding="utf-8"
    )

    # Django core templates
    django_dir = integrations_dir / "back" / "django"
    django_dir.mkdir(parents=True)

    (django_dir / "models_template.j2").write_text(
        "# Core Django Models\nclass {{ entity.name }}(models.Model):\n    pass",
        encoding="utf-8"
    )
    (django_dir / "serializers_template.j2").write_text(
        "# Core Django Serializers\nclass {{ entity.name }}Serializer(serializers.ModelSerializer):\n    pass",
        encoding="utf-8"
    )

    # AWS CDK core templates
    aws_cdk_dir = integrations_dir / "infra" / "aws_cdk"
    aws_cdk_dir.mkdir(parents=True)

    (aws_cdk_dir / "stack_template.j2").write_text(
        "# Core AWS CDK Stack\nclass {{ project.name }}Stack(Stack):\n    pass",
        encoding="utf-8"
    )

    # Create user override templates
    user_templates_dir = base_path / "templates_user"
    user_fastapi_dir = user_templates_dir / "back" / "fastapi"
    user_fastapi_dir.mkdir(parents=True)

    # User override for FastAPI models (higher priority)
    (user_fastapi_dir / "models_template.j2").write_text(
        "# USER OVERRIDE FastAPI Models\nclass {{ entity.name }}(CustomBaseModel):\n    pass",
        encoding="utf-8"
    )

    return {
        'base_path': base_path,
        'user_templates_dir': user_templates_dir,
        'core_content': "# Core FastAPI Models",
        'user_content': "# USER OVERRIDE FastAPI Models",
    }


@pytest.fixture
def plugin_structure_no_user_templates(tmp_path):
    """
    Create plugin structure with only core templates (no user overrides).
    """
    base_path = tmp_path

    # Create only core templates
    fastapi_dir = base_path / "integrations" / "back" / "fastapi"
    fastapi_dir.mkdir(parents=True)

    (fastapi_dir / "models_template.j2").write_text(
        "# Core Only Template\nclass {{ entity.name }}(BaseModel):\n    pass",
        encoding="utf-8"
    )

    return base_path


@pytest.fixture
def empty_plugin_structure(tmp_path):
    """
    Create minimal plugin structure for testing edge cases.
    """
    base_path = tmp_path
    # Create empty integrations directory
    (base_path / "integrations").mkdir()
    return base_path


# =============================================================================
# PLUGIN MODE INITIALIZATION TESTS
# =============================================================================

class TestPluginModeInitialization:
    """Test suite for plugin mode initialization."""

    def test_plugin_mode_initialization(self, plugin_template_structure):
        """Test initialization in plugin mode with base_path."""
        base_path = plugin_template_structure['base_path']

        engine = TemplateEngine(base_path=base_path)

        # Verify attributes
        assert engine.base_path == base_path
        assert engine.user_templates_dir == base_path / "templates_user"

    def test_plugin_mode_custom_user_dir(self, plugin_template_structure):
        """Test plugin mode with custom user templates directory."""
        base_path = plugin_template_structure['base_path']
        custom_user_dir = base_path / "custom_templates"

        engine = TemplateEngine(base_path=base_path, user_templates_dir=custom_user_dir)

        assert engine.user_templates_dir == custom_user_dir

    def test_initialization_with_auto_reload(self, plugin_template_structure):
        """Test initialization with auto_reload option."""
        base_path = plugin_template_structure['base_path']

        engine = TemplateEngine(base_path=base_path, auto_reload=True)

        assert engine.auto_reload is True
        assert engine.env.auto_reload is True


class TestTemplatePriority:
    """Test suite for template priority system (templates_user/ > core)."""

    def test_user_template_priority(self, plugin_template_structure):
        """Test that templates_user/ templates have priority over core templates."""
        base_path = plugin_template_structure['base_path']
        engine = TemplateEngine(base_path=base_path)

        # Get template path - should return user template (higher priority)
        template_path = engine.get_template_path("back", "fastapi", "models")

        # Verify it's the user template, not core
        assert "templates_user" in str(template_path)
        assert template_path.exists()

        # Verify content is from user template
        content = template_path.read_text(encoding="utf-8")
        assert "USER OVERRIDE" in content

    def test_fallback_to_core_template(self, plugin_template_structure):
        """Test fallback to core template when user template doesn't exist."""
        base_path = plugin_template_structure['base_path']
        engine = TemplateEngine(base_path=base_path)

        # Request template that only exists in core (schemas)
        template_path = engine.get_template_path("back", "fastapi", "schemas")

        # Verify it's the core template
        assert "integrations" in str(template_path)
        assert "templates_user" not in str(template_path)
        assert template_path.exists()

        # Verify content is from core template
        content = template_path.read_text(encoding="utf-8")
        assert "Core FastAPI Schemas" in content

    def test_get_template_path_missing_raises_error(self, plugin_template_structure):
        """Test that get_template_path raises FileNotFoundError for missing templates."""
        base_path = plugin_template_structure['base_path']
        engine = TemplateEngine(base_path=base_path)

        with pytest.raises(FileNotFoundError) as exc_info:
            engine.get_template_path("back", "nonexistent", "models")

        error_msg = str(exc_info.value)
        assert "Template not found: back/nonexistent/models" in error_msg
        assert "Searched in:" in error_msg


class TestComponentRendering:
    """Test suite for component-based rendering methods."""

    def test_render_component_to_string(self, plugin_template_structure):
        """Test render_component_to_string method."""
        base_path = plugin_template_structure['base_path']
        engine = TemplateEngine(base_path=base_path)

        context = {"entity": {"name": "TestEntity"}}
        result = engine.render_component_to_string("back", "fastapi", "models", context)

        assert isinstance(result, str)
        assert "USER OVERRIDE" in result  # Should use user template
        assert "TestEntity" in result

    def test_render_component_to_file(self, plugin_template_structure, tmp_path):
        """Test render_component_to_file method."""
        base_path = plugin_template_structure['base_path']
        engine = TemplateEngine(base_path=base_path)

        context = {"entity": {"name": "FileEntity"}}
        destination = tmp_path / "output" / "models.py"

        engine.render_component_to_file("back", "fastapi", "models", context, destination)

        # Verify file was created
        assert destination.exists()

        # Verify content
        content = destination.read_text(encoding="utf-8")
        assert "USER OVERRIDE" in content
        assert "FileEntity" in content

    def test_render_template_by_path(self, plugin_template_structure):
        """Test render_template_by_path method."""
        base_path = plugin_template_structure['base_path']
        engine = TemplateEngine(base_path=base_path)

        # Get template path and render directly
        template_path = engine.get_template_path("back", "fastapi", "schemas")
        context = {"entity": {"name": "DirectEntity"}}

        result = engine.render_template_by_path(template_path, context)

        assert isinstance(result, str)
        assert "Core FastAPI Schemas" in result
        assert "DirectEntity" in result

    def test_basic_render_methods_still_work(self, plugin_template_structure):
        """Test that basic render_to_string and render_to_file methods still work."""
        base_path = plugin_template_structure['base_path']
        engine = TemplateEngine(base_path=base_path)

        # Create a simple template in user directory for testing
        simple_template = engine.user_templates_dir / "simple.j2"
        simple_template.parent.mkdir(parents=True, exist_ok=True)
        simple_template.write_text("Hello {{ name }}!", encoding="utf-8")

        # Should be able to render using basic method
        result = engine.render_to_string("simple.j2", {"name": "World"})
        assert "Hello World!" in result

    def test_render_to_file_basic(self, plugin_template_structure, tmp_path):
        """Test basic render_to_file method."""
        base_path = plugin_template_structure['base_path']
        engine = TemplateEngine(base_path=base_path)

        # Create a simple template
        simple_template = engine.user_templates_dir / "file_test.j2"
        simple_template.parent.mkdir(parents=True, exist_ok=True)
        simple_template.write_text("Content: {{ content }}", encoding="utf-8")

        destination = tmp_path / "output" / "test.txt"

        engine.render_to_file("file_test.j2", {"content": "test data"}, destination)

        # Verify file was created and has correct content
        assert destination.exists()
        content = destination.read_text(encoding="utf-8")
        assert "Content: test data" in content


class TestTemplateDiscovery:
    """Test suite for template discovery and utility methods."""

    def test_list_available_templates(self, plugin_template_structure):
        """Test list_available_templates method."""
        base_path = plugin_template_structure['base_path']
        engine = TemplateEngine(base_path=base_path)

        templates = engine.list_available_templates()

        # Verify structure
        assert "back" in templates
        assert "infra" in templates

        # Verify stacks
        assert "fastapi" in templates["back"]
        assert "django" in templates["back"]
        assert "aws_cdk" in templates["infra"]

        # Verify components
        fastapi_components = templates["back"]["fastapi"]
        assert "models" in fastapi_components
        assert "schemas" in fastapi_components
        assert "router" in fastapi_components

    def test_list_available_templates_filtered(self, plugin_template_structure):
        """Test list_available_templates with category filter."""
        base_path = plugin_template_structure['base_path']
        engine = TemplateEngine(base_path=base_path)

        # Filter by category
        back_templates = engine.list_available_templates(category="back")

        assert "back" in back_templates
        assert "infra" not in back_templates

        # Filter by category and stack
        fastapi_templates = engine.list_available_templates(category="back", stack="fastapi")

        assert "back" in fastapi_templates
        assert "fastapi" in fastapi_templates["back"]
        assert "django" not in fastapi_templates["back"]

    def test_has_user_template(self, plugin_template_structure):
        """Test has_user_template method."""
        base_path = plugin_template_structure['base_path']
        engine = TemplateEngine(base_path=base_path)

        # Should have user template for models
        assert engine.has_user_template("back", "fastapi", "models") is True

        # Should not have user template for schemas (only core)
        assert engine.has_user_template("back", "fastapi", "schemas") is False

        # Should not have user template for non-existent
        assert engine.has_user_template("back", "fastapi", "nonexistent") is False

    def test_get_template_info(self, plugin_template_structure):
        """Test get_template_info method."""
        base_path = plugin_template_structure['base_path']
        engine = TemplateEngine(base_path=base_path)

        # User template info (higher priority)
        user_info = engine.get_template_info("back", "fastapi", "models")
        assert user_info['exists'] is True
        assert user_info['source'] == 'user'
        assert user_info['priority'] == 1
        assert "templates_user" in str(user_info['path'])

        # Core template info (fallback)
        core_info = engine.get_template_info("back", "fastapi", "schemas")
        assert core_info['exists'] is True
        assert core_info['source'] == 'core'
        assert core_info['priority'] == 2
        assert "integrations" in str(core_info['path'])

        # Non-existent template info
        missing_info = engine.get_template_info("back", "fastapi", "nonexistent")
        assert missing_info['exists'] is False
        assert missing_info['source'] is None
        assert missing_info['priority'] is None
        assert missing_info['path'] is None


class TestErrorHandling:
    """Test suite for comprehensive error handling."""

    def test_render_template_by_path_missing_file(self, plugin_template_structure):
        """Test error when template file doesn't exist."""
        base_path = plugin_template_structure['base_path']
        engine = TemplateEngine(base_path=base_path)

        missing_path = base_path / "nonexistent.j2"

        with pytest.raises(FileNotFoundError) as exc_info:
            engine.render_template_by_path(missing_path, {})

        assert "Template file not found" in str(exc_info.value)

    def test_empty_plugin_structure(self, empty_plugin_structure):
        """Test behavior with empty plugin structure."""
        engine = TemplateEngine(base_path=empty_plugin_structure)

        # Should initialize without error
        assert engine.base_path == empty_plugin_structure

        # Should return empty results for discovery
        templates = engine.list_available_templates()
        assert templates == {}

        # Should raise error for missing templates
        with pytest.raises(FileNotFoundError):
            engine.get_template_path("back", "fastapi", "models")

    def test_template_syntax_errors_propagate(self, plugin_template_structure):
        """Test that Jinja2 syntax errors are properly propagated."""
        base_path = plugin_template_structure['base_path']
        engine = TemplateEngine(base_path=base_path)

        # Create template with syntax error
        bad_template = base_path / "templates_user" / "bad.j2"
        bad_template.parent.mkdir(parents=True, exist_ok=True)
        bad_template.write_text("{{ unclosed", encoding="utf-8")  # Syntax error

        # Should raise an exception (TemplateSyntaxError or similar)
        with pytest.raises(Exception) as exc_info:
            engine.render_to_string("bad.j2", {})

        # Just verify that an exception was raised with a meaningful message
        assert len(str(exc_info.value)) > 0  # Non-empty error message
        # Optionally, check it's a Jinja2 related error
        assert hasattr(exc_info.value, '__class__')

    def test_template_not_found_basic_render(self, plugin_template_structure):
        """Test that requesting a non-existent template raises appropriate error."""
        base_path = plugin_template_structure['base_path']
        engine = TemplateEngine(base_path=base_path)

        with pytest.raises(Exception) as exc_info:
            engine.render_to_string("nonexistent.j2", {"name": "Test"})
        assert "nonexistent.j2" in str(exc_info.value)


class TestAdvancedFeatures:
    """Test suite for advanced template engine features."""

    def test_user_templates_directory_creation(self, plugin_structure_no_user_templates):
        """Test behavior when user templates directory doesn't exist initially."""
        base_path = plugin_structure_no_user_templates

        # User templates directory doesn't exist initially
        user_dir = base_path / "templates_user"
        assert not user_dir.exists()

        engine = TemplateEngine(base_path=base_path, user_templates_dir=user_dir)

        # Should initialize successfully
        assert engine.user_templates_dir == user_dir

        # Should fall back to core templates
        template_path = engine.get_template_path("back", "fastapi", "models")
        assert "integrations" in str(template_path)

        content = template_path.read_text(encoding="utf-8")
        assert "Core Only Template" in content

    def test_relative_user_templates_directory(self, plugin_template_structure):
        """Test initialization with relative user templates directory."""
        base_path = plugin_template_structure['base_path']

        # Use relative path
        relative_user_dir = Path("custom_user_templates")
        engine = TemplateEngine(base_path=base_path, user_templates_dir=relative_user_dir)

        # Should resolve relative to base_path
        expected_path = base_path / relative_user_dir
        assert engine.user_templates_dir == expected_path

    def test_absolute_user_templates_directory(self, plugin_template_structure, tmp_path):
        """Test initialization with absolute user templates directory."""
        base_path = plugin_template_structure['base_path']

        # Use absolute path
        absolute_user_dir = tmp_path / "absolute_user_templates"
        absolute_user_dir.mkdir()

        engine = TemplateEngine(base_path=base_path, user_templates_dir=absolute_user_dir)

        # Should use absolute path as-is
        assert engine.user_templates_dir == absolute_user_dir


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestIntegration:
    """Integration tests combining multiple features."""

    def test_complete_workflow_user_override(self, plugin_template_structure, tmp_path):
        """Test complete workflow: discovery -> template selection -> rendering."""
        base_path = plugin_template_structure['base_path']
        engine = TemplateEngine(base_path=base_path)

        # 1. Discover available templates
        templates = engine.list_available_templates()
        assert "models" in templates["back"]["fastapi"]

        # 2. Check template info
        info = engine.get_template_info("back", "fastapi", "models")
        assert info['source'] == 'user'  # Should use user override

        # 3. Render template
        context = {"entity": {"name": "IntegrationEntity"}}
        result = engine.render_component_to_string("back", "fastapi", "models", context)
        assert "USER OVERRIDE" in result
        assert "IntegrationEntity" in result

        # 4. Render to file
        output_file = tmp_path / "integration_output.py"
        engine.render_component_to_file("back", "fastapi", "models", context, output_file)

        # 5. Verify file output
        assert output_file.exists()
        file_content = output_file.read_text(encoding="utf-8")
        assert "USER OVERRIDE" in file_content
        assert "IntegrationEntity" in file_content

    def test_complete_workflow_core_fallback(self, plugin_template_structure, tmp_path):
        """Test complete workflow using core template (no user override)."""
        base_path = plugin_template_structure['base_path']
        engine = TemplateEngine(base_path=base_path)

        # 1. Check template info - should fall back to core
        info = engine.get_template_info("back", "django", "models")
        assert info['source'] == 'core'

        # 2. Render template
        context = {"entity": {"name": "DjangoEntity"}}
        result = engine.render_component_to_string("back", "django", "models", context)
        assert "Core Django Models" in result
        assert "DjangoEntity" in result

    def test_multiple_stacks_and_categories(self, plugin_template_structure):
        """Test that engine works with multiple stacks and categories."""
        base_path = plugin_template_structure['base_path']
        engine = TemplateEngine(base_path=base_path)

        # Test different backends
        fastapi_result = engine.render_component_to_string(
            "back", "fastapi", "schemas", {"entity": {"name": "FastAPIEntity"}}
        )
        assert "Core FastAPI Schemas" in fastapi_result

        django_result = engine.render_component_to_string(
            "back", "django", "serializers", {"entity": {"name": "DjangoEntity"}}
        )
        assert "Core Django Serializers" in django_result

        # Test infrastructure
        infra_result = engine.render_component_to_string(
            "infra", "aws_cdk", "stack", {"project": {"name": "TestProject"}}
        )
        assert "Core AWS CDK Stack" in infra_result
        assert "TestProject" in infra_result

    def test_template_engine_reusability(self, plugin_template_structure):
        """Test that template engine can be reused for multiple operations."""
        base_path = plugin_template_structure['base_path']
        engine = TemplateEngine(base_path=base_path)

        # Multiple operations with same engine
        for i in range(3):
            context = {"entity": {"name": f"Entity{i}"}}
            result = engine.render_component_to_string("back", "fastapi", "models", context)
            assert f"Entity{i}" in result
            assert "USER OVERRIDE" in result

        # Different templates with same engine
        templates_to_test = [
            ("back", "fastapi", "schemas"),
            ("back", "django", "models"),
            ("infra", "aws_cdk", "stack")
        ]

        for category, stack, component in templates_to_test:
            info = engine.get_template_info(category, stack, component)
            assert info['exists'] is True
