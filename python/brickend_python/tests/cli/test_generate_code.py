"""
test_generate_code.py

Integration tests for the 'generate code' CLI command in brickend_cli.main.
This test suite verifies the `generate code` command:
  - Successful generation with single and multiple entities.
  - Proper error handling when entities.yaml is missing.
  - Error when integration key is invalid.
  - Correct directory and file structure.
  - Content validation of generated files.
"""

import pytest
from pathlib import Path
from typer.testing import CliRunner

from brickend_cli.main import app


def write_minimal_entities_yaml(path: Path) -> None:
    """
    Write a minimal entities.yaml with one entity 'User' having two fields: 'id' and 'email'.

    Args:
        path (Path): Path where the YAML file will be created.
    """
    content = """
    entities:
      - name: User
        fields:
          - name: id
            type: uuid
            primary_key: true
            unique: true
            nullable: false
          - name: email
            type: string
            unique: true
            nullable: false
    """
    path.write_text(content.strip(), encoding="utf-8")


def write_multi_entities_yaml(path: Path) -> None:
    """
    Write an entities.yaml with multiple entities for testing.

    Args:
        path (Path): Path where the YAML file will be created.
    """
    content = """
    entities:
      - name: User
        fields:
          - name: id
            type: uuid
            primary_key: true
            unique: true
            nullable: false
          - name: email
            type: string
            unique: true
            nullable: false
      - name: Post
        fields:
          - name: id
            type: uuid
            primary_key: true
            unique: true
            nullable: false
          - name: title
            type: string
            nullable: false
    """
    path.write_text(content.strip(), encoding="utf-8")


@pytest.fixture(autouse=True)
def ensure_clean_fastapi_templates(tmp_path, monkeypatch):
    """
    Ensure that the CLI picks up a valid fastapi integration directory.

    Args:
        tmp_path: Temporary path for the test workspace.
        monkeypatch: Fixture to modify environment (cwd).
    """
    real_project_root = Path(__file__).parents[2]
    fastapi_dir = real_project_root / "src" / "brickend_core" / "integrations" / "back" / "fastapi"
    assert fastapi_dir.is_dir(), "FastAPI integration directory is missing in the repository."

    monkeypatch.chdir(real_project_root)
    yield


def test_generate_code_success(tmp_path):
    """
    Validate that code generation succeeds for a single-entity definition.

    Args:
        tmp_path: Temporary path for the test workspace.
    """
    runner = CliRunner()
    entities_file = tmp_path / "entities.yaml"
    write_minimal_entities_yaml(entities_file)

    output_dir = tmp_path / "output"
    result = runner.invoke(
        app,
        [
            "generate",
            "code",
            str(entities_file),
            "--output",
            str(output_dir),
            "--integration",
            "fastapi",
            "--db-url",
            "sqlite:///./test.db",
        ],
    )

    assert result.exit_code == 0, f"CLI failed unexpectedly: {result.stdout}\n{result.stderr}"
    assert "✅ Code generated successfully" in result.stdout

    # Verify single files generated under app/
    expected_app_files = ["models.py", "schemas.py", "main.py", "database.py"]
    for fname in expected_app_files:
        path = output_dir / "app" / fname
        assert path.exists(), f"Expected app/{fname} to be generated."

    # Check per-entity files for User
    user_crud_path = output_dir / "app" / "crud" / "user_crud.py"
    user_router_path = output_dir / "app" / "routers" / "user_router.py"

    assert user_crud_path.exists(), "Expected app/crud/user_crud.py to be generated."
    assert user_router_path.exists(), "Expected app/routers/user_router.py to be generated."

    # Verify content in models.py
    models_content = (output_dir / "app" / "models.py").read_text(encoding="utf-8")
    assert "class User(Base):" in models_content, "User model should be in models.py"

    # Verify content in CRUD
    crud_content = user_crud_path.read_text(encoding="utf-8")
    assert "def get_user(" in crud_content, "get_user function should be in user_crud.py"
    assert (
        "from app.models import User" in crud_content
        or "from app.models.user import User" in crud_content
    ), "User import should be in user_crud.py"


def test_generate_code_multiple_entities(tmp_path):
    """
    Validate code generation for multiple entities.

    Args:
        tmp_path: Temporary path for the test workspace.
    """
    runner = CliRunner()
    entities_file = tmp_path / "entities.yaml"
    write_multi_entities_yaml(entities_file)

    output_dir = tmp_path / "output_multi"
    result = runner.invoke(
        app,
        [
            "generate",
            "code",
            str(entities_file),
            "--output",
            str(output_dir),
            "--integration",
            "fastapi",
            "--db-url",
            "sqlite:///./test.db",
        ],
    )

    assert result.exit_code == 0, f"CLI failed: {result.stdout}\n{result.stderr}"

    # Check per-entity CRUD and Router files
    for entity in ("user", "post"):
        assert (output_dir / "app" / "crud" / f"{entity}_crud.py").exists(), f"{entity}_crud.py should be generated"
        assert (output_dir / "app" / "routers" / f"{entity}_router.py").exists(), f"{entity}_router.py should be generated"

    # Verify app/main.py imports both routers
    main_content = (output_dir / "app" / "main.py").read_text(encoding="utf-8")
    assert "user_router" in main_content, "main.py should import user_router"
    assert "post_router" in main_content, "main.py should import post_router"


def test_generate_code_missing_entities(tmp_path):
    """
    Validate error when entities.yaml is missing.

    Args:
        tmp_path: Temporary path for the test workspace.
    """
    runner = CliRunner()
    missing_file = tmp_path / "nonexistent_entities.yaml"
    output_dir = tmp_path / "out_missing"

    result = runner.invoke(
        app,
        [
            "generate",
            "code",
            str(missing_file),
            "--output",
            str(output_dir),
            "--integration",
            "fastapi",
            "--db-url",
            "sqlite:///./test.db",
        ],
    )

    assert result.exit_code != 0
    assert "Error:" in result.stdout and ("not found" in result.stdout or "Entities file not found" in result.stdout)


def test_generate_code_invalid_integration(tmp_path):
    """
    Validate error when integration key is invalid.

    Args:
        tmp_path: Temporary path for the test workspace.
    """
    runner = CliRunner()
    entities_file = tmp_path / "entities.yaml"
    write_minimal_entities_yaml(entities_file)

    invalid_integration = "invalid_integration"
    output_dir = tmp_path / "out_invalid"

    result = runner.invoke(
        app,
        [
            "generate",
            "code",
            str(entities_file),
            "--output",
            str(output_dir),
            "--integration",
            invalid_integration,
            "--db-url",
            "sqlite:///./test.db",
        ],
    )

    assert result.exit_code != 0
    assert f"Generation error: Integration '{invalid_integration}' not found" in result.stdout


def test_generate_code_file_structure(tmp_path):
    """
    Validate that the correct directory structure is created.

    Args:
        tmp_path: Temporary path for the test workspace.
    """
    runner = CliRunner()
    entities_file = tmp_path / "entities.yaml"
    write_minimal_entities_yaml(entities_file)

    output_dir = tmp_path / "output_structure"
    result = runner.invoke(
        app,
        [
            "generate",
            "code",
            str(entities_file),
            "--output",
            str(output_dir),
            "--integration",
            "fastapi",
            "--db-url",
            "sqlite:///./test.db",
        ],
    )

    assert result.exit_code == 0

    # Verify directory structure
    assert (output_dir / "app").exists(), "app directory should be created"
    assert (output_dir / "app" / "crud").exists(), "app/crud directory should be created"
    assert (output_dir / "app" / "routers").exists(), "app/routers directory should be created"

    # Verify no old-style files exist in root
    assert not (output_dir / "crud.py").exists(), "crud.py should not exist in root (old structure)"
    assert not (output_dir / "router.py").exists(), "router.py should not exist in root (old structure)"


def test_generate_code_content_validation(tmp_path):
    """
    Validate content patterns in generated files.

    Args:
        tmp_path: Temporary path for the test workspace.
    """
    runner = CliRunner()
    entities_file = tmp_path / "entities.yaml"
    write_minimal_entities_yaml(entities_file)

    output_dir = tmp_path / "output_content"
    result = runner.invoke(
        app,
        [
            "generate",
            "code",
            str(entities_file),
            "--output",
            str(output_dir),
            "--integration",
            "fastapi",
            "--db-url",
            "sqlite:///./test.db",
        ],
    )

    assert result.exit_code == 0

    # Validate models.py and schemas.py inside app/
    models_content = (output_dir / "app" / "models.py").read_text(encoding="utf-8")
    assert "from sqlalchemy import Column" in models_content
    assert "class User(Base):" in models_content
    assert "__tablename__ = \"users\"" in models_content

    schemas_content = (output_dir / "app" / "schemas.py").read_text(encoding="utf-8")
    assert "from pydantic import BaseModel" in schemas_content
    assert "class UserBase(BaseModel):" in schemas_content

    # Validate user_crud.py
    crud_content = (output_dir / "app" / "crud" / "user_crud.py").read_text(encoding="utf-8")
    assert "from sqlalchemy.orm import Session" in crud_content
    assert (
        "from app.models import User" in crud_content
        or "from app.models.user import User" in crud_content
    )
    assert "def get_user(" in crud_content
    assert "def create_user(" in crud_content

    # Validate user_router.py
    router_content = (output_dir / "app" / "routers" / "user_router.py").read_text(encoding="utf-8")
    assert "from fastapi import APIRouter" in router_content
    assert "from app.crud.user_crud import" in router_content
    assert "router = APIRouter(" in router_content

    # Validate main.py inside app/
    main_content = (output_dir / "app" / "main.py").read_text(encoding="utf-8")
    assert "from fastapi import FastAPI" in main_content
    assert "from app.routers.user_router import router as user_router" in main_content
    assert "include_router(" in main_content and "user_router" in main_content

    # Validate database.py inside app/
    db_file = output_dir / "app" / "database.py"
    assert db_file.exists(), f"Expected app/database.py to be generated. Files: {list(output_dir.glob('*.py'))}"

    db_content = db_file.read_text(encoding="utf-8")
    assert "from sqlalchemy import create_engine" in db_content
    assert "def get_db():" in db_content
