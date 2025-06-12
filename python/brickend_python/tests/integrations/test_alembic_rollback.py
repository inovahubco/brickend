"""
test_alembic_rollback.py

Integration test for Alembic migrations and rollback functionality in a Brickend FastAPI project.
Covers:
  - Initial project initialization and code generation.
  - Applying two successive Alembic migrations (adding a new column).
  - Verifying the new column exists in SQLite schema.
  - Rolling back a single revision and confirming the column is removed.
"""

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
    and return the path to the SQLite database file.

    Steps:
      1. Run `brickend init project` with the fastapi skeleton.
      2. Generate code for a User entity.
      3. Apply the first migration (initial table creation).
      4. Insert an 'email' column into the User model file.
      5. Apply the second migration to add the new column.
      6. Locate and return the resulting .db file path.

    Args:
        tmp_path (Path): pytest-provided temporary directory for project files.
        monkeypatch: pytest fixture for changing the working directory.

    Returns:
        Path: Path to the created SQLite database file containing both migrations.
    """
    proj = tmp_path / "demo"
    runner = CliRunner()
    result = runner.invoke(cli_app, ["init", "project", str(proj), "--type", "fastapi"])
    assert result.exit_code == 0, f"Init failed: {result.stdout}"

    monkeypatch.chdir(proj)

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

    result = runner.invoke(cli_app,
                           ["generate", "code", "entities.yaml", "--output", ".", "--db-url", "sqlite:///test.db"])
    assert result.exit_code == 0, f"Generate code failed: {result.stdout}"

    result = runner.invoke(cli_app, ["migrate", "db"])
    assert result.exit_code == 0, f"First migration failed: {result.stdout}"

    model_file = None
    for candidate in (Path("app/models.py"), Path("models.py")):
        if candidate.exists():
            model_file = candidate
            break
    assert model_file is not None, f"Model file not found. Files in project: {list(Path('.').rglob('*.py'))}"

    content = model_file.read_text(encoding="utf-8")

    lines = content.splitlines()
    out = []
    inserted = False

    i = 0
    while i < len(lines):
        line = lines[i]
        out.append(line)

        if line.strip().startswith("class User(Base):"):
            while i + 1 < len(lines):
                i += 1
                line = lines[i]
                out.append(line)

                if line.strip().startswith("id = Column("):
                    while i + 1 < len(lines) and not lines[i].strip().endswith(")"):
                        i += 1
                        out.append(lines[i])

                    out.append("    email = Column(String, nullable=False)")
                    inserted = True
                    break
            break
        i += 1

    if not inserted:
        for idx, line in enumerate(lines):
            if line.strip().startswith("class User(Base):"):
                insert_idx = len(lines)
                for j in range(idx + 1, len(lines)):
                    if lines[j].strip() == "" or not lines[j].startswith("    "):
                        insert_idx = j
                        break

                lines.insert(insert_idx, "    email = Column(String, nullable=False)")
                inserted = True
                break

        content = "\n".join(lines)
    else:
        content = "\n".join(out)

    model_file.write_text(content, encoding="utf-8")

    result = runner.invoke(cli_app, ["migrate", "db"])
    assert result.exit_code == 0, f"Second migration failed: {result.stdout}"

    db_files = list(Path('.').rglob('*.db'))

    if not db_files:
        possible_locations = [
            Path("test.db"),
            Path("./test.db"),
            Path("app/test.db"),
            proj / "test.db"
        ]
        for loc in possible_locations:
            if loc.exists():
                db_files = [loc]
                break

    assert db_files, f"No database file found. Files in directory: {list(Path('.').iterdir())}"

    db_file = db_files[0]
    return db_file


def test_rollback_removes_column(sqlite_file):
    """
    After two migrations have added the 'email' column to the users table,
    running `alembic downgrade -1` should remove that column.

    Verifies:
      - The 'email' column exists after the second migration.
      - After downgrading one revision, the 'email' column is no longer present.

    Args:
        sqlite_file (Path): Path to the SQLite database file prepared by the sqlite_file fixture.
    """
    db_path = str(sqlite_file)
    assert Path(db_path).exists()

    conn = sqlite3.connect(db_path)
    cur = conn.execute("PRAGMA table_info(users)")
    cols = [row[1] for row in cur.fetchall()]
    assert "email" in cols, f"'email' column not found after second migration: {cols}"

    alembic_cfg = Config("alembic.ini")
    command.downgrade(alembic_cfg, "-1")

    cur = conn.execute("PRAGMA table_info(users)")
    cols_after = [row[1] for row in cur.fetchall()]
    assert "email" not in cols_after, f"'email' column still present after downgrade: {cols_after}"

    conn.close()
