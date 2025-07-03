"""
test_add_entity.py

Unit tests for the 'add_entity entity' CLI command in brickend_cli.main.
Covers:
  - Adding a single entity to an empty entities.yaml.
  - Adding a second entity with a foreign key to an existing entity.
"""

import pytest
from pathlib import Path
from typer.testing import CliRunner
import ruamel.yaml

from brickend_cli.main import app as cli_app


def write_empty_entities_yaml(path: Path) -> None:
    """
    Create an entities.yaml file with an empty 'entities' list.

    Args:
        path (Path): Path where entities.yaml will be created.
    """
    content = {"entities": []}
    yaml = ruamel.yaml.YAML()
    with path.open("w", encoding="utf-8") as f:
        yaml.dump(content, f)


def write_brickend_yaml_external(path: Path) -> None:
    """
    Create a brickend.yaml file with external entities reference.

    Args:
        path (Path): Path where brickend.yaml will be created.
    """
    content = {
        "project": {
            "name": "test_project",
            "version": "1.0.0"
        },
        "stack": {
            "back": "fastapi",
            "database": "postgresql"
        },
        "entities": "./entities.yaml",  # External reference
        "settings": {
            "auto_migrations": True,
            "api_docs": True
        }
    }

    yaml = ruamel.yaml.YAML()
    yaml.default_flow_style = False
    with path.open("w", encoding="utf-8") as f:
        yaml.dump(content, f)


@pytest.fixture(autouse=True)
def change_to_tmp_dir(tmp_path, monkeypatch):
    """
    Change cwd to a temporary directory for each test,
    and ensure a proper project structure exists.

    Args:
        tmp_path: pytest fixture for a temporary directory.
        monkeypatch: pytest fixture for patching.
    """
    monkeypatch.chdir(tmp_path)

    # Create brickend.yaml with external entities reference
    brickend_file = tmp_path / "brickend.yaml"
    write_brickend_yaml_external(brickend_file)

    # Create empty entities.yaml
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

    # Create an iterator with all the expected inputs
    inputs = iter([
        "User",  # Entity name (PascalCase)
        "2",  # Number of fields
        # Field 1:
        "id",  # field_name
        "uuid",  # field_type
        "y",  # primary_key?
        "n",  # unique?
        "",  # default
        "",  # foreign_key
        "",  # constraints
        # Field 2:
        "email",  # field_name
        "string",  # field_type
        "n",  # primary_key?
        "y",  # unique?
        "n",  # nullable?
        "",  # default
        "",  # foreign_key
        "",  # constraints
        "y",  # Save this entity?
    ])

    # Patch all the rich prompt functions
    def fake_prompt(*args, **kwargs):
        return next(inputs)

    def fake_confirm(*args, **kwargs):
        value = next(inputs)
        return value.lower() == 'y'

    def fake_intprompt(*args, **kwargs):
        return int(next(inputs))

    # Patch rich.prompt functions
    monkeypatch.setattr("rich.prompt.Prompt.ask", fake_prompt)
    monkeypatch.setattr("rich.prompt.Confirm.ask", fake_confirm)
    monkeypatch.setattr("rich.prompt.IntPrompt.ask", fake_intprompt)

    result = runner.invoke(cli_app, ["add_entity", "entity"])

    # DEBUG: Print output to see what's happening
    print("\n=== CLI OUTPUT ===")
    print(result.stdout)
    print("=== END OUTPUT ===\n")

    # DEBUG: Check both files
    print("=== FILE CONTENTS ===")
    print(f"brickend.yaml exists: {Path('brickend.yaml').exists()}")
    print(f"entities.yaml exists: {Path('entities.yaml').exists()}")

    if Path('brickend.yaml').exists():
        print("\nbrickend.yaml content:")
        print(Path('brickend.yaml').read_text())

    if Path('entities.yaml').exists():
        print("\nentities.yaml content:")
        print(Path('entities.yaml').read_text())
    print("=== END FILES ===\n")

    assert result.exit_code == 0, f"CLI failed: {result.stdout}\n{result.stderr}"

    yaml = ruamel.yaml.YAML()
    entities_file = Path("entities.yaml")
    with entities_file.open("r", encoding="utf-8") as f:
        data = yaml.load(f)

    assert "entities" in data
    assert isinstance(data["entities"], list)
    assert len(data["entities"]) == 1


def test_add_second_entity_with_foreign_key(monkeypatch):
    """
    First add 'User' entity, then add 'Post' entity with fields:
      1. id: uuid, primary_key = True
      2. title: string, primary_key = False, unique = False, nullable = False
      3. user_id: uuid, primary_key = False, unique = False, nullable = False, foreign_key = User.id

    Verify that entities.yaml contains both entities with correct definitions.
    """
    runner = CliRunner()

    # First call inputs
    inputs1 = iter([
        "User",  # Entity name
        "2",     # Number of fields
        "id", "uuid", "y", "n", "", "", "",
        "email", "string", "n", "y", "n", "", "", "",
        "y",     # Save this entity?
    ])

    def fake_prompt1(*args, **kwargs):
        return next(inputs1)

    def fake_confirm1(*args, **kwargs):
        value = next(inputs1)
        return value.lower() == 'y'

    def fake_intprompt1(*args, **kwargs):
        return int(next(inputs1))

    monkeypatch.setattr("rich.prompt.Prompt.ask", fake_prompt1)
    monkeypatch.setattr("rich.prompt.Confirm.ask", fake_confirm1)
    monkeypatch.setattr("rich.prompt.IntPrompt.ask", fake_intprompt1)

    result1 = runner.invoke(cli_app, ["add_entity", "entity"])
    assert result1.exit_code == 0, f"First CLI call failed: {result1.stdout}\n{result1.stderr}"

    # Second call inputs
    inputs2 = iter([
        "Post", "3",
        "id", "uuid", "y", "n", "", "", "",
        "title", "string", "n", "n", "n", "", "", "",
        "user_id", "uuid", "n", "n", "n", "", "User.id", "index, not null",
        "y",     # Save this entity?
    ])

    def fake_prompt2(*args, **kwargs):
        return next(inputs2)

    def fake_confirm2(*args, **kwargs):
        value = next(inputs2)
        return value.lower() == 'y'

    def fake_intprompt2(*args, **kwargs):
        return int(next(inputs2))

    monkeypatch.setattr("rich.prompt.Prompt.ask", fake_prompt2)
    monkeypatch.setattr("rich.prompt.Confirm.ask", fake_confirm2)
    monkeypatch.setattr("rich.prompt.IntPrompt.ask", fake_intprompt2)

    result2 = runner.invoke(cli_app, ["add_entity", "entity"])
    assert result2.exit_code == 0, f"Second CLI call failed: {result2.stdout}\n{result2.stderr}"

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
