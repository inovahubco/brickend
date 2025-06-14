"""
init_project.py

CLI command to initialize a new Brickend project based on provided skeleton templates.

This module provides:
  - find_project_root: locate the 'templates/skeletons' directory.
  - init_project: Typer command to copy the chosen skeleton into a new project folder.
"""

import shutil
from pathlib import Path

import typer

app = typer.Typer(add_completion=False)


def find_project_root() -> Path:
    """Locate the project root by finding the 'templates/skeletons' directory.

    Returns:
        Path: Directory path containing 'templates/skeletons'.

    Raises:
        FileNotFoundError: If no 'templates/skeletons' directory is found
            in current or ancestor paths.
    """
    current = Path(__file__).resolve()
    for parent in [current] + list(current.parents):
        candidate = parent / "templates" / "skeletons"
        if candidate.is_dir():
            return parent

    cwd = Path.cwd()
    if (cwd / "templates" / "skeletons").is_dir():
        return cwd

    raise FileNotFoundError("Could not find project root with 'templates/skeletons' directory")


@app.command("project")
def init_project(
    name: str = typer.Argument(..., help="Name of the new Brickend project"),
    project_type: str = typer.Option(
        "fastapi", "--type", "-t", help="Skeleton type: fastapi, django, pulumi"
    ),
) -> None:
    """Create a new Brickend project directory from a skeleton template.

    Args:
        name (str): Name of the directory to create for the new project.
        project_type (str): Skeleton template type to use
            (e.g., 'fastapi', 'django', 'pulumi').

    Raises:
        typer.Exit: If the project root cannot be located, the specified skeleton
            does not exist, the target directory already exists, or copying fails.
    """
    try:
        project_root = find_project_root()
    except FileNotFoundError as e:
        typer.echo(f"Error: {e}")
        raise typer.Exit(code=1)

    skeletons_root = project_root / "templates" / "skeletons"
    chosen_skeleton = skeletons_root / project_type
    if not chosen_skeleton.is_dir():
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
