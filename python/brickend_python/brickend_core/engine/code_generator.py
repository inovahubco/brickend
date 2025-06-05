"""
code_generator.py

Defines CodeGenerator, which uses a TemplateEngine and TemplateRegistry
to render Jinja2 templates into Python code files for a given integration.
"""

from pathlib import Path
from typing import Any, Dict, List

from brickend_core.engine.template_engine import TemplateEngine
from brickend_core.engine.template_registry import TemplateRegistry


class CodeGenerator:
    """
    CodeGenerator renders project files (models, schemas, CRUD, routers, main, db)
    for a specified integration (e.g., "fastapi"), using Jinja2 templates and a context
    built by ContextBuilder.
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
    ) -> None:
        """
        Initialize CodeGenerator.

        Args:
            template_engine (TemplateEngine): Jinja2 engine to render templates.
            template_registry (TemplateRegistry): Registry of available templates.
            output_dir (Path): Directory where generated files will be written.
        """
        self.template_engine = template_engine
        self.template_registry = template_registry
        self.output_dir = output_dir

    def generate_project(self, context: Dict[str, Any], integration_key: str) -> None:
        """
        Generate all code files for the given integration using the provided context.

        This method will:
          1. Ensure the integration is registered in TemplateRegistry.
          2. Locate each required template file by name.
          3. Render each template with the given context.
          4. Write rendered content to files under output_dir:
             - models.py
             - schemas.py
             - crud.py
             - router.py
             - main.py
             - db.py

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
            # models.py
            rendered_models = self.template_engine.render_to_string(self.MODELS_TEMPLATE, context)
            (self.output_dir / self.MODELS_FILENAME).write_text(rendered_models, encoding="utf-8")

            # schemas.py
            rendered_schemas = self.template_engine.render_to_string(self.SCHEMAS_TEMPLATE, context)
            (self.output_dir / self.SCHEMAS_FILENAME).write_text(rendered_schemas, encoding="utf-8")

            # crud.py
            rendered_crud = self.template_engine.render_to_string(self.CRUD_TEMPLATE, context)
            (self.output_dir / self.CRUD_FILENAME).write_text(rendered_crud, encoding="utf-8")

            # router.py
            rendered_router = self.template_engine.render_to_string(self.ROUTER_TEMPLATE, context)
            (self.output_dir / self.ROUTER_FILENAME).write_text(rendered_router, encoding="utf-8")

            # main.py
            rendered_main = self.template_engine.render_to_string(self.MAIN_TEMPLATE, context)
            (self.output_dir / self.MAIN_FILENAME).write_text(rendered_main, encoding="utf-8")

            # db.py
            rendered_db = self.template_engine.render_to_string(self.DB_TEMPLATE, context)
            (self.output_dir / self.DB_FILENAME).write_text(rendered_db, encoding="utf-8")

        except FileNotFoundError as fnf:
            raise fnf
        except Exception as e:
            raise OSError(f"Failed to generate project files: {e}")
