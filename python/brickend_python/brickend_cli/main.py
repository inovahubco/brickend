"""
main.py
"""

import typer

from brickend_cli.commands.init_command import app as init_app
from brickend_cli.commands.add_entity import app as add_entity_app
from brickend_cli.commands.generate_code import app as generate_app


app = typer.Typer()

# Register subcommands
app.add_typer(init_app, name="init")
app.add_typer(add_entity_app, name="add_entity")
app.add_typer(generate_app, name="generate")

if __name__ == "__main__":
    app()
