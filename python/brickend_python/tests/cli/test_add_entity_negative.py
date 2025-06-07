"""
test_add_entity_negative.py
"""

import pytest
from pathlib import Path
from typer.testing import CliRunner
import ruamel.yaml

from brickend_cli.commands.add_entity import app as add_entity_app


def write_entities_yaml(path: Path, content: dict):
    yaml = ruamel.yaml.YAML()
    with path.open("w", encoding="utf-8") as f:
        yaml.dump(content, f)


@pytest.fixture(autouse=True)
def setup(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    path = tmp_path / "entities.yaml"
    write_entities_yaml(path, {"entities": []})
    return path


def test_add_entity_duplicate(monkeypatch, setup):
    """
    If an entity with the same name exists and the user answers 'n' to overwrite,
    the command should exit 0 and leave the file unchanged.
    """
    # Pre-populate with User
    yaml = ruamel.yaml.YAML()
    orig = {"entities": [{"name": "User", "fields": []}]}
    setup.write_text("")
    yaml.dump(orig, setup.open("w", encoding="utf-8"))

    runner = CliRunner()
    # Simulate prompts: name=User, overwrite? [n]
    inputs = iter([
        "User",  # entity name
        "n",     # overwrite? No
    ])
    monkeypatch.setattr("typer.prompt", lambda *args, **kwargs: next(inputs))

    result = runner.invoke(add_entity_app, [])
    assert result.exit_code == 0
    data = yaml.load(setup.open("r", encoding="utf-8"))
    assert len(data["entities"]) == 1
    assert data["entities"][0]["name"] == "User"


def test_add_entity_invalid_type(monkeypatch, setup):
    """
    If the user supplies an invalid field type, the prompt should repeat
    until a valid one is given, then succeed.
    """
    runner = CliRunner()
    inputs = iter([
        "Post",      # entity name
        "1",         # num fields
        "id",        # field_name
        "foo",       # invalid type
        "uuid",      # valid type
        "y",         # primary_key
        "n",         # unique
        "",          # default
        "",          # foreign_key
        "",          # constraints
    ])
    def fake_prompt(prompt_text, default=""):
        return next(inputs)
    monkeypatch.setattr("typer.prompt", fake_prompt)

    result = runner.invoke(add_entity_app, [])
    assert result.exit_code == 0
    data = ruamel.yaml.YAML().load(setup.open("r", encoding="utf-8"))
    assert any(e["name"] == "Post" for e in data["entities"])
    post = next(e for e in data["entities"] if e["name"] == "Post")
    assert post["fields"][0]["type"] == "uuid"
