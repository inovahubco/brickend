"""
test_code_generator.py

Unit tests for CodeGenerator in brickend_core.engine.code_generator.
Covers:
  1. Successful generation of project files for a valid context and FastAPI integration.
  2. ValueError when integration key is not registered.
  3. FileNotFoundError when a required template is missing.
"""

import pytest
from pathlib import Path

from brickend_core.engine.context_builder import ContextBuilder
from brickend_core.engine.template_registry import TemplateRegistry
from brickend_core.engine.template_engine import TemplateEngine
from brickend_core.engine.code_generator import CodeGenerator


def make_simple_entities_dict() -> dict:
    """
    Helper to create a minimal valid entities_dict for testing:
    - One entity named 'User'
    - Two fields: 'id' (uuid, primary_key=True) and 'email' (string, unique, nullable=False)
    """
    return {
        "entities": [
            {
                "name": "User",
                "fields": [
                    {
                        "name": "id",
                        "type": "uuid",
                        "primary_key": True,
                        "unique": False,
                        "nullable": False,
                        "default": None,
                        "foreign_key": None,
                        "constraints": [],
                    },
                    {
                        "name": "email",
                        "type": "string",
                        "primary_key": False,
                        "unique": True,
                        "nullable": False,
                        "default": None,
                        "foreign_key": None,
                        "constraints": [],
                    },
                ],
            }
        ]
    }


def test_generate_project_success(tmp_path):
    """
    Given a valid context and the 'fastapi' integration, CodeGenerator.generate_project
    should create models.py, schemas.py, crud.py, router.py, main.py, and db.py in output_dir
    with expected content.
    """
    entities_dict = make_simple_entities_dict()
    builder = ContextBuilder()
    context = builder.build_context(entities_dict)
    context["database_url"] = "sqlite:///./test.db"

    fastapi_templates_dir = Path("brickend_core/integrations/back/fastapi")
    assert fastapi_templates_dir.is_dir(), "FastAPI templates directory must exist for this test"

    registry = TemplateRegistry([fastapi_templates_dir])
    engine = TemplateEngine([fastapi_templates_dir], auto_reload=False)

    output_dir = tmp_path / "output_project"
    output_dir.mkdir()

    generator = CodeGenerator(engine, registry, output_dir)
    generator.generate_project(context, "fastapi")

    expected_files = [
        "models.py",
        "schemas.py",
        "crud.py",
        "router.py",
        "main.py",
        "db.py",
    ]
    for filename in expected_files:
        file_path = output_dir / filename
        assert file_path.exists(), f"Expected {filename} to be generated."

    models_content = (output_dir / "models.py").read_text(encoding="utf-8")
    assert "class User(Base):" in models_content

    schemas_content = (output_dir / "schemas.py").read_text(encoding="utf-8")
    assert "class UserBase(BaseModel):" in schemas_content

    crud_content = (output_dir / "crud.py").read_text(encoding="utf-8")
    assert "def get_user(" in crud_content

    router_content = (output_dir / "router.py").read_text(encoding="utf-8")
    assert "router = APIRouter" in router_content

    main_content = (output_dir / "main.py").read_text(encoding="utf-8")
    assert "app = FastAPI" in main_content

    db_content = (output_dir / "db.py").read_text(encoding="utf-8")
    assert "create_engine" in db_content


def test_generate_project_invalid_integration(tmp_path):
    """
    If the integration key is not registered in the TemplateRegistry,
    generate_project should raise a ValueError.
    """
    entities_dict = make_simple_entities_dict()
    builder = ContextBuilder()
    context = builder.build_context(entities_dict)
    context["database_url"] = "sqlite:///./test.db"

    fastapi_templates_dir = Path("brickend_core/integrations/back/fastapi")
    assert fastapi_templates_dir.is_dir()

    registry = TemplateRegistry([fastapi_templates_dir])
    engine = TemplateEngine([fastapi_templates_dir], auto_reload=False)

    output_dir = tmp_path / "output_invalid"
    output_dir.mkdir()

    generator = CodeGenerator(engine, registry, output_dir)

    with pytest.raises(ValueError) as exc_info:
        generator.generate_project(context, "nonexistent")
    assert "Integration 'nonexistent' not found" in str(exc_info.value)


def test_generate_project_missing_template(tmp_path):
    """
    If a required template (e.g., models_template.j2) is missing,
    generate_project should raise a FileNotFoundError.
    """
    entities_dict = make_simple_entities_dict()
    builder = ContextBuilder()
    context = builder.build_context(entities_dict)
    context["database_url"] = "sqlite:///./test.db"

    temp_templates_dir = tmp_path / "templates_fastapi"
    temp_templates_dir.mkdir()

    original_fastapi_dir = Path("brickend_core/integrations/back/fastapi")
    for tpl in original_fastapi_dir.rglob("*.j2"):
        dest = temp_templates_dir / tpl.name
        dest.write_text(tpl.read_text(encoding="utf-8"), encoding="utf-8")

    (temp_templates_dir / "models_template.j2").unlink()

    registry = TemplateRegistry([temp_templates_dir])
    engine = TemplateEngine([temp_templates_dir], auto_reload=False)

    output_dir = tmp_path / "output_missing"
    output_dir.mkdir()

    generator = CodeGenerator(engine, registry, output_dir)

    with pytest.raises(FileNotFoundError) as exc_info:
        generator.generate_project(context, "templates_fastapi")
    assert "models_template.j2" in str(exc_info.value)
