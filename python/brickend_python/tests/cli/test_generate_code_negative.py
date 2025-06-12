"""
test_generate_code_negative.py

Unit tests for negative scenarios of the 'generate code' CLI command:
  - Entities without 'fields' should cause an error.
  - Unknown integration keys should cause an integration-not-found error.
"""

import pytest
from typer.testing import CliRunner
import ruamel.yaml

from brickend_cli.main import app as cli_app


@pytest.fixture
def tmp_proj(tmp_path, monkeypatch):
    """
    Create a minimal project directory with an invalid entities.yaml (missing 'fields').

    Args:
        tmp_path: pytest-provided temporary directory.
        monkeypatch: pytest fixture to modify the environment.

    Returns:
        Tuple[Path, Path]: (project_root, path_to_entities_yaml)
    """
    proj = tmp_path / "demo"
    proj.mkdir()
    (proj / "brickend_core").mkdir()
    monkeypatch.chdir(proj)
    entities = proj / "entities.yaml"
    # Write an entity definition without 'fields'
    entities.write_text("entities:\n  - name: InvalidEntity\n")
    return proj, entities


def test_generate_code_missing_fields(tmp_proj):
    """
    If entities.yaml defines an entity without 'fields', generate_code should exit with an error
    mentioning 'fields'.
    """
    proj, entities = tmp_proj
    output = proj / "out"
    runner = CliRunner()
    result = runner.invoke(
        cli_app,
        ["generate", "code", str(entities), "--output", str(output), "--integration", "fastapi"]
    )
    assert result.exit_code != 0
    # The error message should reference 'fields'
    assert "fields" in result.stdout.lower()


def test_generate_code_invalid_integration(tmp_proj):
    """
    If an unknown integration key is passed, generate_code should exit non-zero
    with a message indicating the integration was not found.
    """
    proj, entities = tmp_proj

    # Rewrite entities.yaml to be valid for this test
    valid_content = {
        "entities": [
            {
                "name": "User",
                "fields": [
                    {
                        "name": "id",
                        "type": "uuid",
                        "primary_key": True,
                        "unique": True,
                        "nullable": False
                    }
                ]
            }
        ]
    }
    yaml = ruamel.yaml.YAML()
    with open(entities, "w", encoding="utf-8") as f:
        yaml.dump(valid_content, f)

    output = proj / "out"
    runner = CliRunner()
    result = runner.invoke(
        cli_app,
        ["generate", "code", str(entities), "--output", str(output), "--integration", "nope"]
    )
    assert result.exit_code != 0
    assert "Generation error: Integration 'nope' not found" in result.stdout
