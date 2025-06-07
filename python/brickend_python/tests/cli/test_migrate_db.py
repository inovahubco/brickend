"""
test_migrate_db.py
"""

import shutil
import sqlite3
from pathlib import Path

import pytest
from typer.testing import CliRunner

from brickend_cli.main import app as cli_app


@pytest.fixture
def project_dir(tmp_path, monkeypatch):
    """
    Create a temporary project directory using the FastAPI skeleton,
    then customize it for migration testing.
    """
    # Find the project root and skeleton directory
    repo_root = Path(__file__).parents[2]
    skeleton_dir = repo_root / "templates" / "skeletons" / "fastapi"

    if not skeleton_dir.exists():
        pytest.skip(f"FastAPI skeleton not found at {skeleton_dir}")

    # Copy the entire skeleton to tmp_path
    shutil.copytree(skeleton_dir, tmp_path, dirs_exist_ok=True)

    # Verify key files exist from skeleton
    alembic_ini = tmp_path / "alembic.ini"
    if not alembic_ini.exists():
        pytest.skip("alembic.ini not found in skeleton")

    env_py = tmp_path / "migrations" / "env.py"
    if not env_py.exists():
        pytest.skip("migrations/env.py not found in skeleton")

    # Ensure app directory structure exists
    app_dir = tmp_path / "app"
    models_dir = app_dir / "models"
    versions_dir = tmp_path / "migrations" / "versions"

    app_dir.mkdir(exist_ok=True)
    models_dir.mkdir(parents=True, exist_ok=True)
    versions_dir.mkdir(parents=True, exist_ok=True)

    # Create or update app/models/__init__.py to ensure it exports what's needed
    models_init = models_dir / "__init__.py"
    if not models_init.exists():
        models_init.write_text("", encoding="utf-8")

    # Create a simple User model for testing (if not exists)
    user_model = models_dir / "user.py"
    if not user_model.exists():
        user_model.write_text(
            """from sqlalchemy import Column, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = "user"
    id = Column(String, primary_key=True)
""".strip(),
            encoding="utf-8",
        )

    # Update models/__init__.py to export Base and User if needed
    current_init_content = models_init.read_text(encoding="utf-8")
    if "Base" not in current_init_content or "User" not in current_init_content:
        # Read the user model to find where Base is imported from
        user_content = user_model.read_text(encoding="utf-8")
        if "from sqlalchemy.ext.declarative import declarative_base" in user_content:
            # Base is defined in user.py
            models_init.write_text(
                """from .user import Base, User

__all__ = ['Base', 'User']
""".strip(),
                encoding="utf-8",
            )
        else:
            models_init.write_text(
                """# Import Base from wherever it's defined in the skeleton
try:
    from app.database import Base
except ImportError:
    from sqlalchemy.ext.declarative import declarative_base
    Base = declarative_base()

from .user import User

__all__ = ['Base', 'User']
""".strip(),
                encoding="utf-8",
            )

    # Ensure database configuration exists
    database_py = app_dir / "database.py"
    if not database_py.exists():
        database_py.write_text(
            """from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
""".strip(),
            encoding="utf-8",
        )

    # Change to the project directory
    monkeypatch.chdir(tmp_path)
    return tmp_path


def test_migrate_creates_initial_revision_and_applies(project_dir):
    """
    Given a fresh project with a User model, running `brickend migrate db`
    should generate an initial Alembic revision under migrations/versions/
    and create the 'user' table in test.db.
    """
    runner = CliRunner()

    # Ensure no revisions exist initially
    versions_dir = project_dir / "migrations" / "versions"
    existing_revisions = list(versions_dir.glob("*.py"))

    # Clean up any existing revision files for a clean test
    for rev_file in existing_revisions:
        rev_file.unlink()

    assert list(versions_dir.glob("*.py")) == []

    # Run migrate db command to generate initial revision
    result = runner.invoke(cli_app, ["migrate", "db"])

    # Print debug info if it fails
    if result.exit_code != 0:
        print("STDOUT:", result.stdout)
        print("STDERR:", result.stderr)
        print("Working directory contents:")
        for item in project_dir.iterdir():
            print(f"  {item.name}")

    assert result.exit_code == 0, f"CLI failed: {result.stdout}\n{result.stderr}"
    assert "Migration" in result.stdout and "created" in result.stdout
    assert "Database upgraded to the latest revision" in result.stdout

    # Check that exactly one revision file was created
    revision_files = list(versions_dir.glob("*.py"))
    assert len(revision_files) == 1, "Expected exactly one revision file."
    revision_file = revision_files[0]
    assert revision_file.stat().st_size > 0, "Revision file should not be empty."

    # Check that SQLite file test.db exists
    db_path = project_dir / "test.db"
    assert db_path.exists(), "test.db should have been created."

    # Verify that 'user' table exists in the new SQLite database
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='user';"
    )
    table = cursor.fetchone()
    conn.close()
    assert table is not None and table[0] == "user", "Table 'user' should exist."


def test_migrate_creates_second_revision_and_handles_no_changes(project_dir):
    """
    After initial migration, modify the User model to add a new column,
    run migrate db again to generate a second revision, then run migrate db a third
    time to confirm no new revision is created.
    """
    runner = CliRunner()

    versions_dir = project_dir / "migrations" / "versions"

    # Clean up any existing revision files
    for rev_file in versions_dir.glob("*.py"):
        rev_file.unlink()

    # First migration (initial)
    result1 = runner.invoke(cli_app, ["migrate", "db"])
    assert result1.exit_code == 0, f"First migration failed: {result1.stdout}\n{result1.stderr}"

    initial_revisions = sorted(p.name for p in versions_dir.glob("*.py"))
    assert len(initial_revisions) == 1

    # Modify app/models/user.py to add a new column "email" (without unique constraint to avoid naming issues)
    user_model = project_dir / "app" / "models" / "user.py"
    user_content = user_model.read_text(encoding="utf-8")

    # Add email column after the id column (simple nullable column)
    new_content = user_content.replace(
        'id = Column(String, primary_key=True)',
        'id = Column(String, primary_key=True)\n    email = Column(String, nullable=True)'
    )
    user_model.write_text(new_content, encoding="utf-8")

    # Run migrate db to generate second revision
    result2 = runner.invoke(cli_app, ["migrate", "db"])
    assert result2.exit_code == 0, f"Second migration failed: {result2.stdout}\n{result2.stderr}"
    out2 = result2.stdout.lower()
    assert "migration" in out2 and "created" in out2

    # Confirm that there are now two revision files
    second_revisions = sorted(p.name for p in versions_dir.glob("*.py"))
    assert len(second_revisions) == 2, "Expected a second revision file after model change."

    # Ensure the new revision filename is not the same as the first
    new_files = set(second_revisions) - set(initial_revisions)
    assert len(new_files) == 1, "Exactly one new revision file should appear."
    new_rev = new_files.pop()
    assert "autogenerated" in new_rev

    # Run migrate db a third time (no model changes) – should report no new revision
    result3 = runner.invoke(cli_app, ["migrate", "db"])
    assert result3.exit_code == 0, f"Third migration failed: {result3.stdout}\n{result3.stderr}"
    out3 = result3.stdout.lower()
    assert "no new revision file found" in out3 or "no changes detected" in out3

    # Confirm that revision count remains two
    final_revisions = sorted(p.name for p in versions_dir.glob("*.py"))
    assert len(final_revisions) == 2, "No additional revision file should be created."
