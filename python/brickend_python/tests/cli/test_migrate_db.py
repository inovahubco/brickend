"""
test_migrate_db.py

Unit tests for the 'migrate db' CLI command in brickend_cli.main,
adapted for the new FastAPI app structure with app/ and migrations/ directories.

This module covers:
  - Initial Alembic revision creation and database upgrade.
  - Generating a second migration after model changes.
  - Handling no-change scenarios (no new revisions).
  - Debugging the migration import environment.
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
    then customize it for migration testing with the correct file structure.

    Args:
        tmp_path (Path): pytest-provided temporary directory.
        monkeypatch: pytest fixture for modifying the working directory.

    Returns:
        Path: Path to the prepared project directory with app/ and migrations/ set up.
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

    migrations_dir = tmp_path / "migrations"
    versions_dir = migrations_dir / "versions"
    env_py = migrations_dir / "env.py"

    migrations_dir.mkdir(exist_ok=True)
    versions_dir.mkdir(parents=True, exist_ok=True)

    # Create or fix the migrations/env.py file for the new structure
    env_py_content = '''"""Alembic environment configuration."""

from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context
import os
import sys

# Add the project directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

try:
    # Try to import from the new structure
    from app.database import SQLALCHEMY_DATABASE_URL, Base
except ImportError:
    try:
        # Fallback to database.py in root
        from database import SQLALCHEMY_DATABASE_URL, Base
    except ImportError:
        try:
            # Fallback to db.py in root
            from db import SQLALCHEMY_DATABASE_URL, Base
        except ImportError:
            raise ImportError(
                "Could not import database configuration. "
                "Make sure you've generated the project and are in the right path. "
                "Expected one of: app/database.py, database.py, or db.py"
            )

try:
    # Try to import models from the new structure
    from app.models import *
except ImportError:
    try:
        # Fallback to models.py in root
        from models import *
    except ImportError:
        # If no models found, that's okay - we'll let Alembic handle it
        pass

# This is the Alembic Config object
config = context.config

# Override the sqlalchemy.url with our DATABASE_URL
config.set_main_option("sqlalchemy.url", SQLALCHEMY_DATABASE_URL)

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set the target metadata
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
'''

    env_py.write_text(env_py_content, encoding="utf-8")

    # Ensure app directory structure exists
    app_dir = tmp_path / "app"
    models_dir = app_dir / "models"
    crud_dir = app_dir / "crud"
    routers_dir = app_dir / "routers"

    app_dir.mkdir(exist_ok=True)
    models_dir.mkdir(parents=True, exist_ok=True)
    crud_dir.mkdir(parents=True, exist_ok=True)
    routers_dir.mkdir(parents=True, exist_ok=True)

    # Create app/__init__.py
    (app_dir / "__init__.py").write_text("", encoding="utf-8")

    # Create or update database configuration
    database_py = app_dir / "database.py"
    database_py.write_text(
        '''"""Database configuration."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """Database dependency."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
'''.strip(),
        encoding="utf-8",
    )

    # Create app/models/__init__.py
    models_init = models_dir / "__init__.py"
    models_init.write_text(
        '''"""Models package."""

from app.database import Base
from .user import User

__all__ = ['Base', 'User']
'''.strip(),
        encoding="utf-8",
    )

    # Create a simple User model for testing
    user_model = models_dir / "user.py"
    user_model.write_text(
        '''"""User model."""

from sqlalchemy import Column, String
from app.database import Base


class User(Base):
    """User model."""
    __tablename__ = "user"
    
    id = Column(String, primary_key=True)
'''.strip(),
        encoding="utf-8",
    )

    # Create basic alembic.ini if it doesn't exist or needs updating
    if not alembic_ini.exists():
        alembic_ini.write_text(
            '''[alembic]
script_location = migrations
prepend_sys_path = .
version_path_separator = os

[post_write_hooks]

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
'''.strip(),
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

    # Debug: Print the project structure
    print("\n=== PROJECT STRUCTURE ===")
    def print_tree(directory, prefix="", max_depth=3, current_depth=0):
        if current_depth >= max_depth:
            return
        items = list(directory.iterdir())
        for i, item in enumerate(items):
            is_last = i == len(items) - 1
            current_prefix = "└── " if is_last else "├── "
            print(f"{prefix}{current_prefix}{item.name}")
            if item.is_dir() and current_depth < max_depth - 1:
                next_prefix = prefix + ("    " if is_last else "│   ")
                print_tree(item, next_prefix, max_depth, current_depth + 1)

    print_tree(project_dir)

    # Check if database.py exists and show its content
    database_file = project_dir / "app" / "database.py"
    if database_file.exists():
        print(f"\n=== DATABASE.PY CONTENT ===")
        print(database_file.read_text(encoding="utf-8")[:500])
    else:
        print("WARNING: app/database.py does not exist!")

    # Check migrations/env.py
    env_file = project_dir / "migrations" / "env.py"
    if env_file.exists():
        print(f"\n=== ENV.PY FIRST 20 LINES ===")
        lines = env_file.read_text(encoding="utf-8").splitlines()
        for i, line in enumerate(lines[:20], 1):
            print(f"{i:2}: {line}")
    else:
        print("WARNING: migrations/env.py does not exist!")

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

    # Modify app/models/user.py to add a new column "email"
    user_model = project_dir / "app" / "models" / "user.py"
    user_content = user_model.read_text(encoding="utf-8")

    # Add email column after the id column
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

    # Run migrate db a third time (no model changes) – should report no new revision
    result3 = runner.invoke(cli_app, ["migrate", "db"])
    assert result3.exit_code == 0, f"Third migration failed: {result3.stdout}\n{result3.stderr}"
    out3 = result3.stdout.lower()
    assert "no new revision file found" in out3 or "no changes detected" in out3

    # Confirm that revision count remains two
    final_revisions = sorted(p.name for p in versions_dir.glob("*.py"))
    assert len(final_revisions) == 2, "No additional revision file should be created."


def test_debug_migration_environment(project_dir):
    """
    Debug test to understand the migration environment setup.
    """
    print("\n=== TESTING IMPORTS ===")

    # Test if we can import the database configuration
    import sys
    sys.path.insert(0, str(project_dir))

    try:
        from app.database import SQLALCHEMY_DATABASE_URL, Base
        print("✅ Successfully imported from app.database")
        print(f"Database URL: {SQLALCHEMY_DATABASE_URL}")
        print(f"Base: {Base}")
    except ImportError as e:
        print(f"❌ Failed to import from app.database: {e}")

    try:
        from app.models import User
        print("✅ Successfully imported User from app.models")
        print(f"User: {User}")
        print(f"User.__tablename__: {User.__tablename__}")
    except ImportError as e:
        print(f"❌ Failed to import User from app.models: {e}")

    # Check file existence
    files_to_check = [
        project_dir / "app" / "database.py",
        project_dir / "app" / "models" / "__init__.py",
        project_dir / "app" / "models" / "user.py",
        project_dir / "migrations" / "env.py",
        project_dir / "alembic.ini"
    ]

    print("\n=== FILE EXISTENCE CHECK ===")
    for file_path in files_to_check:
        exists = file_path.exists()
        print(f"{'✅' if exists else '❌'} {file_path.relative_to(project_dir)}")
        if exists and file_path.suffix == '.py':
            size = file_path.stat().st_size
            print(f"    Size: {size} bytes")
