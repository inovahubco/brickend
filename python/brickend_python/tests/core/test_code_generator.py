"""
test_code_generator.py

Unit tests for CodeGenerator in brickend_core.engine.code_generator.
Tests cover:
  - Successful generation of project files for a valid context and FastAPI integration.
  - ValueError when integration key is not registered.
  - FileNotFoundError when a required template is missing.
  - Behavior when protected regions are disabled.
  - Verification of generated file structure and content.
"""

import pytest
from pathlib import Path

from brickend_core.engine.context_builder import ContextBuilder
from brickend_core.engine import TemplateRegistry
from brickend_core.engine.template_engine import TemplateEngine
from brickend_core.engine.code_generator import CodeGenerator


def make_simple_entities_dict() -> dict:
    """
    Helper to create a minimal valid entities dictionary for testing.

    Creates:
      - A single entity 'User'.
      - Two fields:
          * 'id': type 'uuid', primary_key=True, unique=False, nullable=False.
          * 'email': type 'string', primary_key=False, unique=True, nullable=False.

    Returns:
        dict: Dictionary representing entities configuration.
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
    Helper to create a multi-entity dictionary for testing.

    Creates:
      - Entities 'User' and 'Post'.
      - Each entity with:
          * 'id': type 'uuid', primary_key=True, unique=False, nullable=False.
          * One additional string field ('email' for User, 'title' for Post).

    Returns:
        dict: Dictionary representing multiple entities' configuration.
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
    Test that CodeGenerator.generate_project creates the correct project structure and files.

    Scenario:
      - Given a valid entities dictionary for one entity.
      - Using 'fastapi' integration and a SQLite database URL.
    Verifies:
      - Presence of models.py, schemas.py, main.py, database.py in app/.
      - Presence of user_crud.py in app/crud/ and user_router.py in app/routers/.
      - Content checks for class definitions and imports.

    Args:
        tmp_path (Path): Temporary directory fixture for output.
    """
    entities_dict = make_simple_entities_dict()
    builder = ContextBuilder()
    context = builder.build_context(entities_dict)
    context["database_url"] = "sqlite:///./test.db"

    fastapi_templates_dir = Path("src/brickend_core/integrations/back/fastapi")
    assert fastapi_templates_dir.is_dir(), "FastAPI templates directory must exist for this test"

    registry = TemplateRegistry([fastapi_templates_dir])
    engine = TemplateEngine([fastapi_templates_dir], auto_reload=False)

    output_dir = tmp_path / "output_project"
    output_dir.mkdir()

    generator = CodeGenerator(engine, registry, output_dir)
    generator.generate_project(context, "fastapi")

    expected_app_files = [
        "models.py",
        "schemas.py",
        "main.py",
        "database.py",
    ]
    for filename in expected_app_files:
        path = output_dir / "app" / filename
        assert path.exists(), f"Expected app/{filename} to be generated."

    user_crud = output_dir / "app" / "crud" / "user_crud.py"
    assert user_crud.exists(), "Expected app/crud/user_crud.py to be generated."

    user_router = output_dir / "app" / "routers" / "user_router.py"
    assert user_router.exists(), "Expected app/routers/user_router.py to be generated."

    models_content = (output_dir / "app" / "models.py").read_text(encoding="utf-8")
    assert "class User(Base):" in models_content

    schemas_content = (output_dir / "app" / "schemas.py").read_text(encoding="utf-8")
    assert "class UserBase(BaseModel):" in schemas_content

    crud_content = user_crud.read_text(encoding="utf-8")
    assert "def get_user(" in crud_content
    assert "from app.models import User" in crud_content

    router_content = user_router.read_text(encoding="utf-8")
    assert "router = APIRouter" in router_content
    assert "from app.crud.user_crud import" in router_content

    main_content = (output_dir / "app" / "main.py").read_text(encoding="utf-8")
    assert "app = FastAPI" in main_content
    assert "from app.routers.user_router import router as user_router" in main_content

    db_content = (output_dir / "app" / "database.py").read_text(encoding="utf-8")
    assert "create_engine" in db_content


def test_generate_project_multiple_entities(tmp_path):
    """
    Test generation of CRUD and router files for multiple entities.

    Scenario:
      - Entities 'User' and 'Post'.
    Verifies:
      - app/crud/user_crud.py and post_crud.py exist.
      - app/routers/user_router.py and post_router.py exist.
      - models.py includes both User and Post classes.
      - main.py imports both routers.

    Args:
        tmp_path (Path): Temporary directory fixture for output.
    """
    entities_dict = make_multi_entities_dict()
    builder = ContextBuilder()
    context = builder.build_context(entities_dict)
    context["database_url"] = "sqlite:///./test.db"

    fastapi_templates_dir = Path("src/brickend_core/integrations/back/fastapi")
    registry = TemplateRegistry([fastapi_templates_dir])
    engine = TemplateEngine([fastapi_templates_dir], auto_reload=False)

    output_dir = tmp_path / "output_multi"
    output_dir.mkdir()

    generator = CodeGenerator(engine, registry, output_dir)
    generator.generate_project(context, "fastapi")

    # CRUD files
    assert (output_dir / "app" / "crud" / "user_crud.py").exists()
    assert (output_dir / "app" / "crud" / "post_crud.py").exists()

    # Routers
    assert (output_dir / "app" / "routers" / "user_router.py").exists()
    assert (output_dir / "app" / "routers" / "post_router.py").exists()

    # models.py con ambas clases
    models_content = (output_dir / "app" / "models.py").read_text(encoding="utf-8")
    assert "class User(Base):" in models_content
    assert "class Post(Base):" in models_content

    # main.py importa los routers
    main_content = (output_dir / "app" / "main.py").read_text(encoding="utf-8")
    assert "from app.routers.user_router import router as user_router" in main_content
    assert "from app.routers.post_router import router as post_router" in main_content


def test_generate_project_invalid_integration(tmp_path):
    """
    Test error when integration key is not registered.

    Scenario:
      - Using integration 'nonexistent'.
    Verifies:
      - CodeGenerator.generate_project raises ValueError with appropriate message.

    Args:
        tmp_path (Path): Temporary directory fixture.
    """
    entities_dict = make_simple_entities_dict()
    builder = ContextBuilder()
    context = builder.build_context(entities_dict)
    context["database_url"] = "sqlite:///./test.db"

    fastapi_templates_dir = Path("src/brickend_core/integrations/back/fastapi")
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
    Test error when a required template file is missing.

    Scenario:
      - Remove 'models_template.j2' from templates directory.
    Verifies:
      - CodeGenerator.generate_project raises FileNotFoundError mentioning the missing template.

    Args:
        tmp_path (Path): Temporary directory fixture.
    """
    entities_dict = make_simple_entities_dict()
    builder = ContextBuilder()
    context = builder.build_context(entities_dict)
    context["database_url"] = "sqlite:///./test.db"

    temp_templates_dir = tmp_path / "templates_fastapi"
    temp_templates_dir.mkdir()
    original = Path("src/brickend_core/integrations/back/fastapi")
    for tpl in original.rglob("*.j2"):
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


def test_generate_project_protected_regions_disabled(tmp_path):
    """
    Test generation with protected regions disabled.

    Scenario:
      - preserve_protected_regions=False.
    Verifies:
      - All expected files are generated.
      - generator.preserve_protected_regions is False and protected_handler is None.

    Args:
        tmp_path (Path): Temporary directory fixture.
    """
    entities_dict = make_simple_entities_dict()
    builder = ContextBuilder()
    context = builder.build_context(entities_dict)
    context["database_url"] = "sqlite:///./test.db"

    fastapi_templates_dir = Path("src/brickend_core/integrations/back/fastapi")
    registry = TemplateRegistry([fastapi_templates_dir])
    engine = TemplateEngine([fastapi_templates_dir], auto_reload=False)

    output_dir = tmp_path / "output_no_protection"
    output_dir.mkdir()

    generator = CodeGenerator(engine, registry, output_dir, preserve_protected_regions=False)
    generator.generate_project(context, "fastapi")

    assert (output_dir / "app" / "models.py").exists()
    assert (output_dir / "app" / "crud" / "user_crud.py").exists()
    assert (output_dir / "app" / "routers" / "user_router.py").exists()

    assert not generator.preserve_protected_regions
    assert generator.protected_handler is None


def test_generate_project_file_structure(tmp_path):
    """
    Test that the generated file structure matches expectations.

    Scenario:
      - Single entity 'User'.
    Verifies:
      - Directories app/, app/crud/, app/routers/ exist.
      - Specific files exist and are non-empty.

    Args:
        tmp_path (Path): Temporary directory fixture.
    """
    entities_dict = make_simple_entities_dict()
    builder = ContextBuilder()
    context = builder.build_context(entities_dict)
    context["database_url"] = "sqlite:///./test.db"

    fastapi_templates_dir = Path("src/brickend_core/integrations/back/fastapi")
    registry = TemplateRegistry([fastapi_templates_dir])
    engine = TemplateEngine([fastapi_templates_dir], auto_reload=False)

    output_dir = tmp_path / "output_structure"
    generator = CodeGenerator(engine, registry, output_dir)
    generator.generate_project(context, "fastapi")

    assert output_dir.exists()
    assert (output_dir / "app").exists()
    assert (output_dir / "app" / "crud").exists()
    assert (output_dir / "app" / "routers").exists()

    expected = {
        "models.py": output_dir / "app" / "models.py",
        "schemas.py": output_dir / "app" / "schemas.py",
        "main.py": output_dir / "app" / "main.py",
        "database.py": output_dir / "app" / "database.py",
        "user_crud.py": output_dir / "app" / "crud" / "user_crud.py",
        "user_router.py": output_dir / "app" / "routers" / "user_router.py",
    }
    for name, path in expected.items():
        assert path.exists(), f"{name} should exist at {path}"
        assert path.is_file(), f"{name} should be a file"
        assert path.stat().st_size > 0, f"{name} should not be empty"
