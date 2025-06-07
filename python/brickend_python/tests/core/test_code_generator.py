"""
test_code_generator.py

Unit tests for CodeGenerator in brickend_core.engine.code_generator.
Covers:
  1. Successful generation of project files for a valid context and FastAPI integration.
  2. ValueError when integration key is not registered.
  3. FileNotFoundError when a required template is missing.

Updated to match the new file structure where CRUD and Router files are generated
per-entity in app/crud/ and app/routers/ directories.
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


def make_multi_entities_dict() -> dict:
    """
    Helper to create a multi-entity dict for testing:
    - User and Post entities
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
            },
            {
                "name": "Post",
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
                        "name": "title",
                        "type": "string",
                        "primary_key": False,
                        "unique": False,
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
    should create the correct file structure:
    - Root files: models.py, schemas.py, main.py, db.py
    - Per-entity files: app/crud/{entity}_crud.py, app/routers/{entity}_router.py
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

    # Check single files that should be generated in the root
    expected_root_files = [
        "models.py",
        "schemas.py",
        "main.py",
        "db.py",
    ]
    for filename in expected_root_files:
        file_path = output_dir / filename
        assert file_path.exists(), f"Expected {filename} to be generated in root."

    # Check per-entity CRUD files
    user_crud_path = output_dir / "app" / "crud" / "user_crud.py"
    assert user_crud_path.exists(), "Expected app/crud/user_crud.py to be generated."

    # Check per-entity Router files
    user_router_path = output_dir / "app" / "routers" / "user_router.py"
    assert user_router_path.exists(), "Expected app/routers/user_router.py to be generated."

    # Verify content of generated files
    models_content = (output_dir / "models.py").read_text(encoding="utf-8")
    assert "class User(Base):" in models_content, "User model should be in models.py"

    schemas_content = (output_dir / "schemas.py").read_text(encoding="utf-8")
    assert "class UserBase(BaseModel):" in schemas_content, "User schema should be in schemas.py"

    crud_content = user_crud_path.read_text(encoding="utf-8")
    assert "def get_user(" in crud_content, "get_user function should be in user_crud.py"
    assert "from app.models.user import User" in crud_content, "User import should be in user_crud.py"

    router_content = user_router_path.read_text(encoding="utf-8")
    assert "router = APIRouter" in router_content, "APIRouter should be in user_router.py"
    assert "from app.crud.user_crud import" in router_content, "CRUD import should be in user_router.py"

    main_content = (output_dir / "main.py").read_text(encoding="utf-8")
    assert "app = FastAPI" in main_content, "FastAPI app should be in main.py"
    assert "from app.routers.user_router import router as user_router" in main_content, "Router import should be in main.py"

    db_content = (output_dir / "db.py").read_text(encoding="utf-8")
    assert "create_engine" in db_content, "create_engine should be in db.py"


def test_generate_project_multiple_entities(tmp_path):
    """
    Test generation with multiple entities to ensure each gets its own CRUD and Router files.
    """
    entities_dict = make_multi_entities_dict()
    builder = ContextBuilder()
    context = builder.build_context(entities_dict)
    context["database_url"] = "sqlite:///./test.db"

    fastapi_templates_dir = Path("brickend_core/integrations/back/fastapi")
    assert fastapi_templates_dir.is_dir()

    registry = TemplateRegistry([fastapi_templates_dir])
    engine = TemplateEngine([fastapi_templates_dir], auto_reload=False)

    output_dir = tmp_path / "output_multi"
    output_dir.mkdir()

    generator = CodeGenerator(engine, registry, output_dir)
    generator.generate_project(context, "fastapi")

    # Check that both entities get their own CRUD files
    user_crud_path = output_dir / "app" / "crud" / "user_crud.py"
    post_crud_path = output_dir / "app" / "crud" / "post_crud.py"
    assert user_crud_path.exists(), "user_crud.py should be generated"
    assert post_crud_path.exists(), "post_crud.py should be generated"

    # Check that both entities get their own Router files
    user_router_path = output_dir / "app" / "routers" / "user_router.py"
    post_router_path = output_dir / "app" / "routers" / "post_router.py"
    assert user_router_path.exists(), "user_router.py should be generated"
    assert post_router_path.exists(), "post_router.py should be generated"

    # Verify models.py contains both entities
    models_content = (output_dir / "models.py").read_text(encoding="utf-8")
    assert "class User(Base):" in models_content
    assert "class Post(Base):" in models_content

    # Verify main.py imports both routers
    main_content = (output_dir / "main.py").read_text(encoding="utf-8")
    assert "from app.routers.user_router import router as user_router" in main_content
    assert "from app.routers.post_router import router as post_router" in main_content

    # Verify entity-specific content in CRUD files
    user_crud_content = user_crud_path.read_text(encoding="utf-8")
    assert "from app.models.user import User" in user_crud_content
    assert "def get_user(" in user_crud_content

    post_crud_content = post_crud_path.read_text(encoding="utf-8")
    assert "from app.models.post import Post" in post_crud_content
    assert "def get_post(" in post_crud_content


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

    # Create a temporary templates directory with missing models_template.j2
    temp_templates_dir = tmp_path / "templates_fastapi"
    temp_templates_dir.mkdir()

    original_fastapi_dir = Path("brickend_core/integrations/back/fastapi")
    for tpl in original_fastapi_dir.rglob("*.j2"):
        dest = temp_templates_dir / tpl.name
        dest.write_text(tpl.read_text(encoding="utf-8"), encoding="utf-8")

    # Remove the models template to trigger the error
    (temp_templates_dir / "models_template.j2").unlink()

    registry = TemplateRegistry([temp_templates_dir])
    engine = TemplateEngine([temp_templates_dir], auto_reload=False)

    output_dir = tmp_path / "output_missing"
    output_dir.mkdir()

    generator = CodeGenerator(engine, registry, output_dir)

    with pytest.raises(FileNotFoundError) as exc_info:
        generator.generate_project(context, "templates_fastapi")
    assert "models_template.j2" in str(exc_info.value)


def test_generate_project_protected_regions_disabled(tmp_path):
    """
    Test that CodeGenerator works correctly when protected regions are disabled.
    """
    entities_dict = make_simple_entities_dict()
    builder = ContextBuilder()
    context = builder.build_context(entities_dict)
    context["database_url"] = "sqlite:///./test.db"

    fastapi_templates_dir = Path("brickend_core/integrations/back/fastapi")
    assert fastapi_templates_dir.is_dir()

    registry = TemplateRegistry([fastapi_templates_dir])
    engine = TemplateEngine([fastapi_templates_dir], auto_reload=False)

    output_dir = tmp_path / "output_no_protection"
    output_dir.mkdir()

    # Create generator with protected regions disabled
    generator = CodeGenerator(engine, registry, output_dir, preserve_protected_regions=False)
    generator.generate_project(context, "fastapi")

    # Should generate all expected files
    assert (output_dir / "models.py").exists()
    assert (output_dir / "app" / "crud" / "user_crud.py").exists()
    assert (output_dir / "app" / "routers" / "user_router.py").exists()

    # Verify that protected regions functionality is disabled
    assert generator.preserve_protected_regions is False
    assert generator.protected_handler is None


def test_generate_project_file_structure(tmp_path):
    """
    Test that the generated file structure matches expectations.
    """
    entities_dict = make_simple_entities_dict()
    builder = ContextBuilder()
    context = builder.build_context(entities_dict)
    context["database_url"] = "sqlite:///./test.db"

    fastapi_templates_dir = Path("brickend_core/integrations/back/fastapi")
    registry = TemplateRegistry([fastapi_templates_dir])
    engine = TemplateEngine([fastapi_templates_dir], auto_reload=False)

    output_dir = tmp_path / "output_structure"
    generator = CodeGenerator(engine, registry, output_dir)
    generator.generate_project(context, "fastapi")

    # Verify directory structure
    assert output_dir.exists()
    assert (output_dir / "app").exists()
    assert (output_dir / "app" / "crud").exists()
    assert (output_dir / "app" / "routers").exists()

    # Verify file locations
    expected_structure = {
        "models.py": output_dir / "models.py",
        "schemas.py": output_dir / "schemas.py",
        "main.py": output_dir / "main.py",
        "db.py": output_dir / "db.py",
        "user_crud.py": output_dir / "app" / "crud" / "user_crud.py",
        "user_router.py": output_dir / "app" / "routers" / "user_router.py",
    }

    for desc, path in expected_structure.items():
        assert path.exists(), f"{desc} should exist at {path}"
        assert path.is_file(), f"{desc} should be a file"
        assert path.stat().st_size > 0, f"{desc} should not be empty"
