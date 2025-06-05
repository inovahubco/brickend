"""
test_template_registry.py

Unit tests for TemplateRegistry in core.engine.template_registry.
Covers:
  1. Successful discovery of templates for multiple integrations.
  2. list_integrations returns correct keys.
  3. get_template_paths for existing integration.
  4. find_template returns correct Path for an existing template.
  5. get_template_paths raises KeyError for unknown integration.
  6. find_template raises FileNotFoundError if template does not exist.
"""

import pytest

from brickend_core.engine.template_registry import TemplateRegistry


@pytest.fixture
def sample_integration_dirs(tmp_path):
    """
    Create a temporary directory structure simulating:
    tmp_path/integrations/back/fastapi/models_template.j2
    tmp_path/integrations/back/fastapi/router_template.j2
    tmp_path/integrations/back/django/serializer_template.j2
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
    Given two integration directories 'fastapi' and 'django',
    TemplateRegistry should register both and list them correctly.
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
    find_template should return the exact Path when the template name exists.
    """
    registry = TemplateRegistry(sample_integration_dirs)
    path = registry.find_template("fastapi", "models_template.j2")
    assert path.name == "models_template.j2"
    assert path.exists()
    assert path.parent.name == "fastapi"


def test_get_template_paths_unknown_integration(sample_integration_dirs):
    """
    get_template_paths for a non-registered integration should raise KeyError.
    """
    registry = TemplateRegistry(sample_integration_dirs)
    with pytest.raises(KeyError) as exc_info:
        registry.get_template_paths("nonexistent")
    assert "No templates registered for integration 'nonexistent'" in str(exc_info.value)


def test_find_template_not_found(sample_integration_dirs):
    """
    find_template on an existing integration but with a missing template name
    should raise FileNotFoundError.
    """
    registry = TemplateRegistry(sample_integration_dirs)
    with pytest.raises(FileNotFoundError) as exc_info:
        registry.find_template("fastapi", "does_not_exist.j2")
    assert "Template 'does_not_exist.j2' not found under integration 'fastapi'" in str(exc_info.value)
