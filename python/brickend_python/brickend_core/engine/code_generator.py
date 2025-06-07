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
    CodeGenerator renders project files (models, schemas, CRUD, routers, main, db)
    for a specified integration (e.g., "fastapi"), using Jinja2 templates and a context
    built by ContextBuilder, while preserving protected code regions.
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
    DB_FILENAME: str = "db.py"

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
        self.protected_handler = SmartProtectedRegionsHandler() if preserve_protected_regions else None

    def generate_project(self, context: Dict[str, Any], integration_key: str) -> None:
        """
        Generate all code files for the given integration using the provided context.

        This method will:
          1. Ensure the integration is registered in TemplateRegistry.
          2. Locate each required template file by name.
          3. Render each template with the given context.
          4. Preserve any protected regions from existing files.
          5. Write rendered content to files under output_dir:
             - models.py (single file with all entities)
             - schemas.py (single file with all entities)
             - crud.py files (one per entity in app/crud/)
             - router.py files (one per entity in app/routers/)
             - main.py (single file importing all routers)
             - db.py (single file)

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

        template_map: Dict[str, Path] = {path.name: path for path in template_paths}

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
            # Generate single-file templates (models, schemas, main, db)
            self._generate_single_file_templates(context)

            # Generate per-entity templates (crud, routers)
            self._generate_per_entity_templates(context)

        except FileNotFoundError as fnf:
            raise fnf
        except Exception as e:
            raise OSError(f"Failed to generate project files: {e}")

    def _generate_single_file_templates(self, context: Dict[str, Any]) -> None:
        """
        Generate templates that create single files containing all entities.

        Args:
            context (Dict[str, Any]): Context dictionary with entities list.
        """
        # models.py - single file with all entity models
        self._generate_and_write_file(
            self.MODELS_TEMPLATE,
            context,
            self.output_dir / self.MODELS_FILENAME
        )

        # schemas.py - single file with all entity schemas
        self._generate_and_write_file(
            self.SCHEMAS_TEMPLATE,
            context,
            self.output_dir / self.SCHEMAS_FILENAME
        )

        # main.py - single file importing all routers
        self._generate_and_write_file(
            self.MAIN_TEMPLATE,
            context,
            self.output_dir / self.MAIN_FILENAME
        )

        # db.py - single database configuration file
        self._generate_and_write_file(
            self.DB_TEMPLATE,
            context,
            self.output_dir / self.DB_FILENAME
        )

    def _generate_per_entity_templates(self, context: Dict[str, Any]) -> None:
        """
        Generate templates that create one file per entity.

        Args:
            context (Dict[str, Any]): Context dictionary with entities list.
        """
        entities = context.get('entities', [])

        for entity in entities:
            # Create entity-specific context
            entity_context = context.copy()
            entity_context['entity'] = entity

            # Generate CRUD file for this entity
            self._generate_entity_crud_file(entity_context, entity)

            # Generate Router file for this entity
            self._generate_entity_router_file(entity_context, entity)

    def _generate_entity_crud_file(self, entity_context: Dict[str, Any], entity: Dict[str, Any]) -> None:
        """
        Generate CRUD file for a specific entity.

        Args:
            entity_context (Dict[str, Any]): Context with 'entity' key added.
            entity (Dict[str, Any]): The specific entity data.
        """
        # Create app/crud directory structure
        crud_dir = self.output_dir / "app" / "crud"
        crud_dir.mkdir(parents=True, exist_ok=True)

        # Generate and write entity-specific CRUD file
        crud_filename = f"{entity['names']['snake']}_crud.py"
        crud_path = crud_dir / crud_filename

        self._generate_and_write_file(
            self.CRUD_TEMPLATE,
            entity_context,
            crud_path
        )

    def _generate_entity_router_file(self, entity_context: Dict[str, Any], entity: Dict[str, Any]) -> None:
        """
        Generate Router file for a specific entity.

        Args:
            entity_context (Dict[str, Any]): Context with 'entity' key added.
            entity (Dict[str, Any]): The specific entity data.
        """
        # Create app/routers directory structure
        routers_dir = self.output_dir / "app" / "routers"
        routers_dir.mkdir(parents=True, exist_ok=True)

        # Generate and write entity-specific Router file
        router_filename = f"{entity['names']['snake']}_router.py"
        router_path = routers_dir / router_filename

        self._generate_and_write_file(
            self.ROUTER_TEMPLATE,
            entity_context,
            router_path
        )

    def _generate_and_write_file(self, template_name: str, context: Dict[str, Any], output_path: Path) -> None:
        """
        Generate content from template and write to file, preserving protected regions.

        Args:
            template_name (str): Name of the template to render.
            context (Dict[str, Any]): Context for template rendering.
            output_path (Path): Path where the file should be written.
        """
        # Render the template
        rendered_content = self.template_engine.render_to_string(template_name, context)

        # Preserve protected regions if enabled
        if self.preserve_protected_regions and self.protected_handler:
            rendered_content = self.protected_handler.preserve_protected_regions(
                output_path,
                rendered_content
            )

        # Write the file
        output_path.write_text(rendered_content, encoding="utf-8")

    def disable_protected_regions(self) -> None:
        """Disable protected regions preservation for this generator."""
        self.preserve_protected_regions = False
        self.protected_handler = None

    def enable_protected_regions(self) -> None:
        """Enable protected regions preservation for this generator."""
        self.preserve_protected_regions = True
        self.protected_handler = SmartProtectedRegionsHandler()
