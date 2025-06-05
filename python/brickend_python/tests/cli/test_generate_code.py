"""
test_generate_code.py

Integration tests for the 'generate code' CLI command in cli.commands.generate_code.
Covers:
  1. Successful code generation for a valid entities.yaml and FastAPI integration.
  2. Error when entities.yaml is missing.
  3. Error when integration key is invalid.
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

    expected_files = [
        "models.py",
        "schemas.py",
        "crud.py",
        "router.py",
        "main.py",
        "db.py",
    ]
    for f_name in expected_files:
        file_path = output_dir / f_name
        assert file_path.exists(), f"Expected {f_name} to be generated."


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
