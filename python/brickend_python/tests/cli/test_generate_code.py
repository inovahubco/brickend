"""
test_generate_code.py

Integration tests for the 'generate code' CLI command in brickend_cli.main.
This test suite verifies the `generate code` command:
  - Successful generation with single and multiple entities.
  - Proper error handling when configuration is missing.
  - Error when stack is invalid.
  - Correct directory and file structure.
  - Content validation of generated files.
"""

import pytest
from pathlib import Path
from typer.testing import CliRunner

from brickend_cli.main import app


def write_brickend_config_single_entity(path: Path) -> None:
    """
    Write a minimal brickend.yaml with one entity 'User' having two fields: 'id' and 'email'.

    Args:
        path (Path): Path where the YAML file will be created.
    """
    content = """
project:
  name: test_project
  description: Test project for code generation
  version: 1.0.0

stack:
  back: fastapi
  database: postgresql

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

settings:
  auto_migrations: true
  api_docs: true
"""
    path.write_text(content.strip(), encoding="utf-8")


def write_brickend_config_multi_entities(path: Path) -> None:
    """
    Write a brickend.yaml with multiple entities for testing.

    Args:
        path (Path): Path where the YAML file will be created.
    """
    content = """
project:
  name: multi_project
  description: Test project with multiple entities
  version: 1.0.0

stack:
  back: fastapi
  database: postgresql

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

settings:
  auto_migrations: true
  api_docs: true
"""
    path.write_text(content.strip(), encoding="utf-8")


def write_brickend_config_invalid_stack(path: Path) -> None:
    """
    Write a brickend.yaml with invalid stack for testing.

    Args:
        path (Path): Path where the YAML file will be created.
    """
    content = """
project:
  name: invalid_project
  version: 1.0.0

stack:
  back: invalid_integration
  database: postgresql

entities:
  - name: User
    fields:
      - name: id
        type: uuid
        primary_key: true

settings: {}
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

    # Create brickend.yaml config
    config_file = tmp_path / "brickend.yaml"
    write_brickend_config_single_entity(config_file)

    output_dir = tmp_path / "output"

    # Use new CLI interface
    result = runner.invoke(
        app,
        [
            "generate",
            "code",
            "--config", str(config_file),
            "--output", str(output_dir),
            "--db-url", "sqlite:///./test.db",
        ],
    )

    assert result.exit_code == 0, f"CLI failed unexpectedly: {result.stdout}\n{result.stderr}"
    assert "✅ Code generated successfully" in result.stdout

    # Verify single files generated under app/
    expected_app_files = ["models.py", "schemas.py", "main.py", "database.py"]
    for fname in expected_app_files:
        path = output_dir / "app" / fname
        assert path.exists(), f"Expected app/{fname} to be generated."

    # Check per-entity files for User (per-entity structure)
    user_crud_path = output_dir / "app" / "crud" / "user_crud.py"
    user_router_path = output_dir / "app" / "routers" / "user_router.py"

    assert user_crud_path.exists(), "Expected app/crud/user_crud.py to be generated."
    assert user_router_path.exists(), "Expected app/routers/user_router.py to be generated."

    # Verify content in models.py
    models_content = (output_dir / "app" / "models.py").read_text(encoding="utf-8")
    assert "class User(Base):" in models_content, "User model should be in models.py"


def test_generate_code_multiple_entities(tmp_path):
    """
    Validate code generation for multiple entities.

    Args:
        tmp_path: Temporary path for the test workspace.
    """
    runner = CliRunner()

    # Create brickend.yaml config
    config_file = tmp_path / "brickend.yaml"
    write_brickend_config_multi_entities(config_file)

    output_dir = tmp_path / "output_multi"

    result = runner.invoke(
        app,
        [
            "generate",
            "code",
            "--config", str(config_file),
            "--output", str(output_dir),
            "--db-url", "sqlite:///./test.db",
        ],
    )

    assert result.exit_code == 0, f"CLI failed: {result.stdout}\n{result.stderr}"

    # Check that models.py contains both entities
    models_content = (output_dir / "app" / "models.py").read_text(encoding="utf-8")
    assert "class User(Base):" in models_content, "User model should be in models.py"
    assert "class Post(Base):" in models_content, "Post model should be in models.py"

    # Check per-entity CRUD and Router files
    for entity in ("user", "post"):
        crud_path = output_dir / "app" / "crud" / f"{entity}_crud.py"
        router_path = output_dir / "app" / "routers" / f"{entity}_router.py"
        assert crud_path.exists(), f"{entity}_crud.py should be generated"
        assert router_path.exists(), f"{entity}_router.py should be generated"

    # Verify app/main.py contains routers
    main_content = (output_dir / "app" / "main.py").read_text(encoding="utf-8")
    assert "router" in main_content.lower(), "main.py should contain router references"


def test_generate_code_missing_config(tmp_path):
    """
    Validate error when brickend.yaml is missing.

    Args:
        tmp_path: Temporary path for the test workspace.
    """
    runner = CliRunner()
    missing_file = tmp_path / "nonexistent_brickend.yaml"
    output_dir = tmp_path / "out_missing"

    result = runner.invoke(
        app,
        [
            "generate",
            "code",
            "--config", str(missing_file),
            "--output", str(output_dir),
            "--db-url", "sqlite:///./test.db",
        ],
    )

    assert result.exit_code != 0
    assert "Error: No configuration file found" in result.stdout or "Error: No configuration found" in result.stdout


def test_generate_code_invalid_stack(tmp_path):
    """
    Validate error when stack is invalid.

    Args:
        tmp_path: Temporary path for the test workspace.
    """
    runner = CliRunner()

    # Create config with invalid stack
    config_file = tmp_path / "brickend.yaml"
    write_brickend_config_invalid_stack(config_file)

    output_dir = tmp_path / "out_invalid"

    result = runner.invoke(
        app,
        [
            "generate",
            "code",
            "--config", str(config_file),
            "--output", str(output_dir),
            "--db-url", "sqlite:///./test.db",
        ],
    )

    assert result.exit_code != 0
    assert ("invalid_integration" in result.stdout or
            "not available" in result.stdout or
            "Validation error" in result.stdout)


def test_generate_code_file_structure(tmp_path):
    """
    Validate that the correct directory structure is created.

    Args:
        tmp_path: Temporary path for the test workspace.
    """
    runner = CliRunner()

    # Create brickend.yaml config
    config_file = tmp_path / "brickend.yaml"
    write_brickend_config_single_entity(config_file)

    output_dir = tmp_path / "output_structure"

    result = runner.invoke(
        app,
        [
            "generate",
            "code",
            "--config", str(config_file),
            "--output", str(output_dir),
            "--db-url", "sqlite:///./test.db",
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

    # Create brickend.yaml config
    config_file = tmp_path / "brickend.yaml"
    write_brickend_config_single_entity(config_file)

    output_dir = tmp_path / "output_content"

    result = runner.invoke(
        app,
        [
            "generate",
            "code",
            "--config", str(config_file),
            "--output", str(output_dir),
            "--db-url", "sqlite:///./test.db",
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

    # Validate user_crud.py (per-entity structure)
    user_crud_path = output_dir / "app" / "crud" / "user_crud.py"
    assert user_crud_path.exists(), "Expected app/crud/user_crud.py to be generated"

    crud_content = user_crud_path.read_text(encoding="utf-8")
    assert "from sqlalchemy.orm import Session" in crud_content
    assert (
        "from app.models import User" in crud_content or
        "from .models import User" in crud_content or
        "from app.models.user import User" in crud_content
    )
    assert "def get_user(" in crud_content
    assert "def create_user(" in crud_content

    # Validate user_router.py (per-entity structure)
    user_router_path = output_dir / "app" / "routers" / "user_router.py"
    assert user_router_path.exists(), "Expected app/routers/user_router.py to be generated"

    router_content = user_router_path.read_text(encoding="utf-8")
    assert "from fastapi import APIRouter" in router_content
    assert (
        "from app.crud.user_crud import" in router_content or
        "from ..crud.user_crud import" in router_content
    )
    assert "router = APIRouter(" in router_content

    # Validate main.py inside app/
    main_content = (output_dir / "app" / "main.py").read_text(encoding="utf-8")
    assert "from fastapi import FastAPI" in main_content
    assert "include_router(" in main_content

    # Validate database.py inside app/
    db_file = output_dir / "app" / "database.py"
    assert db_file.exists(), f"Expected app/database.py to be generated."

    db_content = db_file.read_text(encoding="utf-8")
    assert "from sqlalchemy import create_engine" in db_content
    assert "def get_db():" in db_content


def test_generate_code_default_config_detection(tmp_path):
    """
    Test that the command can auto-detect brickend.yaml in current directory.

    Args:
        tmp_path: Temporary path for the test workspace.
    """
    runner = CliRunner()

    # Create brickend.yaml in temp directory
    config_file = tmp_path / "brickend.yaml"
    write_brickend_config_single_entity(config_file)

    output_dir = tmp_path / "output_auto"

    # Change to temp directory and run without --config
    import os
    original_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)

        result = runner.invoke(
            app,
            [
                "generate",
                "code",
                "--output", str(output_dir),
                "--db-url", "sqlite:///./test.db",
            ],
        )

        assert result.exit_code == 0, f"Auto-detection failed: {result.stdout}\n{result.stderr}"
        assert (output_dir / "app" / "models.py").exists()

    finally:
        os.chdir(original_cwd)


def test_generate_code_validate_only(tmp_path):
    """
    Test --validate-only flag functionality.

    Args:
        tmp_path: Temporary path for the test workspace.
    """
    runner = CliRunner()

    # Create brickend.yaml config
    config_file = tmp_path / "brickend.yaml"
    write_brickend_config_single_entity(config_file)

    result = runner.invoke(
        app,
        [
            "generate",
            "code",
            "--config", str(config_file),
            "--validate-only",
        ],
    )

    assert result.exit_code == 0
    assert "✅ Configuration is valid" in result.stdout

    # Verify no files were generated
    output_dir = tmp_path / "app"
    assert not output_dir.exists(), "No files should be generated with --validate-only"


def test_generate_code_with_external_entities(tmp_path):
    """
    Test generation with external entities file reference.

    Args:
        tmp_path: Temporary path for the test workspace.
    """
    runner = CliRunner()

    # Create brickend.yaml with external entities reference
    brickend_content = """
project:
  name: external_test
  version: 1.0.0

stack:
  back: fastapi
  database: postgresql

entities: "./entities.yaml"

settings:
  auto_migrations: true
"""

    # Create separate entities.yaml
    entities_content = """
entities:
  - name: Product
    fields:
      - name: id
        type: uuid
        primary_key: true
      - name: name
        type: string
"""

    config_file = tmp_path / "brickend.yaml"
    entities_file = tmp_path / "entities.yaml"

    config_file.write_text(brickend_content.strip(), encoding="utf-8")
    entities_file.write_text(entities_content.strip(), encoding="utf-8")

    output_dir = tmp_path / "output_external"

    result = runner.invoke(
        app,
        [
            "generate",
            "code",
            "--config", str(config_file),
            "--output", str(output_dir),
            "--db-url", "sqlite:///./test.db",
        ],
    )

    assert result.exit_code == 0

    # Verify Product model was generated
    models_content = (output_dir / "app" / "models.py").read_text(encoding="utf-8")
    assert "class Product(Base):" in models_content