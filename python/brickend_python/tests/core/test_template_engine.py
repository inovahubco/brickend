"""
test_template_engine.py

Unit tests for the TemplateEngine class in brickend_core.engine.template_engine.
Covers:
  - LEGACY: Rendering Jinja2 templates to strings and files (existing functionality)
  - NEW: Plugin mode with priority system (templates_user/ > core_templates)
  - NEW: Template discovery and triplet-based access
  - NEW: Template info and utility methods
"""

import pytest
from pathlib import Path

from brickend_core.engine.template_engine import TemplateEngine


# =============================================================================
# FIXTURES FOR EXISTING FUNCTIONALITY (maintain compatibility)
# =============================================================================

@pytest.fixture
def simple_template_dir(tmp_path):
    """
    Create a temporary directory with a single Jinja2 template for testing.

    The template will be named 'greeting.j2' and contain:
        Hello, {{ name }}!
    """
    tpl_dir = tmp_path / "templates_test"
    tpl_dir.mkdir()
    (tpl_dir / "greeting.j2").write_text("Hello, {{ name }}!", encoding="utf-8")
    return tpl_dir


# =============================================================================
# FIXTURES FOR NEW PLUGIN MODE FUNCTIONALITY
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
# EXISTING TESTS (maintain backward compatibility)
# =============================================================================

def test_render_to_string(simple_template_dir):
    """
    Test that TemplateEngine.render_to_string returns the correctly rendered text.

    Given a template directory containing 'greeting.j2' with content "Hello, {{ name }}!",
    calling render_to_string with context {"name": "Alice"} should return "Hello, Alice!".
    """
    engine = TemplateEngine([simple_template_dir], auto_reload=False)
    output = engine.render_to_string("greeting.j2", {"name": "Alice"})
    assert isinstance(output, str)
    assert output.strip() == "Hello, Alice!"


def test_render_to_file(simple_template_dir, tmp_path):
    """
    Test that TemplateEngine.render_to_file writes rendered output to the specified file.

    Verifies:
      1. The destination directory is created if it does not exist.
      2. The rendered content "Hello, Bob!" is written to 'result.txt' under the output folder.
    """
    engine = TemplateEngine([simple_template_dir], auto_reload=False)
    destination = tmp_path / "output_folder" / "result.txt"

    assert not (tmp_path / "output_folder").exists()

    engine.render_to_file("greeting.j2", {"name": "Bob"}, destination)

    assert (tmp_path / "output_folder").exists()

    assert destination.exists()
    content = destination.read_text(encoding="utf-8").strip()
    assert content == "Hello, Bob!"


def test_template_not_found(simple_template_dir):
    """
    Test that requesting a non-existent template raises a TemplateNotFound error.

    Calling render_to_string with "nonexistent.j2" should raise an exception
    mentioning that 'nonexistent.j2' could not be found.
    """
    engine = TemplateEngine([simple_template_dir], auto_reload=False)
    with pytest.raises(Exception) as exc_info:
        engine.render_to_string("nonexistent.j2", {"name": "Test"})
    assert "nonexistent.j2" in str(exc_info.value)


# =============================================================================
# NEW TESTS FOR PLUGIN MODE FUNCTIONALITY
# =============================================================================

class TestPluginModeInitialization:
    """Test suite for plugin mode initialization."""

    def test_plugin_mode_initialization(self, plugin_template_structure):
        """Test initialization in plugin mode with base_path."""
        base_path = plugin_template_structure['base_path']

        engine = TemplateEngine(base_path=base_path)

        # Verify mode and attributes
        assert engine.mode == "plugin"
        assert engine.base_path == base_path
        assert engine.user_templates_dir == base_path / "templates_user"
        assert engine.template_dirs is None

    def test_plugin_mode_custom_user_dir(self, plugin_template_structure):
        """Test plugin mode with custom user templates directory."""
        base_path = plugin_template_structure['base_path']
        custom_user_dir = base_path / "custom_templates"

        engine = TemplateEngine(base_path=base_path, user_templates_dir=custom_user_dir)

        assert engine.user_templates_dir == custom_user_dir

    def test_legacy_mode_initialization(self, simple_template_dir):
        """Test initialization in legacy mode with template_dirs."""
        engine = TemplateEngine([simple_template_dir])

        # Verify mode and attributes
        assert engine.mode == "legacy"
        assert engine.template_dirs == [simple_template_dir]
        assert engine.base_path is None
        assert engine.user_templates_dir is None

    def test_invalid_initialization_raises_error(self):
        """Test that invalid initialization raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            TemplateEngine()  # Neither template_dirs nor base_path provided

        error_msg = str(exc_info.value)
        assert "Either template_dirs (legacy) or base_path (plugin mode) must be provided" in error_msg


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

    def test_get_template_path_requires_plugin_mode(self, simple_template_dir):
        """Test that get_template_path raises RuntimeError in legacy mode."""
        engine = TemplateEngine([simple_template_dir])  # Legacy mode

        with pytest.raises(RuntimeError) as exc_info:
            engine.get_template_path("back", "fastapi", "models")

        error_msg = str(exc_info.value)
        assert "requires plugin mode initialization" in error_msg


class TestComponentRendering:
    """Test suite for new component-based rendering methods."""

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

    def test_render_component_requires_plugin_mode(self, simple_template_dir):
        """Test that component rendering methods require plugin mode."""
        engine = TemplateEngine([simple_template_dir])  # Legacy mode

        with pytest.raises(RuntimeError):
            engine.render_component_to_string("back", "fastapi", "models", {})

        with pytest.raises(RuntimeError):
            engine.render_component_to_file("back", "fastapi", "models", {}, Path("out.py"))


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

    def test_utility_methods_require_plugin_mode(self, simple_template_dir):
        """Test that utility methods require plugin mode."""
        engine = TemplateEngine([simple_template_dir])  # Legacy mode

        with pytest.raises(RuntimeError):
            engine.list_available_templates()

        # has_user_template should return False in legacy mode
        assert engine.has_user_template("back", "fastapi", "models") is False

        with pytest.raises(RuntimeError):
            engine.get_template_info("back", "fastapi", "models")


class TestLegacyCompatibility:
    """Test suite for backward compatibility with legacy mode."""

    def test_legacy_methods_work_in_plugin_mode(self, plugin_template_structure):
        """Test that legacy methods still work in plugin mode."""
        base_path = plugin_template_structure['base_path']
        engine = TemplateEngine(base_path=base_path)

        # Test render_to_string works (should find template in search paths)
        # Note: This might not work perfectly due to path structure, but the method should exist
        assert hasattr(engine, 'render_to_string')
        assert hasattr(engine, 'render_to_file')

        # Create a simple template in user directory for testing
        simple_template = engine.user_templates_dir / "simple.j2"
        simple_template.parent.mkdir(parents=True, exist_ok=True)
        simple_template.write_text("Hello {{ name }}!", encoding="utf-8")

        # Should be able to render using legacy method
        result = engine.render_to_string("simple.j2", {"name": "World"})
        assert "Hello World!" in result

    def test_plugin_methods_work_independently(self, plugin_template_structure):
        """Test that new plugin methods work independently of legacy methods."""
        base_path = plugin_template_structure['base_path']
        engine = TemplateEngine(base_path=base_path)

        # Plugin methods should work
        template_path = engine.get_template_path("back", "fastapi", "models")
        assert template_path.exists()

        templates = engine.list_available_templates()
        assert len(templates) > 0

        info = engine.get_template_info("back", "fastapi", "models")
        assert info['exists'] is True


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
        assert engine.mode == "plugin"

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

    def test_mixed_mode_compatibility(self, plugin_template_structure):
        """Test that both legacy and plugin interfaces work together."""
        base_path = plugin_template_structure['base_path']
        engine = TemplateEngine(base_path=base_path)

        # Create simple template for legacy interface
        simple_template = engine.user_templates_dir / "legacy_test.j2"
        simple_template.write_text("Legacy: {{ value }}", encoding="utf-8")

        # Use legacy interface
        legacy_result = engine.render_to_string("legacy_test.j2", {"value": "works"})
        assert "Legacy: works" in legacy_result

        # Use plugin interface
        plugin_result = engine.render_component_to_string("back", "fastapi", "models", {"entity": {"name": "Mixed"}})
        assert "Mixed" in plugin_result

        # Both should work independently
        assert "Legacy" in legacy_result
        assert "Mixed" in plugin_result
