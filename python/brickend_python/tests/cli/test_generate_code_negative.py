"""
test_generate_code_negative.py
"""

import pytest
from typer.testing import CliRunner
import ruamel.yaml

from brickend_cli.main import app as cli_app


@pytest.fixture
def tmp_proj(tmp_path, monkeypatch):
    """Creates a minimal project dir with an invalid entities.yaml (missing fields)."""
    proj = tmp_path / "demo"
    proj.mkdir()
    (proj / "brickend_core").mkdir()
    monkeypatch.chdir(proj)
    entities = proj / "entities.yaml"
    entities.write_text("entities:\n  - name: InvalidEntity\n")
    return proj, entities


def test_generate_code_missing_fields(tmp_proj):
    """
    If entities.yaml defines an entity without 'fields', generate_code should error.
    """
    proj, entities = tmp_proj
    output = proj / "out"
    runner = CliRunner()
    result = runner.invoke(
        cli_app,
        ["generate", "code", str(entities), "--output", str(output), "--integration", "fastapi"]
    )
    assert result.exit_code != 0
    assert "fields" in result.stdout.lower()


def test_generate_code_invalid_integration(tmp_proj):
    """
    If an unknown integration is passed, generate_code exits non-zero with message about integration not found.
    """
    proj, entities = tmp_proj

    valid_content = {
        "entities": [
            {
                "name": "User",
                "fields": [
                    {"name": "id", "type": "uuid", "primary_key": True, "unique": True, "nullable": False}
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
