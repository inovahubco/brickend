"""
main.py

CLI entrypoint that aggregates Brickend CLI subcommands: migrate, init, add_entity, generate, and validate.
"""

import typer

from brickend_cli.commands.init_project import app as init_app
from brickend_cli.commands.add_entity import app as add_entity_app
from brickend_cli.commands.generate_code import app as generate_code_app
from brickend_cli.commands.migrate_db import app as migrate_db_app
from brickend_cli.commands.validate import validate

app = typer.Typer()

app.add_typer(migrate_db_app, name="migrate")
app.add_typer(init_app, name="init")
app.add_typer(add_entity_app, name="add_entity")
app.add_typer(generate_code_app, name="generate")

app.command()(validate)


if __name__ == "__main__":
    app()
