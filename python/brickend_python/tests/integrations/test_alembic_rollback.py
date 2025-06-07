# tests/integrations/test_alembic_rollback.py

import sqlite3
import pytest
from pathlib import Path
from typer.testing import CliRunner
from alembic.config import Config
from alembic import command
import ruamel.yaml

from brickend_cli.main import app as cli_app


@pytest.fixture
def sqlite_file(tmp_path, monkeypatch):
    """
    Initialize a Brickend FastAPI project, generate two Alembic revisions,
    and return the path to the SQLite file.
    """
    # 1. Init project
    proj = tmp_path / "demo"
    runner = CliRunner()
    result = runner.invoke(cli_app, ["init", "project", str(proj), "--type", "fastapi"])
    assert result.exit_code == 0, f"Init failed: {result.stdout}"
    # 2. Enter project dir
    monkeypatch.chdir(proj)

    # 3. Write a minimal entities.yaml
    yaml = ruamel.yaml.YAML()
    yaml.dump(
        {
            "entities": [
                {
                    "name": "User",
                    "fields": [
                        {
                            "name": "id",
                            "type": "uuid",
                            "primary_key": True,
                            "unique": True,
                            "nullable": False,
                        }
                    ],
                }
            ]
        },
        open("entities.yaml", "w", encoding="utf-8"),
    )

    # 4. Generate code and first migration
    runner.invoke(cli_app, ["generate", "code", "entities.yaml", "--output", ".", "--db-url", "sqlite:///test.db"])
    runner.invoke(cli_app, ["migrate", "db"])

    # 5. Detect dónde está el modelo User
    model_file = None
    for candidate in (Path("app/models/user.py"), Path("models.py")):
        if candidate.exists():
            model_file = candidate
            break
    assert model_file is not None, "Model file not found (app/models/user.py or models.py)"

    # 6. Append a new column 'email' into that file
    content = model_file.read_text(encoding="utf-8")
    if model_file.name == "user.py":
        # Single-entity file: insert under class definition
        insertion = "\n    email = Column(String, unique=True, nullable=False)\n"
        content += insertion
    else:
        # Flat models.py: find class User and insert below it
        lines = content.splitlines()
        out = []
        inserted = False
        for line in lines:
            out.append(line)
            if line.strip().startswith("class User"):
                # next non-empty line is where to insert
                out.append("    email = Column(String, unique=True, nullable=False)")
                inserted = True
        content = "\n".join(out) + ("\n" if not content.endswith("\n") else "")
        assert inserted, "Failed to insert email column into models.py"
    model_file.write_text(content, encoding="utf-8")

    # 7. Generate second migration
    runner.invoke(cli_app, ["migrate", "db"])

    return proj / "test.db"


def test_rollback_removes_column(sqlite_file):
    """
    After two migrations, downgrade by one should remove the 'email' column.
    """
    db_path = str(sqlite_file)
    assert Path(db_path).exists()

    # 1. Verify 'email' column exists
    conn = sqlite3.connect(db_path)
    cur = conn.execute("PRAGMA table_info(users)")
    cols = [row[1] for row in cur.fetchall()]
    assert "email" in cols, f"'email' column not found after second migration: {cols}"

    # 2. Perform downgrade -1
    alembic_cfg = Config("alembic.ini")
    command.downgrade(alembic_cfg, "-1")

    # 3. Verify 'email' column is gone
    cur = conn.execute("PRAGMA table_info(users)")
    cols_after = [row[1] for row in cur.fetchall()]
    assert "email" not in cols_after, f"'email' column still present after downgrade: {cols_after}"

    conn.close()
