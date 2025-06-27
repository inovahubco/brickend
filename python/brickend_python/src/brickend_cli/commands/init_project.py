"""
init_project.py

CLI command to initialize a new Brickend project with hybrid configuration support.

This module provides:
  - find_project_root: locate the 'templates/skeletons' directory.
  - init_project: Typer command to create a new project with brickend.yaml + entities.yaml.
  - generate_skeleton: copy and customize skeleton templates.
"""

import shutil
from pathlib import Path
from typing import Optional

import ruamel.yaml
import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from brickend_core.config.project_schema import BrickendProject, ProjectInfo, StackConfig, ProjectSettings, DeployConfig
from brickend_core.utils.yaml_loader import save_project_config

app = typer.Typer(add_completion=False)
console = Console()


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


def get_available_stacks() -> list[str]:
    """Get list of available skeleton stacks.

    Returns:
        List of available stack names from templates/skeletons/
    """
    try:
        project_root = find_project_root()
        skeletons_root = project_root / "templates" / "skeletons"

        if not skeletons_root.exists():
            return ["fastapi"]  # Default fallback

        # Get all directories in skeletons that contain skeleton templates
        stacks = []
        for item in skeletons_root.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                stacks.append(item.name)

        return sorted(stacks) if stacks else ["fastapi"]

    except FileNotFoundError:
        return ["fastapi"]  # Default fallback


def create_project_config(
    name: str,
    stack: str,
    description: Optional[str] = None,
    author: Optional[str] = None
) -> BrickendProject:
    """Create a BrickendProject configuration for a new project.

    Args:
        name: Project name
        stack: Backend stack (fastapi, django, etc.)
        description: Optional project description
        author: Optional author name

    Returns:
        BrickendProject configuration object
    """
    # Determine database based on stack
    database_mapping = {
        "fastapi": "postgresql",
        "django": "postgresql",
        "flask": "postgresql",
        "expressjs": "postgresql",
    }

    return BrickendProject(
        project=ProjectInfo(
            name=name,
            description=description or f"{name} API generated with Brickend",
            version="1.0.0",
            author=author,
            license="MIT"
        ),
        stack=StackConfig(
            back=stack,
            database=database_mapping.get(stack, "postgresql")
        ),
        entities="./entities.yaml",
        settings=ProjectSettings(
            auto_migrations=True,
            api_docs=True,
            cors_enabled=True,
            authentication=False,
            authorization=False
        ),
        deploy=DeployConfig(
            environment="development",
            monitoring=True,
            logging=True
        )
    )


def generate_skeleton(stack: str, project_name: str, target_dir: Path) -> None:
    """Generate project skeleton from templates.

    Args:
        stack: Backend stack type
        project_name: Name of the project
        target_dir: Target directory for the project

    Raises:
        FileNotFoundError: If skeleton template doesn't exist
        PermissionError: If you cannot write to target directory
    """
    try:
        project_root = find_project_root()
    except FileNotFoundError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(code=1)

    skeletons_root = project_root / "templates" / "skeletons"
    chosen_skeleton = skeletons_root / stack

    if not chosen_skeleton.is_dir():
        available_stacks = get_available_stacks()
        console.print(f"[red]Error: No skeleton found for stack '{stack}'.[/red]")
        console.print(f"[yellow]Available stacks: {', '.join(available_stacks)}[/yellow]")
        raise typer.Exit(code=1)

    if target_dir.exists():
        console.print(f"[red]Error: The directory '{project_name}' already exists.[/red]")
        raise typer.Exit(code=1)

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task(f"Copying {stack} skeleton...", total=None)
            shutil.copytree(chosen_skeleton, target_dir)
            progress.update(task, completed=True)

    except Exception as e:
        console.print(f"[red]Failed to copy skeleton: {e}[/red]")
        raise typer.Exit(code=1)


def create_entities_file(target_dir: Path) -> None:
    """Create an empty entities.yaml file.

    Args:
        target_dir: Project directory where to create entities.yaml
    """
    entities_path = target_dir / "entities.yaml"

    yaml = ruamel.yaml.YAML()
    yaml.default_flow_style = False
    yaml.width = 120
    yaml.indent(mapping=2, sequence=4, offset=2)

    # Create empty entities structure with helpful comments
    entities_data = {
        'entities': []
    }

    try:
        with entities_path.open('w', encoding='utf-8') as f:
            f.write("# Entities configuration for Brickend\n")
            f.write("# Define your data models here\n")
            f.write("# Example:\n")
            f.write("# entities:\n")
            f.write("#   - name: User\n")
            f.write("#     fields:\n")
            f.write("#       - name: id\n")
            f.write("#         type: uuid\n")
            f.write("#         primary_key: true\n")
            f.write("#       - name: email\n")
            f.write("#         type: string\n")
            f.write("#         unique: true\n")
            f.write("\n")
            yaml.dump(entities_data, f)

    except Exception as e:
        console.print(f"[red]Failed to create entities.yaml: {e}[/red]")
        raise typer.Exit(code=1)


def customize_skeleton_files(target_dir: Path, project_name: str, stack: str) -> None:
    """Customize skeleton files with project-specific information.

    Args:
        target_dir: Project directory
        project_name: Name of the project
        stack: Backend stack type
    """
    try:
        # Customize README.md if it exists
        readme_path = target_dir / "README.md"
        if readme_path.exists():
            content = readme_path.read_text(encoding='utf-8')
            # Replace placeholder project name
            content = content.replace("{{project_name}}", project_name)
            content = content.replace("{{stack}}", stack)
            readme_path.write_text(content, encoding='utf-8')

        # Add .gitignore if it doesn't exist
        gitignore_path = target_dir / ".gitignore"
        if not gitignore_path.exists():
            gitignore_content = """
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
env.bak/
venv.bak/

# IDEs
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Logs
*.log
logs/

# Database
*.db
*.sqlite3

# Environment variables
.env
.env.local
.env.production

# Brickend
templates_user/
"""
            gitignore_path.write_text(gitignore_content.strip(), encoding='utf-8')

    except Exception as e:
        console.print(f"[yellow]Warning: Could not customize skeleton files: {e}[/yellow]")


@app.command("project")
def init_project(
    name: str = typer.Argument(..., help="Name of the new Brickend project"),
    stack: str = typer.Option(
        "fastapi", "--stack", "-s", help="Backend stack: fastapi, django, etc."
    ),
    description: Optional[str] = typer.Option(
        None, "--description", "-d", help="Project description"
    ),
    author: Optional[str] = typer.Option(
        None, "--author", "-a", help="Author name"
    ),
    # Maintain backward compatibility with the original parameter
    project_type: Optional[str] = typer.Option(
        None, "--type", "-t", help="[DEPRECATED] Use --stack instead", hidden=True
    ),
) -> None:
    """Create a new Brickend project with hybrid configuration support.

    This command creates:
    - brickend.yaml: Main configuration file with project settings
    - entities.yaml: Empty entities file (referenced by brickend.yaml)
    - Project skeleton: Stack-specific template files
    - Customized files: README, .gitignore, etc.

    Args:
        name: Name of the directory to create for the new project
        stack: Backend stack type (fastapi, django, etc.)
        description: Optional project description
        author: Optional author name
        project_type: [DEPRECATED] Legacy parameter for backward compatibility

    Examples:
        brickend init my-api --stack fastapi --author "John Doe"
        brickend init blog-api --stack django --description "Blog API with Django"
    """
    # Handle backward compatibility
    if project_type is not None:
        console.print("[yellow]Warning: --type is deprecated, use --stack instead[/yellow]")
        stack = project_type

    # Validate project name
    if not name.replace('_', '').replace('-', '').isalnum():
        console.print("[red]Error: Project name must contain only letters, numbers, hyphens, and underscores[/red]")
        raise typer.Exit(code=1)

    if len(name) < 2:
        console.print("[red]Error: Project name must be at least 2 characters long[/red]")
        raise typer.Exit(code=1)

    # Validate stack
    available_stacks = get_available_stacks()
    if stack not in available_stacks:
        console.print(f"[red]Error: Stack '{stack}' is not available.[/red]")
        console.print(f"[yellow]Available stacks: {', '.join(available_stacks)}[/yellow]")
        raise typer.Exit(code=1)

    target_dir = Path.cwd() / name

    console.print(Panel(
        f"[bold blue]Initializing Brickend project[/bold blue]\n\n"
        f"[bold]Project:[/bold] {name}\n"
        f"[bold]Stack:[/bold] {stack}\n"
        f"[bold]Directory:[/bold] {target_dir}",
        title="🚀 Brickend Init",
        border_style="blue"
    ))

    try:
        # 1. Generate project skeleton
        generate_skeleton(stack, name, target_dir)

        # 2. Create project configuration
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            config_task = progress.add_task("Creating configuration files...", total=None)

            config = create_project_config(name, stack, description, author)

            # 3. Save brickend.yaml
            brickend_path = target_dir / "brickend.yaml"
            save_project_config(config, brickend_path)

            # 4. Create entities.yaml
            create_entities_file(target_dir)

            progress.update(config_task, completed=True)

        # 5. Customize skeleton files
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            custom_task = progress.add_task("Customizing project files...", total=None)
            customize_skeleton_files(target_dir, name, stack)
            progress.update(custom_task, completed=True)

        # Success message
        console.print(Panel(
            f"[bold green]✅ Project '{name}' created successfully![/bold green]\n\n"
            f"[bold]Files created:[/bold]\n"
            f"  📄 brickend.yaml - Main configuration\n"
            f"  📄 entities.yaml - Data models (empty)\n"
            f"  📁 Project skeleton - {stack} template\n"
            f"  📄 README.md - Documentation\n"
            f"  📄 .gitignore - Git ignore rules\n\n"
            f"[bold]Next steps:[/bold]\n"
            f"  1. cd {name}\n"
            f"  2. Edit entities.yaml to define your data models\n"
            f"  3. Run: brickend generate\n"
            f"  4. Run: brickend validate",
            title="🎉 Success",
            border_style="green"
        ))

    except typer.Exit:
        # Re-raise typer exits (already handled)
        raise
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]")
        # Clean up on failure
        if target_dir.exists():
            try:
                shutil.rmtree(target_dir)
                console.print(f"[yellow]Cleaned up incomplete project directory[/yellow]")
            except Exception:
                pass
        raise typer.Exit(code=1)
