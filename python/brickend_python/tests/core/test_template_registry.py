"""
test_template_registry.py

Unit tests for TemplateRegistry in brickend_core.engine.template_registry.
Covers:
  - Successful discovery of templates for multiple integrations.
  - list_integrations returns correct integration keys.
  - get_template_paths returns correct template paths.
  - find_template returns correct Path for an existing template.
  - get_template_paths raises KeyError for unknown integration.
  - find_template raises FileNotFoundError for missing template.
"""

import pytest

from brickend_core.engine.template_registry import TemplateRegistry


@pytest.fixture
def sample_integration_dirs(tmp_path):
    """
    Create a temporary directory structure simulating integration template directories.

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
