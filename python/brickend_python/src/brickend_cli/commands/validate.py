"""
validate.py

CLI command to validate Brickend project configuration.

This module provides a comprehensive validation command that checks:
  - Project configuration file integrity (brickend.yaml or entities.yaml)
  - Entity definitions and Pydantic schema compliance
  - Stack availability and template existence
  - File system consistency and permissions
  - Configuration completeness and best practices
"""

import typer
from pathlib import Path
from typing import List, Dict, Any, Tuple
from enum import Enum

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import box

from brickend_core.utils.yaml_loader import load_project_config
from brickend_core.engine.template_registry import TemplateRegistry
from brickend_core.engine.template_engine import TemplateEngine
from brickend_core.config.project_schema import BrickendProject
from brickend_core.config.validation_schemas import EntitiesFile

app = typer.Typer(add_completion=False)
console = Console()


class ValidationLevel(str, Enum):
    """Validation severity levels."""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    SUCCESS = "success"


class ValidationResult:
    """Container for validation results."""

    def __init__(self):
        self.issues: List[Tuple[ValidationLevel, str, str]] = []
        self.stats: Dict[str, Any] = {}

    def add_issue(self, level: ValidationLevel, category: str, message: str):
        """Add a validation issue."""
        self.issues.append((level, category, message))

    def add_success(self, category: str, message: str):
        """Add a success message."""
        self.add_issue(ValidationLevel.SUCCESS, category, message)

    def add_error(self, category: str, message: str):
        """Add an error."""
        self.add_issue(ValidationLevel.ERROR, category, message)

    def add_warning(self, category: str, message: str):
        """Add a warning."""
        self.add_issue(ValidationLevel.WARNING, category, message)

    def add_info(self, category: str, message: str):
        """Add an info message."""
        self.add_issue(ValidationLevel.INFO, category, message)

    def has_errors(self) -> bool:
        """Check if there are any errors."""
        return any(level == ValidationLevel.ERROR for level, _, _ in self.issues)

    def has_warnings(self) -> bool:
        """Check if there are any warnings."""
        return any(level == ValidationLevel.WARNING for level, _, _ in self.issues)

    def get_summary(self) -> Dict[str, int]:
        """Get summary count of issues by level."""
        summary = {level.value: 0 for level in ValidationLevel}
        for level, _, _ in self.issues:
            summary[level.value] += 1
        return summary


def find_project_root() -> Path:
    """Find the project root containing brickend_core."""
    current = Path(__file__).resolve()

    # Try to find src/brickend_core (development structure)
    for parent in [current] + list(current.parents):
        if (parent / "src" / "brickend_core").is_dir():
            return parent / "src"
        if (parent / "brickend_core").is_dir():
            return parent

    # Check current working directory
    cwd = Path.cwd()
    if (cwd / "src" / "brickend_core").is_dir():
        return cwd / "src"
    if (cwd / "brickend_core").is_dir():
        return cwd

    raise FileNotFoundError("Could not find project root with brickend_core directory")


def validate_project_configuration(result: ValidationResult) -> BrickendProject:
    """Validate project configuration file."""
    try:
        config = load_project_config()
        result.add_success("Configuration", "Project configuration loaded successfully")

        # Validate configuration completeness
        if not config.project.name:
            result.add_warning("Configuration", "Project name is empty")
        elif len(config.project.name) < 2:
            result.add_warning("Configuration", "Project name is very short")
        else:
            result.add_success("Configuration", f"Project name: {config.project.name}")

        if not config.project.description:
            result.add_info("Configuration", "Consider adding a project description")

        if not config.project.author:
            result.add_info("Configuration", "Consider adding an author name")

        # Validate stack configuration
        if config.stack.back:
            result.add_success("Stack", f"Backend stack: {config.stack.back}")
        else:
            result.add_error("Stack", "No backend stack specified")

        if config.stack.database:
            result.add_success("Stack", f"Database: {config.stack.database}")
        else:
            result.add_warning("Stack", "No database specified")

        # Validate entities configuration
        if isinstance(config.entities, str):
            # External entities file
            entities_path = config.get_entities_file_path()
            if entities_path and entities_path.exists():
                result.add_success("Entities", f"External entities file: {entities_path}")
            else:
                result.add_error("Entities", f"External entities file not found: {entities_path}")
        elif isinstance(config.entities, list):
            if config.entities:
                result.add_success("Entities", f"Inline entities: {len(config.entities)} defined")
            else:
                result.add_warning("Entities", "No entities defined")

        return config

    except FileNotFoundError as e:
        result.add_error("Configuration", f"Configuration file not found: {e}")
        raise
    except Exception as e:
        result.add_error("Configuration", f"Configuration validation failed: {e}")
        raise


def validate_entities(config: BrickendProject, result: ValidationResult) -> None:
    """Validate entity definitions."""
    try:
        if not config.entities:
            result.add_warning("Entities", "No entities defined in the project")
            return

        # Get entities as list
        if isinstance(config.entities, str):
            # Load external entities file
            entities_path = config.get_entities_file_path()
            if entities_path and entities_path.exists():
                import ruamel.yaml
                yaml = ruamel.yaml.YAML(typ="safe")
                with entities_path.open("r", encoding="utf-8") as f:
                    entities_data = yaml.load(f)
                entities_file = EntitiesFile.model_validate(entities_data)
                entities = entities_file.entities
            else:
                result.add_error("Entities", "Cannot load external entities file")
                return
        else:
            entities = config.entities

        # Validate each entity
        entity_names = set()
        total_fields = 0

        for entity in entities:
            # Check for duplicate entity names
            if entity.name in entity_names:
                result.add_error("Entities", f"Duplicate entity name: {entity.name}")
            else:
                entity_names.add(entity.name)
                result.add_success("Entities", f"Entity '{entity.name}' is valid")

            # Validate fields
            if not entity.fields:
                result.add_error("Entities", f"Entity '{entity.name}' has no fields")
                continue

            field_names = set()
            has_primary_key = False

            for field in entity.fields:
                # Check for duplicate field names
                if field.name in field_names:
                    result.add_error("Entities", f"Duplicate field name '{field.name}' in entity '{entity.name}'")
                else:
                    field_names.add(field.name)

                # Check for primary key
                if field.primary_key:
                    if has_primary_key:
                        result.add_warning("Entities", f"Multiple primary keys in entity '{entity.name}'")
                    has_primary_key = True

                # Validate foreign key format
                if field.foreign_key:
                    if "." not in field.foreign_key:
                        result.add_warning("Entities",
                                           f"Foreign key '{field.foreign_key}' should use format 'Entity.field'")

                total_fields += 1

            if not has_primary_key:
                result.add_error("Entities", f"Entity '{entity.name}' has no primary key field")

        # Summary statistics
        result.stats["entity_count"] = len(entities)
        result.stats["total_fields"] = total_fields
        result.add_success("Entities", f"Total: {len(entities)} entities, {total_fields} fields")

    except Exception as e:
        result.add_error("Entities", f"Entity validation failed: {e}")


def validate_stack_availability(config: BrickendProject, result: ValidationResult) -> Tuple[TemplateRegistry, TemplateEngine]:
    """Validate that the configured stack is available."""
    try:
        project_root = find_project_root()
        base_path = project_root / "brickend_core"

        # Initialize template system
        template_registry = TemplateRegistry(base_path=base_path)
        template_engine = TemplateEngine(base_path=base_path)

        result.add_success("Templates", "Template system initialized successfully")

        # Check if stack is available
        integrations = template_registry.discover_integrations(base_path)

        if "back" not in integrations:
            result.add_error("Stack", "No backend integrations found")
            return template_registry, template_engine

        available_stacks = integrations["back"]

        if config.stack.back not in available_stacks:
            result.add_error("Stack", f"Stack '{config.stack.back}' not available")
            result.add_info("Stack", f"Available stacks: {', '.join(available_stacks)}")
        else:
            result.add_success("Stack", f"Stack '{config.stack.back}' is available")
            result.add_info("Stack", f"Available stacks: {', '.join(available_stacks)}")

        return template_registry, template_engine

    except Exception as e:
        result.add_error("Stack", f"Stack validation failed: {e}")
        raise


def validate_templates(config: BrickendProject, template_registry: TemplateRegistry, template_engine: TemplateEngine, result: ValidationResult) -> None:
    """Validate that required templates exist for the stack."""
    try:
        stack = config.stack.back

        # Get available components for this stack
        try:
            components = template_registry.get_available_components("back", stack)
            if components:
                result.add_success("Templates", f"Found {len(components)} template components for {stack}")
                result.add_info("Templates", f"Components: {', '.join(components)}")
            else:
                result.add_warning("Templates", f"No template components found for stack '{stack}'")
        except Exception:
            # Fallback to checking common templates
            components = ["models", "schemas", "crud", "router", "main", "db"]
            result.add_info("Templates", "Using fallback component list for validation")

        # Check each component template
        found_templates = []
        missing_templates = []

        for component in components:
            try:
                template_path = template_engine.get_template_path("back", stack, component)
                found_templates.append(component)

                # Check if it's a user override
                if template_engine.has_user_template("back", stack, component):
                    result.add_info("Templates", f"Template '{component}' has user override")

            except FileNotFoundError:
                missing_templates.append(component)

        if found_templates:
            result.add_success("Templates", f"Found templates: {', '.join(found_templates)}")

        if missing_templates:
            result.add_warning("Templates", f"Missing templates: {', '.join(missing_templates)}")

        # Check for user template directory
        user_templates_dir = template_engine.user_templates_dir
        if user_templates_dir.exists():
            user_stack_dir = user_templates_dir / "back" / stack
            if user_stack_dir.exists():
                user_templates = list(user_stack_dir.glob("*_template.j2"))
                if user_templates:
                    result.add_info("Templates", f"Found {len(user_templates)} user template overrides")

        result.stats["found_templates"] = len(found_templates)
        result.stats["missing_templates"] = len(missing_templates)

    except Exception as e:
        result.add_error("Templates", f"Template validation failed: {e}")


def validate_file_system(config: BrickendProject, result: ValidationResult) -> None:
    """Validate file system permissions and structure."""
    try:
        # Check current directory permissions
        current_dir = Path.cwd()
        if not current_dir.exists():
            result.add_error("FileSystem", "Current directory does not exist")
            return

        # Check write permissions
        test_file = current_dir / ".brickend_test"
        try:
            test_file.write_text("test")
            test_file.unlink()
            result.add_success("FileSystem", "Write permissions verified")
        except Exception:
            result.add_error("FileSystem", "No write permissions in current directory")

        # Check configuration file
        config_file = Path("brickend.yaml")
        if config_file.exists():
            if config_file.is_file():
                result.add_success("FileSystem", "brickend.yaml is accessible")
            else:
                result.add_error("FileSystem", "brickend.yaml exists but is not a file")

        # Check entities file (if external)
        if isinstance(config.entities, str):
            entities_path = config.get_entities_file_path()
            if entities_path:
                if entities_path.exists():
                    if entities_path.is_file():
                        result.add_success("FileSystem", f"Entities file {entities_path} is accessible")
                    else:
                        result.add_error("FileSystem", f"Entities path {entities_path} exists but is not a file")
                else:
                    result.add_error("FileSystem", f"Entities file {entities_path} does not exist")

        # Check common directories
        common_dirs = ["app", "templates_user", ".git"]
        for dir_name in common_dirs:
            dir_path = current_dir / dir_name
            if dir_path.exists():
                if dir_path.is_dir():
                    result.add_info("FileSystem", f"Directory {dir_name}/ exists")
                else:
                    result.add_warning("FileSystem", f"{dir_name} exists but is not a directory")

    except Exception as e:
        result.add_error("FileSystem", f"File system validation failed: {e}")


def display_validation_results(result: ValidationResult) -> None:
    """Display validation results in a nice format."""
    summary = result.get_summary()

    # Summary panel
    summary_text = []
    if summary[ValidationLevel.SUCCESS.value] > 0:
        summary_text.append(f"[green]✅ {summary[ValidationLevel.SUCCESS.value]} successful checks[/green]")
    if summary[ValidationLevel.WARNING.value] > 0:
        summary_text.append(f"[yellow]⚠️  {summary[ValidationLevel.WARNING.value]} warnings[/yellow]")
    if summary[ValidationLevel.ERROR.value] > 0:
        summary_text.append(f"[red]❌ {summary[ValidationLevel.ERROR.value]} errors[/red]")
    if summary[ValidationLevel.INFO.value] > 0:
        summary_text.append(f"[blue]ℹ️  {summary[ValidationLevel.INFO.value]} info items[/blue]")

    console.print(Panel(
        "\n".join(summary_text),
        title="📊 Validation Summary",
        border_style="blue"
    ))

    # Detailed results table
    if result.issues:
        table = Table(box=box.ROUNDED)
        table.add_column("Level", style="bold")
        table.add_column("Category", style="cyan")
        table.add_column("Message")

        # Group by level for better display
        level_styles = {
            ValidationLevel.SUCCESS: "green",
            ValidationLevel.WARNING: "yellow",
            ValidationLevel.ERROR: "red",
            ValidationLevel.INFO: "blue"
        }

        level_icons = {
            ValidationLevel.SUCCESS: "✅",
            ValidationLevel.WARNING: "⚠️",
            ValidationLevel.ERROR: "❌",
            ValidationLevel.INFO: "ℹ️"
        }

        for level, category, message in result.issues:
            icon = level_icons[level]
            style = level_styles[level]
            table.add_row(
                f"[{style}]{icon}[/{style}]",
                f"[bold]{category}[/bold]",
                message
            )

        console.print(table)

    # Statistics
    if result.stats:
        stats_table = Table(title="📈 Project Statistics", box=box.SIMPLE)
        stats_table.add_column("Metric", style="cyan")
        stats_table.add_column("Value", style="green")

        for key, value in result.stats.items():
            formatted_key = key.replace("_", " ").title()
            stats_table.add_row(formatted_key, str(value))

        console.print(stats_table)


@app.command()
def validate(
        config_path: Path = typer.Option(
            Path("brickend.yaml"), "--config", "-c", help="Path to brickend.yaml configuration file"
        ),
        verbose: bool = typer.Option(
            False, "--verbose", "-v", help="Show detailed validation information"
        ),
        warnings_as_errors: bool = typer.Option(
            False, "--strict", help="Treat warnings as errors (exit with non-zero code)"
        ),
) -> None:
    """
    Validate Brickend project configuration and setup.

    Performs comprehensive validation of:
    - Project configuration (brickend.yaml or entities.yaml)
    - Entity definitions and schema compliance
    - Stack availability and template existence
    - File system permissions and structure

    Examples:
        brickend validate                    # Validate current project
        brickend validate --verbose          # Show detailed information
        brickend validate --strict           # Treat warnings as errors
    """

    console.print(Panel(
        "[bold blue]Brickend Project Validation[/bold blue]\n"
        "Checking project configuration, entities, and templates...",
        title="🔍 Validate",
        border_style="blue"
    ))

    result = ValidationResult()

    try:
        with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
        ) as progress:

            # Step 1: Validate project configuration
            task = progress.add_task("Validating project configuration...", total=None)
            config = validate_project_configuration(result)
            progress.update(task, completed=True)

            # Step 2: Validate entities
            task = progress.add_task("Validating entities...", total=None)
            validate_entities(config, result)
            progress.update(task, completed=True)

            # Step 3: Validate stack availability
            task = progress.add_task("Checking stack availability...", total=None)
            template_registry, template_engine = validate_stack_availability(config, result)
            progress.update(task, completed=True)

            # Step 4: Validate templates
            task = progress.add_task("Validating templates...", total=None)
            validate_templates(config, template_registry, template_engine, result)
            progress.update(task, completed=True)

            # Step 5: Validate file system
            task = progress.add_task("Checking file system...", total=None)
            validate_file_system(config, result)
            progress.update(task, completed=True)

    except Exception as e:
        console.print(f"[red]Validation failed: {e}[/red]")
        raise typer.Exit(code=1)

    # Display results
    display_validation_results(result)

    # Determine exit code
    exit_code = 0
    if result.has_errors():
        exit_code = 1
        console.print(Panel(
            "[bold red]❌ Validation failed with errors[/bold red]\n"
            "Fix the errors above before proceeding with code generation.",
            border_style="red"
        ))
    elif warnings_as_errors and result.has_warnings():
        exit_code = 1
        console.print(Panel(
            "[bold yellow]⚠️ Validation failed (warnings treated as errors)[/bold yellow]\n"
            "Address the warnings above or run without --strict flag.",
            border_style="yellow"
        ))
    else:
        if result.has_warnings():
            console.print(Panel(
                "[bold green]✅ Validation passed with warnings[/bold green]\n"
                "Consider addressing the warnings for best practices.",
                border_style="green"
            ))
        else:
            console.print(Panel(
                "[bold green]✅ Validation passed successfully![/bold green]\n"
                "Your project configuration is ready for code generation.",
                border_style="green"
            ))

    if exit_code != 0:
        raise typer.Exit(code=exit_code)
