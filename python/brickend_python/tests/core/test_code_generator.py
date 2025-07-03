"""
test_code_generator.py

Unit tests for CodeGenerator in brickend_core.engine.code_generator.
"""

import pytest
from pathlib import Path

from brickend_core.engine.context_builder import ContextBuilder
from brickend_core.engine.template_registry import TemplateRegistry
from brickend_core.engine.template_engine import TemplateEngine
from brickend_core.engine.code_generator import CodeGenerator
from brickend_core.config.project_schema import BrickendProject, ProjectInfo, StackConfig
from brickend_core.config.validation_schemas import EntityConfig


def make_simple_entities_dict() -> dict:
    """Helper to create a minimal valid entities dictionary for testing."""
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
    """Helper to create a multi-entity dictionary for testing."""
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
    """Test that CodeGenerator creates the correct project structure using generate_all."""
    entities_dict = make_simple_entities_dict()

    # Crear un proyecto de configuración completo
    config = BrickendProject(
        project=ProjectInfo(name="test_project", version="1.0.0"),
        stack=StackConfig(back="fastapi", database="postgresql"),
        entities=[EntityConfig(**entity) for entity in entities_dict["entities"]]
    )

    # Usar la ruta base correcta
    base_path = Path("src/brickend_core")
    assert base_path.is_dir(), "brickend_core directory must exist for this test"

    registry = TemplateRegistry(base_path)
    engine = TemplateEngine(base_path)

    output_dir = tmp_path / "output_project"
    output_dir.mkdir()

    # Usar el nuevo CodeGenerator con config
    generator = CodeGenerator(engine, registry, output_dir, config=config)
    generator.generate_all()  # Usar generate_all en lugar de generate_project

    # Verificar archivos generados
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

    # Verificar contenido
    models_content = (output_dir / "app" / "models.py").read_text(encoding="utf-8")
    assert "class User(Base):" in models_content

    schemas_content = (output_dir / "app" / "schemas.py").read_text(encoding="utf-8")
    assert "class UserBase(BaseModel):" in schemas_content

    crud_content = user_crud.read_text(encoding="utf-8")
    assert "def get_user(" in crud_content

    router_content = user_router.read_text(encoding="utf-8")
    assert "router = APIRouter" in router_content

    main_content = (output_dir / "app" / "main.py").read_text(encoding="utf-8")
    assert "app = FastAPI" in main_content


def test_generate_project_multiple_entities(tmp_path):
    """Test generation of CRUD and router files for multiple entities."""
    entities_dict = make_multi_entities_dict()

    config = BrickendProject(
        project=ProjectInfo(name="test_project", version="1.0.0"),
        stack=StackConfig(back="fastapi", database="postgresql"),
        entities=[EntityConfig(**entity) for entity in entities_dict["entities"]]
    )

    base_path = Path("src/brickend_core")
    registry = TemplateRegistry(base_path)
    engine = TemplateEngine(base_path)

    output_dir = tmp_path / "output_multi"
    output_dir.mkdir()

    generator = CodeGenerator(engine, registry, output_dir, config=config)
    generator.generate_all()

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


def test_generate_project_invalid_stack(tmp_path):
    """Test error when stack is not available."""
    entities_dict = make_simple_entities_dict()

    config = BrickendProject(
        project=ProjectInfo(name="test_project", version="1.0.0"),
        stack=StackConfig(back="nonexistent", database="postgresql"),
        entities=[EntityConfig(**entity) for entity in entities_dict["entities"]]
    )

    base_path = Path("src/brickend_core")
    registry = TemplateRegistry(base_path)
    engine = TemplateEngine(base_path)

    output_dir = tmp_path / "output_invalid"
    output_dir.mkdir()

    generator = CodeGenerator(engine, registry, output_dir, config=config)

    with pytest.raises(ValueError) as exc_info:
        generator.generate_all()
    assert "No templates found for stack 'nonexistent'" in str(exc_info.value)


def test_generate_project_missing_template(tmp_path):
    """Test that generation handles missing optional components gracefully."""
    entities_dict = make_simple_entities_dict()

    base_path = Path("src/brickend_core")
    temp_base = tmp_path / "brickend_core"
    temp_integrations = temp_base / "integrations" / "back" / "fastapi"
    temp_integrations.mkdir(parents=True)

    original_fastapi = base_path / "integrations" / "back" / "fastapi"

    if (original_fastapi / "meta.yaml").exists():
        (temp_integrations / "meta.yaml").write_text(
            (original_fastapi / "meta.yaml").read_text()
        )

    for template in ["models_template.j2", "schemas_template.j2",
                     "main_template.j2", "db_template.j2"]:
        if (original_fastapi / template).exists():
            content = (original_fastapi / template).read_text(encoding="utf-8")
            (temp_integrations / template).write_text(content, encoding="utf-8")

    config = BrickendProject(
        project=ProjectInfo(name="test_project", version="1.0.0"),
        stack=StackConfig(back="fastapi", database="postgresql"),
        entities=[EntityConfig(**entity) for entity in entities_dict["entities"]]
    )

    registry = TemplateRegistry(temp_base)
    engine = TemplateEngine(temp_base)

    output_dir = tmp_path / "output_missing"
    output_dir.mkdir()

    generator = CodeGenerator(engine, registry, output_dir, config=config)

    generator.generate_all()

    assert (output_dir / "app" / "models.py").exists(), "models.py should be generated"
    assert (output_dir / "app" / "schemas.py").exists(), "schemas.py should be generated"
    assert (output_dir / "app" / "main.py").exists(), "main.py should be generated"
    assert (output_dir / "app" / "database.py").exists(), "database.py should be generated"

    crud_dir = output_dir / "app" / "crud"
    routers_dir = output_dir / "app" / "routers"

    if crud_dir.exists():
        crud_files = list(crud_dir.glob("*_crud.py"))
        assert len(crud_files) == 0, "No crud files should be generated"

    if routers_dir.exists():
        router_files = list(routers_dir.glob("*_router.py"))
        assert len(router_files) == 0, "No router files should be generated"


def test_generate_project_protected_regions_disabled(tmp_path):
    """Test generation with protected regions disabled."""
    entities_dict = make_simple_entities_dict()

    config = BrickendProject(
        project=ProjectInfo(name="test_project", version="1.0.0"),
        stack=StackConfig(back="fastapi", database="postgresql"),
        entities=[EntityConfig(**entity) for entity in entities_dict["entities"]]
    )

    base_path = Path("src/brickend_core")
    registry = TemplateRegistry(base_path)
    engine = TemplateEngine(base_path)

    output_dir = tmp_path / "output_no_protection"
    output_dir.mkdir()

    generator = CodeGenerator(engine, registry, output_dir, preserve_protected_regions=False, config=config)
    generator.generate_all()

    assert (output_dir / "app" / "models.py").exists()
    assert (output_dir / "app" / "crud" / "user_crud.py").exists()
    assert (output_dir / "app" / "routers" / "user_router.py").exists()

    assert not generator.preserve_protected_regions
    assert generator.protected_handler is None


def test_generate_project_file_structure(tmp_path):
    """Test that the generated file structure matches expectations."""
    entities_dict = make_simple_entities_dict()

    config = BrickendProject(
        project=ProjectInfo(name="test_project", version="1.0.0"),
        stack=StackConfig(back="fastapi", database="postgresql"),
        entities=[EntityConfig(**entity) for entity in entities_dict["entities"]]
    )

    base_path = Path("src/brickend_core")
    registry = TemplateRegistry(base_path)
    engine = TemplateEngine(base_path)

    output_dir = tmp_path / "output_structure"
    generator = CodeGenerator(engine, registry, output_dir, config=config)
    generator.generate_all()

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
