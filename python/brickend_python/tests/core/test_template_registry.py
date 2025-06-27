"""
test_template_registry.py

Unit tests for TemplateRegistry in brickend_core.engine.template_registry.
Covers:
  - LEGACY MODE: Successful discovery of templates for multiple integrations.
  - LEGACY MODE: list_integrations, get_template_paths, find_template methods.
  - LEGACY MODE: Error handling for unknown integrations and missing templates.
  - PLUGIN MODE: discover_integrations static method functionality.
  - PLUGIN MODE: Triplet indexing (category, stack, component).
  - PLUGIN MODE: get_template, get_available_stacks, get_available_components.
  - PLUGIN MODE: meta.yaml requirement validation.
"""

import pytest
from pathlib import Path

from brickend_core.engine import TemplateRegistry


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def sample_integration_dirs(tmp_path):
    """
    Create a temporary directory structure simulating integration template directories.
    FOR LEGACY MODE testing.

    Structure:
      tmp_path/integrations/back/fastapi/models_template.j2
      tmp_path/integrations/back/fastapi/router_template.j2
      tmp_path/integrations/back/django/serializer_template.j2

    Args:
        tmp_path (Path): pytest-provided temporary directory.

    Returns:
        List[Path]: List of base integration directories for TemplateRegistry.
    """
    base = tmp_path / "integrations" / "back"
    fastapi_dir = base / "fastapi"
    django_dir = base / "django"

    fastapi_dir.mkdir(parents=True, exist_ok=True)
    django_dir.mkdir(parents=True, exist_ok=True)

    (fastapi_dir / "models_template.j2").write_text("dummy content", encoding="utf-8")
    (fastapi_dir / "router_template.j2").write_text("dummy content", encoding="utf-8")
    (django_dir / "serializer_template.j2").write_text("dummy content", encoding="utf-8")

    return [fastapi_dir, django_dir]


@pytest.fixture
def plugin_structure_with_meta(tmp_path):
    """
    Create a complete plugin-style directory structure with meta.yaml files.
    FOR PLUGIN MODE testing.

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
# LEGACY MODE TESTS(maintain existing functionality)
# =============================================================================

def test_list_integrations_and_get_paths(sample_integration_dirs):
    """
    Verify that TemplateRegistry correctly discovers and lists integrations,
    and returns the expected template paths for each integration.

    Args:
        sample_integration_dirs (List[Path]): Directories simulating integrations.
    """
    registry = TemplateRegistry(sample_integration_dirs)

    integrations = registry.list_integrations()
    assert "fastapi" in integrations
    assert "django" in integrations
    assert len(integrations) == 2

    fastapi_paths = registry.get_template_paths("fastapi")
    names = sorted([p.name for p in fastapi_paths])
    assert names == ["models_template.j2", "router_template.j2"]

    django_paths = registry.get_template_paths("django")
    assert len(django_paths) == 1
    assert django_paths[0].name == "serializer_template.j2"


def test_find_existing_template(sample_integration_dirs):
    """
    Verify that find_template returns the correct Path object for an existing template file.

    Args:
        sample_integration_dirs (List[Path]): Directories simulating integrations.
    """
    registry = TemplateRegistry(sample_integration_dirs)
    path = registry.find_template("fastapi", "models_template.j2")
    assert path.name == "models_template.j2"
    assert path.exists()
    assert path.parent.name == "fastapi"


def test_get_template_paths_unknown_integration(sample_integration_dirs):
    """
    Verify that get_template_paths raises KeyError when querying a non-registered integration.

    Args:
        sample_integration_dirs (List[Path]): Directories simulating integrations.
    """
    registry = TemplateRegistry(sample_integration_dirs)
    with pytest.raises(KeyError) as exc_info:
        registry.get_template_paths("nonexistent")
    assert "No templates registered for integration 'nonexistent'" in str(exc_info.value)


def test_find_template_not_found(sample_integration_dirs):
    """
    Verify that find_template raises FileNotFoundError when the template name does not exist
    under a registered integration.

    Args:
        sample_integration_dirs (List[Path]): Directories simulating integrations.
    """
    registry = TemplateRegistry(sample_integration_dirs)
    with pytest.raises(FileNotFoundError) as exc_info:
        registry.find_template("fastapi", "does_not_exist.j2")
    assert "Template 'does_not_exist.j2' not found under integration 'fastapi'" in str(exc_info.value)


# =============================================================================
# PLUGIN MODE TESTS(new functionality)
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

    def test_plugin_mode_initialization(self, plugin_structure_with_meta):
        """Test initialization in plugin mode with base_path."""
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

    def test_legacy_compatibility_in_plugin_mode(self, plugin_structure_with_meta):
        """Test that legacy methods work in plugin mode."""
        base_path = plugin_structure_with_meta
        registry = TemplateRegistry(base_path=base_path)

        # Legacy methods should work
        integrations = registry.list_integrations()
        assert "fastapi" in integrations
        assert "django" in integrations
        assert "aws_cdk" in integrations
        assert "terraform" in integrations

        # get_template_paths should work for any stack
        fastapi_paths = registry.get_template_paths("fastapi")
        assert len(fastapi_paths) == 3  # models, schemas, router

        # find_template should work
        path = registry.find_template("fastapi", "models_template.j2")
        assert path.exists()


# =============================================================================
# ERROR HANDLING TESTS
# =============================================================================

class TestErrorHandling:
    """Test error handling in both modes."""

    def test_invalid_initialization(self):
        """Test that invalid initialization raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            TemplateRegistry()  # Neither base_dirs nor base_path provided
        assert "Either base_dirs (legacy) or base_path (plugin mode) must be provided" in str(exc_info.value)

    def test_plugin_methods_require_plugin_mode(self, sample_integration_dirs):
        """Test that plugin methods raise RuntimeError in legacy mode."""
        registry = TemplateRegistry(sample_integration_dirs)  # Legacy mode

        with pytest.raises(RuntimeError) as exc_info:
            registry.get_template("back", "fastapi", "models")
        assert "requires plugin mode initialization" in str(exc_info.value)

        with pytest.raises(RuntimeError) as exc_info:
            registry.get_available_stacks("back")
        assert "requires plugin mode initialization" in str(exc_info.value)

        with pytest.raises(RuntimeError) as exc_info:
            registry.get_available_components("back", "fastapi")
        assert "requires plugin mode initialization" in str(exc_info.value)


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

        # 3. Template access via different methods
        # Via triplet
        template_path = registry.get_template("back", "fastapi", "models")
        assert template_path.exists()

        # Via legacy methods
        fastapi_templates = registry.get_template_paths("fastapi")
        assert len(fastapi_templates) == 3

        found_template = registry.find_template("fastapi", "models_template.j2")
        assert found_template == template_path

        # 4. Available stacks and components
        back_stacks = registry.get_available_stacks("back")
        assert "fastapi" in back_stacks

        fastapi_components = registry.get_available_components("back", "fastapi")
        assert "models" in fastapi_components
