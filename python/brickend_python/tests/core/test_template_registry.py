"""
test_template_registry.py

Unit tests for TemplateRegistry in brickend_core.engine.template_registry.
Covers:
  - Plugin discovery and initialization
  - Triplet indexing (category, stack, component)
  - Template access methods
  - Error handling
  - Integration workflows
"""

import pytest
from pathlib import Path

from brickend_core.engine import TemplateRegistry


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def plugin_structure_with_meta(tmp_path):
    """
    Create a complete plugin-style directory structure with meta.yaml files.

    Structure:
      tmp_path/integrations/
      ├── back/
      │   ├── fastapi/
      │   │   ├── meta.yaml
      │   │   ├── models_template.j2
      │   │   ├── schemas_template.j2
      │   │   └── router_template.j2
      │   └── django/
      │       ├── meta.yaml
      │       ├── models_template.j2
      │       └── serializers_template.j2
      └── infra/
          ├── aws_cdk/
          │   ├── meta.yaml
          │   └── stack_template.j2
          └── terraform/
              ├── meta.yaml
              └── main_template.j2

    Args:
        tmp_path (Path): pytest-provided temporary directory.

    Returns:
        Path: Base path for plugin-style TemplateRegistry initialization.
    """
    base = tmp_path

    # Create directory structure
    back_dir = base / "integrations" / "back"
    infra_dir = base / "integrations" / "infra"

    fastapi_dir = back_dir / "fastapi"
    django_dir = back_dir / "django"
    aws_cdk_dir = infra_dir / "aws_cdk"
    terraform_dir = infra_dir / "terraform"

    for dir_path in [fastapi_dir, django_dir, aws_cdk_dir, terraform_dir]:
        dir_path.mkdir(parents=True, exist_ok=True)

    # Create meta.yaml files
    fastapi_meta = """
name: fastapi
category: back
description: "FastAPI framework"
version: "1.0.0"
components: [models, schemas, router]
"""

    django_meta = """
name: django
category: back
description: "Django framework"
version: "0.1.0"
components: [models, serializers]
"""

    aws_cdk_meta = """
name: aws_cdk
category: infra
description: "AWS CDK"
version: "0.1.0"
components: [stack]
"""

    terraform_meta = """
name: terraform
category: infra
description: "Terraform"
version: "0.1.0"
components: [main]
"""

    (fastapi_dir / "meta.yaml").write_text(fastapi_meta, encoding="utf-8")
    (django_dir / "meta.yaml").write_text(django_meta, encoding="utf-8")
    (aws_cdk_dir / "meta.yaml").write_text(aws_cdk_meta, encoding="utf-8")
    (terraform_dir / "meta.yaml").write_text(terraform_meta, encoding="utf-8")

    # Create template files
    (fastapi_dir / "models_template.j2").write_text("FastAPI models", encoding="utf-8")
    (fastapi_dir / "schemas_template.j2").write_text("FastAPI schemas", encoding="utf-8")
    (fastapi_dir / "router_template.j2").write_text("FastAPI router", encoding="utf-8")

    (django_dir / "models_template.j2").write_text("Django models", encoding="utf-8")
    (django_dir / "serializers_template.j2").write_text("Django serializers", encoding="utf-8")

    (aws_cdk_dir / "stack_template.j2").write_text("AWS CDK stack", encoding="utf-8")
    (terraform_dir / "main_template.j2").write_text("Terraform main", encoding="utf-8")

    return base


@pytest.fixture
def plugin_structure_no_meta(tmp_path):
    """
    Create plugin structure WITHOUT meta.yaml files for testing discovery.

    Args:
        tmp_path (Path): pytest-provided temporary directory.

    Returns:
        Path: Base path with incomplete plugin structure.
    """
    base = tmp_path

    # Create directories without meta.yaml
    back_dir = base / "integrations" / "back"
    fastapi_dir = back_dir / "fastapi"
    django_dir = back_dir / "django"

    fastapi_dir.mkdir(parents=True, exist_ok=True)
    django_dir.mkdir(parents=True, exist_ok=True)

    # Only create templates, NO meta.yaml
    (fastapi_dir / "models_template.j2").write_text("content", encoding="utf-8")
    (django_dir / "models_template.j2").write_text("content", encoding="utf-8")

    return base


# =============================================================================
# PLUGIN DISCOVERY TESTS
# =============================================================================

class TestPluginDiscovery:
    """Test suite for plugin discovery functionality."""

    def test_discover_integrations_structure(self, plugin_structure_with_meta):
        """Test that discover_integrations correctly scans and returns integration structure."""
        base_path = plugin_structure_with_meta

        result = TemplateRegistry.discover_integrations(base_path)

        # Verify structure
        assert "back" in result
        assert "infra" in result

        # Verify stacks per category
        assert sorted(result["back"]) == ["django", "fastapi"]
        assert sorted(result["infra"]) == ["aws_cdk", "terraform"]

    def test_discover_integrations_requires_meta_yaml(self, plugin_structure_no_meta):
        """Test that discovery only includes stacks with meta.yaml files."""
        base_path = plugin_structure_no_meta

        result = TemplateRegistry.discover_integrations(base_path)

        # Should be empty because no meta.yaml files exist
        assert result == {}

    def test_discover_integrations_nonexistent_path(self, tmp_path):
        """Test discovery with non-existent integrations' directory."""
        base_path = tmp_path / "nonexistent"

        result = TemplateRegistry.discover_integrations(base_path)

        assert result == {}


# =============================================================================
# TEMPLATE REGISTRY TESTS
# =============================================================================

class TestTemplateRegistry:
    """Test suite for TemplateRegistry core functionality."""

    def test_initialization(self, plugin_structure_with_meta):
        """Test initialization with base_path."""
        base_path = plugin_structure_with_meta

        registry = TemplateRegistry(base_path=base_path)

        # Verify internal state
        assert registry.base_path == base_path
        assert "back" in registry._integrations
        assert "infra" in registry._integrations
        assert len(registry._index) > 0  # Templates were indexed

    def test_get_template_by_triplet(self, plugin_structure_with_meta):
        """Test get_template with triplet (category, stack, component)."""
        base_path = plugin_structure_with_meta
        registry = TemplateRegistry(base_path=base_path)

        # Test valid triplets
        fastapi_models = registry.get_template("back", "fastapi", "models")
        assert fastapi_models.exists()
        assert fastapi_models.name == "models_template.j2"
        assert "fastapi" in str(fastapi_models)

        django_serializers = registry.get_template("back", "django", "serializers")
        assert django_serializers.exists()
        assert django_serializers.name == "serializers_template.j2"

        aws_stack = registry.get_template("infra", "aws_cdk", "stack")
        assert aws_stack.exists()
        assert aws_stack.name == "stack_template.j2"

    def test_get_template_missing_raises_key_error(self, plugin_structure_with_meta):
        """Test that get_template raises KeyError for missing triplet."""
        base_path = plugin_structure_with_meta
        registry = TemplateRegistry(base_path=base_path)

        # Test missing category
        with pytest.raises(KeyError) as exc_info:
            registry.get_template("nonexistent", "fastapi", "models")
        assert "Template not found: nonexistent/fastapi/models" in str(exc_info.value)

        # Test missing stack
        with pytest.raises(KeyError) as exc_info:
            registry.get_template("back", "nonexistent", "models")
        assert "Template not found: back/nonexistent/models" in str(exc_info.value)

        # Test missing component
        with pytest.raises(KeyError) as exc_info:
            registry.get_template("back", "fastapi", "nonexistent")
        assert "Template not found: back/fastapi/nonexistent" in str(exc_info.value)

    def test_get_available_stacks(self, plugin_structure_with_meta):
        """Test get_available_stacks method."""
        base_path = plugin_structure_with_meta
        registry = TemplateRegistry(base_path=base_path)

        back_stacks = registry.get_available_stacks("back")
        assert sorted(back_stacks) == ["django", "fastapi"]

        infra_stacks = registry.get_available_stacks("infra")
        assert sorted(infra_stacks) == ["aws_cdk", "terraform"]

        # Test non-existent category
        empty_stacks = registry.get_available_stacks("nonexistent")
        assert empty_stacks == []

    def test_get_available_components(self, plugin_structure_with_meta):
        """Test get_available_components method."""
        base_path = plugin_structure_with_meta
        registry = TemplateRegistry(base_path=base_path)

        fastapi_components = registry.get_available_components("back", "fastapi")
        assert sorted(fastapi_components) == ["models", "router", "schemas"]

        django_components = registry.get_available_components("back", "django")
        assert sorted(django_components) == ["models", "serializers"]

        aws_components = registry.get_available_components("infra", "aws_cdk")
        assert aws_components == ["stack"]

        # Test non-existent category/stack
        empty_components = registry.get_available_components("nonexistent", "fastapi")
        assert empty_components == []

        empty_components2 = registry.get_available_components("back", "nonexistent")
        assert empty_components2 == []


# =============================================================================
# ERROR HANDLING TESTS
# =============================================================================

class TestErrorHandling:
    """Test error handling."""

    def test_invalid_initialization(self):
        """Test that initializing without base_path raises TypeError."""
        with pytest.raises(TypeError):
            TemplateRegistry()

    def test_invalid_base_path_type(self):
        """Test that invalid base_path type raises TypeError."""
        with pytest.raises(TypeError):
            TemplateRegistry(base_path="string_instead_of_path")

    def test_nonexistent_base_path(self, tmp_path):
        """Test initialization with non-existent base_path."""
        nonexistent_path = tmp_path / "does_not_exist"

        # Should not raise error during init, but will have empty integrations
        registry = TemplateRegistry(base_path=nonexistent_path)
        assert registry._integrations == {}
        assert registry._index == {}


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestIntegration:
    """Integration tests combining multiple features."""

    def test_full_plugin_workflow(self, plugin_structure_with_meta):
        """Test complete workflow: discovery -> initialization -> template access."""
        base_path = plugin_structure_with_meta

        # 1. Static discovery
        discovered = TemplateRegistry.discover_integrations(base_path)
        assert len(discovered) == 2  # back and infra categories

        # 2. Registry initialization
        registry = TemplateRegistry(base_path=base_path)

        # 3. Template access via triplet
        template_path = registry.get_template("back", "fastapi", "models")
        assert template_path.exists()

        # 4. Available stacks and components
        back_stacks = registry.get_available_stacks("back")
        assert "fastapi" in back_stacks

        fastapi_components = registry.get_available_components("back", "fastapi")
        assert "models" in fastapi_components

    def test_complete_stack_enumeration(self, plugin_structure_with_meta):
        """Test complete enumeration of all available stacks and components."""
        base_path = plugin_structure_with_meta
        registry = TemplateRegistry(base_path=base_path)

        # Enumerate all categories
        all_integrations = registry._integrations
        assert set(all_integrations.keys()) == {"back", "infra"}

        # Verify all stacks are discoverable
        for category, stacks in all_integrations.items():
            available_stacks = registry.get_available_stacks(category)
            assert sorted(available_stacks) == sorted(stacks)

            # Verify all components for each stack
            for stack in stacks:
                components = registry.get_available_components(category, stack)
                assert len(components) > 0  # Each stack should have at least one component

                # Verify each component is accessible
                for component in components:
                    template_path = registry.get_template(category, stack, component)
                    assert template_path.exists()
