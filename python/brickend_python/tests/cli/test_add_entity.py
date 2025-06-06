"""
test_add_entity.py

Unit tests for the 'add_entity' CLI command in cli.commands.add_entity.
Covers:
  1. Adding a single entity to an empty entities.yaml.
  2. Adding a second entity with a foreign key to an existing entity.
"""

import pytest
from pathlib import Path
from typer.testing import CliRunner
import ruamel.yaml

from brickend_cli.commands.add_entity import app as add_entity_app


def write_empty_entities_yaml(path: Path) -> None:
    """
    Create an entities.yaml file with an empty 'entities' list.
    """
    content = {"entities": []}
    yaml = ruamel.yaml.YAML()
    with path.open("w", encoding="utf-8") as f:
        yaml.dump(content, f)


@pytest.fixture(autouse=True)
def change_to_tmp_dir(tmp_path, monkeypatch):
    """
    Change cwd to a temporary directory for each test,
    and ensure an empty entities.yaml exists.
    """
    monkeypatch.chdir(tmp_path)
    entities_file = tmp_path / "entities.yaml"
    write_empty_entities_yaml(entities_file)
    yield


def test_add_single_entity(monkeypatch):
    """
    Simulate adding a single entity 'User' with two fields:
      1. id: uuid, primary_key = True, unique = False, nullable = False
      2. email: string, primary_key = False, unique = True, nullable = False

    Verify that entities.yaml is updated correctly.
    """
    runner = CliRunner()

    inputs = iter([
        "User",      # Entity name (PascalCase)
        "2",         # Number of fields
        # Field 1:
        "id",        # field_name
        "uuid",      # field_type
        "y",         # primary_key?
        "n",         # unique?
        # (primary key => nullable=False automatically; no prompt)
        "",          # default
        "",          # foreign_key
        "",          # constraints
        # Field 2:
        "email",     # field_name
        "string",    # field_type
        "n",         # primary_key?
        "y",         # unique?
        "n",         # nullable?
        "",          # default
        "",          # foreign_key
        "",          # constraints
    ])

    def fake_prompt(prompt_text: str, default: str = ""):
        return next(inputs)

    monkeypatch.setattr("typer.prompt", fake_prompt)

    result = runner.invoke(add_entity_app, [])
    assert result.exit_code == 0

    yaml = ruamel.yaml.YAML()
    entities_file = Path("entities.yaml")
    with entities_file.open("r", encoding="utf-8") as f:
        data = yaml.load(f)

    assert "entities" in data
    assert isinstance(data["entities"], list)
    assert len(data["entities"]) == 1

    user_entity = data["entities"][0]
    assert user_entity["name"] == "User"
    fields = user_entity["fields"]
    assert len(fields) == 2

    # Validate first field
    id_field = fields[0]
    assert id_field["name"] == "id"
    assert id_field["type"] == "uuid"
    assert id_field["primary_key"] is True
    assert id_field["unique"] is False
    assert id_field["nullable"] is False
    assert id_field.get("default") is None
    assert id_field.get("foreign_key") is None
    assert id_field.get("constraints") == []

    # Validate second field
    email_field = fields[1]
    assert email_field["name"] == "email"
    assert email_field["type"] == "string"
    assert email_field["primary_key"] is False
    assert email_field["unique"] is True
    assert email_field["nullable"] is False
    assert email_field.get("default") is None
    assert email_field.get("foreign_key") is None
    assert email_field.get("constraints") == []


def test_add_second_entity_with_foreign_key(monkeypatch):
    """
    First add 'User' entity, then add 'Post' entity with fields:
      1. id: uuid, primary_key = True
      2. title: string, primary_key = False, unique = False, nullable = False
      3. user_id: uuid, primary_key = False, unique = False, nullable = False, foreign_key = User.id

    Verify that entities.yaml contains both entities with correct definitions.
    """
    runner = CliRunner()

    inputs1 = iter([
        "User",  # Entity name
        "2",     # Number of fields
        # id field
        "id",
        "uuid",
        "y",
        "n",
        "",      # default
        "",      # foreign_key
        "",      # constraints
        # email field
        "email",
        "string",
        "n",
        "y",
        "n",
        "",
        "",
        "",
    ])

    def fake_prompt1(prompt_text: str, default: str = ""):
        return next(inputs1)

    monkeypatch.setattr("typer.prompt", fake_prompt1)
    result1 = runner.invoke(add_entity_app, [])
    assert result1.exit_code == 0

    inputs2 = iter([
        "Post",   # Entity name
        "3",      # Number of fields
        # Field 1: id
        "id",
        "uuid",
        "y",
        "n",
        "",       # default
        "",       # foreign_key
        "",       # constraints
        # Field 2: title
        "title",
        "string",
        "n",
        "n",
        "n",
        "",       # default
        "",       # foreign_key
        "",       # constraints
        # Field 3: user_id
        "user_id",
        "uuid",
        "n",
        "n",
        "n",
        "",                           # default
        "User.id",                    # foreign_key
        "index, not null",            # constraints (two constraints: "index", "not null")
    ])

    def fake_prompt2(prompt_text: str, default: str = ""):
        return next(inputs2)

    monkeypatch.setattr("typer.prompt", fake_prompt2)
    result2 = runner.invoke(add_entity_app, [])
    assert result2.exit_code == 0

    # Load and verify entities.yaml
    yaml = ruamel.yaml.YAML()
    entities_file = Path("entities.yaml")
    with entities_file.open("r", encoding="utf-8") as f:
        data = yaml.load(f)

    assert "entities" in data
    assert isinstance(data["entities"], list)
    assert len(data["entities"]) == 2

    # Validate 'User' entity remains correct
    user_entity = next(e for e in data["entities"] if e["name"] == "User")
    user_fields = user_entity["fields"]
    assert len(user_fields) == 2
    assert user_fields[0]["name"] == "id"
    assert user_fields[1]["name"] == "email"

    # Validate 'Post' entity
    post_entity = next(e for e in data["entities"] if e["name"] == "Post")
    post_fields = post_entity["fields"]
    assert len(post_fields) == 3

    # Field 'id'
    post_id = next(f for f in post_fields if f["name"] == "id")
    assert post_id["type"] == "uuid"
    assert post_id["primary_key"] is True
    assert post_id["nullable"] is False

    # Field 'title'
    post_title = next(f for f in post_fields if f["name"] == "title")
    assert post_title["type"] == "string"
    assert post_title["primary_key"] is False
    assert post_title["unique"] is False
    assert post_title["nullable"] is False

    # Field 'user_id'
    post_user_id = next(f for f in post_fields if f["name"] == "user_id")
    assert post_user_id["type"] == "uuid"
    assert post_user_id["primary_key"] is False
    assert post_user_id["nullable"] is False
    assert post_user_id["foreign_key"] == "User.id"
    assert "constraints" in post_user_id
    assert isinstance(post_user_id["constraints"], list)
    assert "index" in post_user_id["constraints"]
    assert "not null" in post_user_id["constraints"]
