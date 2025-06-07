"""
init_project.py
"""

import shutil
from pathlib import Path

import typer


app = typer.Typer(add_completion=False)


def find_project_root() -> Path:
    """
    Find the project root by looking for the 'templates/skeletons' directory.
    Traverse upwards from this file until found; otherwise, check cwd.
    Raises FileNotFoundError if not found.
    """
    current = Path(__file__).resolve()
    for parent in [current] + list(current.parents):
        candidate = parent / "templates" / "skeletons"
        if candidate.exists() and candidate.is_dir():
            return parent

    cwd = Path.cwd()
    if (cwd / "templates" / "skeletons").exists():
        return cwd

    raise FileNotFoundError("Could not find project root with 'templates/skeletons' directory")


@app.command("project")
def init_project(
    name: str = typer.Argument(..., help="Name of the new Brickend project"),
    project_type: str = typer.Option(
        "fastapi", "--type", "-t", help="Skeleton type: fastapi, django, pulumi"
    ),
) -> None:
    """
    Initialize a new Brickend project of the given type by copying
    the corresponding skeleton folder into a new directory named 'name'.
    """
    try:
        project_root = find_project_root()
    except FileNotFoundError as e:
        typer.echo(f"Error: {e}")
        raise typer.Exit(code=1)

    skeletons_root = project_root / "templates" / "skeletons"
    chosen_skeleton = skeletons_root / project_type

    if not chosen_skeleton.exists() or not chosen_skeleton.is_dir():
        typer.echo(f"Error: No skeleton found for type '{project_type}'.")
        raise typer.Exit(code=1)

    target_dir = Path.cwd() / name
    if target_dir.exists():
        typer.echo(f"Error: The folder '{name}' already exists.")
        raise typer.Exit(code=1)

    try:
        shutil.copytree(chosen_skeleton, target_dir)
    except Exception as e:
        typer.echo(f"Failed to copy skeleton: {e}")
        raise typer.Exit(code=1)

    typer.echo(f"✅ Project '{name}' created using skeleton '{project_type}'.")
