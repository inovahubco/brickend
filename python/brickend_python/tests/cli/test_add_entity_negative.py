"""
test_add_entity_negative.py

Unit tests for negative scenarios of the `add_entity` CLI command:
  - Duplicate entity without overwrite (user aborts correctly).
  - Invalid field type prompt repeats until valid type is provided.
"""

import pytest
from pathlib import Path
from typer.testing import CliRunner
import ruamel.yaml

from brickend_cli.commands.add_entity import app as add_entity_app


def write_entities_yaml(path: Path, content: dict) -> None:
    """
    Write a YAML file with the provided content to the given path.

    Args:
        path (Path): File path where the YAML should be written.
        content (dict): Python dictionary to serialize as YAML.
    """
    yaml = ruamel.yaml.YAML()
    with path.open("w", encoding="utf-8") as f:
        yaml.dump(content, f)


@pytest.fixture(autouse=True)
def setup(tmp_path, monkeypatch):
    """
    Pytest fixture to set up a temporary working directory and an empty entities.yaml.

    Args:
        tmp_path: Temporary directory provided by pytest.
        monkeypatch: Monkeypatch fixture to change working directory.

    Returns:
        Path: Path to the created entities.yaml file.
    """
    monkeypatch.chdir(tmp_path)
    path = tmp_path / "entities.yaml"
    write_entities_yaml(path, {"entities": []})
    return path


def test_add_entity_duplicate(monkeypatch, setup):
    """
    Ensure that if an entity already exists and the user opts not to overwrite,
    the command exits with code 0 and leaves the file unchanged.
    """
    # Pre-populate with User
    yaml = ruamel.yaml.YAML()
    original = {"entities": [{"name": "User", "fields": []}]}
    setup.write_text("")  # clear file
    yaml.dump(original, setup.open("w", encoding="utf-8"))

    runner = CliRunner()
    # Simulate prompts: entity name 'User', then 'n' for overwrite
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
    Ensure that if the user provides an invalid field type, the prompt repeats
    until a valid type is given, and then the entity is added successfully.
    """
    runner = CliRunner()
    inputs = iter([
        "Post",      # entity name
        "1",         # number of fields
        "id",        # field_name
        "foo",       # invalid type (prompt repeats)
        "uuid",      # valid type
        "y",         # primary_key
        "n",         # unique
        "",          # default
        "",          # foreign_key
        "",          # constraints
    ])

    def fake_prompt(prompt_text: str, default: str = "") -> str:
        return next(inputs)

    monkeypatch.setattr("typer.prompt", fake_prompt)

    result = runner.invoke(add_entity_app, [])
    assert result.exit_code == 0

    data = ruamel.yaml.YAML().load(setup.open("r", encoding="utf-8"))
    assert any(e["name"] == "Post" for e in data["entities"])
    post = next(e for e in data["entities"] if e["name"] == "Post")
    assert post["fields"][0]["type"] == "uuid"
