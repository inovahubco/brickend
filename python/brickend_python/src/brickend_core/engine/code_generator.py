"""
code_generator.py

Defines CodeGenerator with protected regions support, which uses a TemplateEngine
and TemplateRegistry to render Jinja2 templates into Python code files for a given
integration while preserving protected code regions.
"""

from pathlib import Path
from typing import Any, Dict, List

from brickend_core.engine.template_engine import TemplateEngine
from brickend_core.engine.template_registry import TemplateRegistry
from brickend_core.engine.protected_regions import SmartProtectedRegionsHandler


class CodeGenerator:
    """
    CodeGenerator renders project files (models, schemas, CRUD, routers, main, database)
    for a specified integration (e.g., "fastapi"), using Jinja2 templates and a context
    built by ContextBuilder, while preserving protected code regions.

    All files are generated inside the app/ directory to match FastAPI conventions
    and template import expectations.
    """

    MODELS_TEMPLATE: str = "models_template.j2"
    SCHEMAS_TEMPLATE: str = "schemas_template.j2"
    CRUD_TEMPLATE: str = "crud_template.j2"
    ROUTER_TEMPLATE: str = "router_template.j2"
    MAIN_TEMPLATE: str = "main_template.j2"
    DB_TEMPLATE: str = "db_template.j2"

    MODELS_FILENAME: str = "models.py"
    SCHEMAS_FILENAME: str = "schemas.py"
    CRUD_FILENAME: str = "crud.py"
    ROUTER_FILENAME: str = "router.py"
    MAIN_FILENAME: str = "main.py"
    DATABASE_FILENAME: str = "database.py"  # Changed from "db.py" to match template imports

    def __init__(
        self,
        template_engine: TemplateEngine,
        template_registry: TemplateRegistry,
        output_dir: Path,
        preserve_protected_regions: bool = True,
    ) -> None:
        """
        Initialize CodeGenerator.

        Args:
            template_engine (TemplateEngine): Jinja2 engine to render templates.
            template_registry (TemplateRegistry): Registry of available templates.
            output_dir (Path): Directory where generated files will be written.
            preserve_protected_regions (bool): Whether to preserve protected regions during regeneration.
        """
        self.template_engine = template_engine
        self.template_registry = template_registry
        self.output_dir = output_dir
        self.preserve_protected_regions = preserve_protected_regions
        self.protected_handler = (
            SmartProtectedRegionsHandler() if preserve_protected_regions else None
        )

    def generate_project(self, context: Dict[str, Any], integration_key: str) -> None:
        """
        Generate all code files for the given integration using the provided context.

        This method will:
          1. Ensure the integration is registered in TemplateRegistry.
          2. Locate each required template file by name.
          3. Render each template with the given context.
          4. Preserve any protected regions from existing files.
          5. Write rendered content to files under output_dir/app/:
             - app/models.py
             - app/schemas.py
             - app/crud/{entity}_crud.py (one per entity)
             - app/routers/{entity}_router.py (one per entity)
             - app/main.py
             - app/database.py

        Args:
            context (Dict[str, Any]): Context dictionary from ContextBuilder.
            integration_key (str): Integration name to select templates (e.g., "fastapi").

        Raises:
            ValueError: If the integration_key is not registered.
            FileNotFoundError: If any required template is missing for that integration.
            OSError: If writing to the output directory fails.
        """
        try:
            template_paths: List[Path] = self.template_registry.get_template_paths(integration_key)
        except KeyError:
            raise ValueError(f"Integration '{integration_key}' not found in TemplateRegistry.")

        template_map = {path.name: path for path in template_paths}
        required_templates = [
            self.MODELS_TEMPLATE,
            self.SCHEMAS_TEMPLATE,
            self.CRUD_TEMPLATE,
            self.ROUTER_TEMPLATE,
            self.MAIN_TEMPLATE,
            self.DB_TEMPLATE,
        ]
        for tpl_name in required_templates:
            if tpl_name not in template_map:
                raise FileNotFoundError(
                    f"Template '{tpl_name}' not found under integration '{integration_key}'."
                )

        try:
            self.output_dir.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            raise OSError(f"Cannot create output directory '{self.output_dir}': {e}")

        try:
            # Generate single-file templates (models, schemas, main, database)
            self._generate_single_file_templates(context)
            # Generate per-entity templates (crud, routers)
            self._generate_per_entity_templates(context)
        except FileNotFoundError:
            raise
        except Exception as e:
            raise OSError(f"Failed to generate project files: {e}")

    def _generate_single_file_templates(self, context: Dict[str, Any]) -> None:
        """
        Generate templates that create single files containing all entities.

        Args:
            context (Dict[str, Any]): Context dictionary with entities list.
        """
        app_dir = self.output_dir / "app"
        app_dir.mkdir(parents=True, exist_ok=True)
        (app_dir / "__init__.py").write_text("", encoding="utf-8")

        # models.py
        self._generate_and_write_file(self.MODELS_TEMPLATE, context, app_dir / self.MODELS_FILENAME)
        # schemas.py
        self._generate_and_write_file(self.SCHEMAS_TEMPLATE, context, app_dir / self.SCHEMAS_FILENAME)
        # main.py
        self._generate_and_write_file(self.MAIN_TEMPLATE, context, app_dir / self.MAIN_FILENAME)
        # database.py
        self._generate_and_write_file(self.DB_TEMPLATE, context, app_dir / self.DATABASE_FILENAME)

    def _generate_per_entity_templates(self, context: Dict[str, Any]) -> None:
        """
        Generate templates that create one file per entity.

        Args:
            context (Dict[str, Any]): Context dictionary with entities list.
        """
        entities = context.get("entities", [])
        for entity in entities:
            entity_context = context.copy()
            entity_context["entity"] = entity
            self._generate_entity_crud_file(entity_context, entity)
            self._generate_entity_router_file(entity_context, entity)

    def _generate_entity_crud_file(self, entity_context: Dict[str, Any], entity: Dict[str, Any]) -> None:
        """
        Generate CRUD file for a specific entity.

        Args:
            entity_context (Dict[str, Any]): Context with 'entity' key added.
            entity (Dict[str, Any]): The specific entity data.
        """
        crud_dir = self.output_dir / "app" / "crud"
        crud_dir.mkdir(parents=True, exist_ok=True)
        (crud_dir / "__init__.py").write_text("", encoding="utf-8")

        filename = f"{entity['names']['snake']}_crud.py"
        self._generate_and_write_file(self.CRUD_TEMPLATE, entity_context, crud_dir / filename)

    def _generate_entity_router_file(self, entity_context: Dict[str, Any], entity: Dict[str, Any]) -> None:
        """
        Generate Router file for a specific entity.

        Args:
            entity_context (Dict[str, Any]): Context with 'entity' key added.
            entity (Dict[str, Any]): The specific entity data.
        """
        routers_dir = self.output_dir / "app" / "routers"
        routers_dir.mkdir(parents=True, exist_ok=True)
        (routers_dir / "__init__.py").write_text("", encoding="utf-8")

        filename = f"{entity['names']['snake']}_router.py"
        self._generate_and_write_file(self.ROUTER_TEMPLATE, entity_context, routers_dir / filename)

    def _generate_and_write_file(self, template_name: str, context: Dict[str, Any], output_path: Path) -> None:
        """
        Generate content from template and write to file, preserving protected regions.

        Args:
            template_name (str): Name of the template to render.
            context (Dict[str, Any]): Context for template rendering.
            output_path (Path): Path where the file should be written.
        """
        rendered = self.template_engine.render_to_string(template_name, context)
        if self.preserve_protected_regions and self.protected_handler:
            rendered = self.protected_handler.preserve_protected_regions(output_path, rendered)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(rendered, encoding="utf-8")

    def disable_protected_regions(self) -> None:
        """Disable protected regions preservation for this generator."""
        self.preserve_protected_regions = False
        self.protected_handler = None

    def enable_protected_regions(self) -> None:
        """Enable protected regions preservation for this generator."""
        self.preserve_protected_regions = True
        self.protected_handler = SmartProtectedRegionsHandler()
