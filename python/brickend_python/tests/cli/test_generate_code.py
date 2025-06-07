"""
test_generate_code.py

Integration tests for the 'generate code' CLI command in cli.commands.generate_code.
Updated to match the new file structure where CRUD and Router files are generated
per-entity in app/crud/ and app/routers/ directories.
"""

import pytest
from pathlib import Path
from typer.testing import CliRunner

from brickend_cli.main import app


def write_minimal_entities_yaml(path: Path) -> None:
    """
    Write a minimal entities.yaml with one entity 'User' having two fields: 'id' and 'email'.
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
    If tests run from a different CWD, monkeypatch the project_root accordingly.
    """
    real_project_root = Path(__file__).parents[2]
    fastapi_dir = real_project_root / "brickend_core" / "integrations" / "back" / "fastapi"
    assert fastapi_dir.is_dir(), "FastAPI integration directory is missing in the repository."

    monkeypatch.chdir(real_project_root)
    yield


def test_generate_code_success(tmp_path):
    """
    Given a valid entities.yaml and the default 'fastapi' integration,
    the CLI should generate code files successfully under the specified output directory.

    Expected structure:
    - Root files: models.py, schemas.py, main.py, db.py
    - Per-entity files: app/crud/{entity}_crud.py, app/routers/{entity}_router.py
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

    # Check root files (database.py might be the actual filename)
    expected_root_files = [
        "models.py",
        "schemas.py",
        "main.py",
    ]
    for f_name in expected_root_files:
        file_path = output_dir / f_name
        assert file_path.exists(), f"Expected {f_name} to be generated in root."

    # Check for database file (could be db.py or database.py)
    db_exists = (output_dir / "db.py").exists() or (output_dir / "database.py").exists()
    assert db_exists, "Expected either db.py or database.py to be generated."

    # Check per-entity files for User
    user_crud_path = output_dir / "app" / "crud" / "user_crud.py"
    user_router_path = output_dir / "app" / "routers" / "user_router.py"

    assert user_crud_path.exists(), "Expected app/crud/user_crud.py to be generated."
    assert user_router_path.exists(), "Expected app/routers/user_router.py to be generated."

    # Verify content
    models_content = (output_dir / "models.py").read_text(encoding="utf-8")
    assert "class User(Base):" in models_content, "User model should be in models.py"

    crud_content = user_crud_path.read_text(encoding="utf-8")
    assert "def get_user(" in crud_content, "get_user function should be in user_crud.py"
    assert "from app.models.user import User" in crud_content, "User import should be in user_crud.py"


def test_generate_code_multiple_entities(tmp_path):
    """
    Test code generation with multiple entities to ensure proper file structure.
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

    # Check that both entities get their own files
    user_crud = output_dir / "app" / "crud" / "user_crud.py"
    post_crud = output_dir / "app" / "crud" / "post_crud.py"
    user_router = output_dir / "app" / "routers" / "user_router.py"
    post_router = output_dir / "app" / "routers" / "post_router.py"

    assert user_crud.exists(), "user_crud.py should be generated"
    assert post_crud.exists(), "post_crud.py should be generated"
    assert user_router.exists(), "user_router.py should be generated"
    assert post_router.exists(), "post_router.py should be generated"

    # Verify main.py imports both routers
    main_content = (output_dir / "main.py").read_text(encoding="utf-8")
    assert "user_router" in main_content, "main.py should import user_router"
    assert "post_router" in main_content, "main.py should import post_router"


def test_generate_code_missing_entities(tmp_path):
    """
    If entities.yaml does not exist, the CLI should exit with an error and message indicating the missing file.
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
    If the integration key passed is not found under core/integrations/back/,
    the CLI should exit with an error indicating integration not found.
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
    Test that the correct directory structure is created.
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
    Test that generated files contain expected content patterns.
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

    # Validate models.py
    models_content = (output_dir / "models.py").read_text(encoding="utf-8")
    assert "from sqlalchemy import Column" in models_content
    assert "class User(Base):" in models_content
    assert "__tablename__ = \"user\"" in models_content

    # Validate schemas.py
    schemas_content = (output_dir / "schemas.py").read_text(encoding="utf-8")
    assert "from pydantic import BaseModel" in schemas_content
    assert "class UserBase(BaseModel):" in schemas_content

    # Validate user_crud.py
    crud_content = (output_dir / "app" / "crud" / "user_crud.py").read_text(encoding="utf-8")
    assert "from sqlalchemy.orm import Session" in crud_content
    assert "from app.models.user import User" in crud_content
    assert "def get_user(" in crud_content
    assert "def create_user(" in crud_content

    # Validate user_router.py
    router_content = (output_dir / "app" / "routers" / "user_router.py").read_text(encoding="utf-8")
    assert "from fastapi import APIRouter" in router_content
    assert "from app.crud.user_crud import" in router_content
    assert "router = APIRouter(" in router_content

    # Validate main.py
    main_content = (output_dir / "main.py").read_text(encoding="utf-8")
    assert "from fastapi import FastAPI" in main_content
    assert "from app.routers.user_router import router as user_router" in main_content
    # Check for include_router pattern (could be with different formatting)
    assert "include_router(" in main_content and "user_router" in main_content

    # Validate database.py (might be database.py instead of db.py based on template)
    db_files = [output_dir / "db.py", output_dir / "database.py"]
    db_file = None
    for possible_db in db_files:
        if possible_db.exists():
            db_file = possible_db
            break

    assert db_file is not None, f"Neither db.py nor database.py found. Files: {list(output_dir.glob('*.py'))}"

    db_content = db_file.read_text(encoding="utf-8")
    assert "from sqlalchemy import create_engine" in db_content
    assert "def get_db():" in db_content
