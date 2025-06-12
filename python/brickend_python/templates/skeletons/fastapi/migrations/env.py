"""
env.py

Alembic environment script for database migrations.

This module:
  - Configures the Alembic context using the application's database URL and metadata.
  - Supports offline and online migration modes.
  - Attempts to import `SQLALCHEMY_DATABASE_URL` and `Base` metadata from the generated app structure,
    with a fallback to legacy `database.py` and `models.py`.
"""

import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context


# Ensure project root is on sys.path
sys.path.append(os.getcwd())

# Import database URL and metadata
try:
    from app.database import SQLALCHEMY_DATABASE_URL
    DATABASE_URL = SQLALCHEMY_DATABASE_URL
    from app.models import Base
except ImportError as e:
    try:
        # Fallback for backward compatibility
        from db import SQLALCHEMY_DATABASE_URL
        DATABASE_URL = SQLALCHEMY_DATABASE_URL
        from models import Base
    except ImportError:
        raise ImportError(
            "Could not import database or models. "
            "Make sure you've generated the project and are on the right path. "
            "Expected: app/database.py and app/models.py or db.py and models.py"
        ) from e

# Alembic Config object
config = context.config
fileConfig(config.config_file_name)

# Set the SQLAlchemy URL in Alembic config
config.set_main_option("sqlalchemy.url", DATABASE_URL)

# Target metadata for autogenerate
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.

    In this mode, Alembic generates SQL scripts without connecting to the database.
    It uses literal binds and batch mode for compatibility with SQLite.

    Raises:
        None
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode.

    In this mode, Alembic opens a connection to the database and applies migrations
    programmatically. Batch mode is enabled for compatibility with SQLite.

    Raises:
        None
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=True,
        )

        with context.begin_transaction():
            context.run_migrations()


# Execute the appropriate migration mode
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
