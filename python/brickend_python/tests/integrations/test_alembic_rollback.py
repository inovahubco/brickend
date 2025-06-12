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
    result = runner.invoke(cli_app,
                           ["generate", "code", "entities.yaml", "--output", ".", "--db-url", "sqlite:///test.db"])
    assert result.exit_code == 0, f"Generate code failed: {result.stdout}"

    result = runner.invoke(cli_app, ["migrate", "db"])
    assert result.exit_code == 0, f"First migration failed: {result.stdout}"

    # 5. Detect model file location
    model_file = None
    for candidate in (Path("app/models.py"), Path("models.py")):
        if candidate.exists():
            model_file = candidate
            break
    assert model_file is not None, f"Model file not found. Files in project: {list(Path('.').rglob('*.py'))}"

    # 6. Append a new column 'email' into that file
    content = model_file.read_text(encoding="utf-8")

    # Buscar la clase User y agregar el campo después de la definición completa del id
    lines = content.splitlines()
    out = []
    inserted = False

    i = 0
    while i < len(lines):
        line = lines[i]
        out.append(line)

        # Si encontramos la clase User, buscar el final del campo id
        if line.strip().startswith("class User(Base):"):
            # Avanzar hasta encontrar el campo id
            while i + 1 < len(lines):
                i += 1
                line = lines[i]
                out.append(line)

                # Si encontramos el inicio del campo id, avanzar hasta su final
                if line.strip().startswith("id = Column("):
                    # Avanzar hasta encontrar el cierre del paréntesis del Column
                    while i + 1 < len(lines) and not lines[i].strip().endswith(")"):
                        i += 1
                        out.append(lines[i])

                    # Ahora insertar el campo email (sin unique para evitar problemas con SQLite)
                    out.append("    email = Column(String, nullable=False)")
                    inserted = True
                    break
            break
        i += 1

    # Si no pudimos insertar, agregar al final de la clase
    if not inserted:
        # Buscar la clase User y agregar al final
        for idx, line in enumerate(lines):
            if line.strip().startswith("class User(Base):"):
                # Buscar una línea vacía después de la clase o el final del archivo
                insert_idx = len(lines)
                for j in range(idx + 1, len(lines)):
                    if lines[j].strip() == "" or not lines[j].startswith("    "):
                        insert_idx = j
                        break

                # Insertar antes de esa línea (sin unique para evitar problemas con SQLite)
                lines.insert(insert_idx, "    email = Column(String, nullable=False)")
                inserted = True
                break

        content = "\n".join(lines)
    else:
        content = "\n".join(out)

    model_file.write_text(content, encoding="utf-8")

    # 7. Generate second migration
    result = runner.invoke(cli_app, ["migrate", "db"])
    assert result.exit_code == 0, f"Second migration failed: {result.stdout}"

    # Find the actual database file
    db_files = list(Path('.').rglob('*.db'))

    if not db_files:
        # Try different possible locations
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
    After two migrations, downgrade by one should remove the 'email' column.
    """
    db_path = str(sqlite_file)
    assert Path(db_path).exists()

    # 1. Verify 'email' column exists
    conn = sqlite3.connect(db_path)
    cur = conn.execute("PRAGMA table_info(users)")  # ← CAMBIO: users en lugar de user (por el plural fix)
    cols = [row[1] for row in cur.fetchall()]
    assert "email" in cols, f"'email' column not found after second migration: {cols}"

    # 2. Perform downgrade -1
    alembic_cfg = Config("alembic.ini")
    command.downgrade(alembic_cfg, "-1")

    # 3. Verify 'email' column is gone
    cur = conn.execute("PRAGMA table_info(users)")  # ← CAMBIO: users en lugar de user
    cols_after = [row[1] for row in cur.fetchall()]
    assert "email" not in cols_after, f"'email' column still present after downgrade: {cols_after}"

    conn.close()
