"""
code_generator.py

Defines CodeGenerator with multi-stack support and protected regions,
using the plugin-based TemplateEngine and TemplateRegistry.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

from brickend_core.engine.template_engine import TemplateEngine
from brickend_core.engine.template_registry import TemplateRegistry
from brickend_core.engine.protected_regions import SmartProtectedRegionsHandler
from brickend_core.engine.context_builder import ContextBuilder
from brickend_core.config.project_schema import BrickendProject


class CodeGenerator:
    """
    Multi-stack CodeGenerator that renders project files for different backends
    (FastAPI, Django, etc.) using the plugin-based template system with priority support.
    """

    def __init__(
        self,
        template_engine: TemplateEngine,
        template_registry: TemplateRegistry,
        output_dir: Path,
        preserve_protected_regions: bool = True,
        config: Optional[BrickendProject] = None,
    ) -> None:
        """
        Initialize CodeGenerator with multi-stack support.

        Args:
            template_engine: Template engine in plugin mode
            template_registry: Template registry in plugin mode
            output_dir: Directory where generated files will be written
            preserve_protected_regions: Whether to preserve protected regions
            config: Project configuration
        """
        self.template_engine = template_engine
        self.template_registry = template_registry
        self.output_dir = output_dir
        self.preserve_protected_regions = preserve_protected_regions
        self.config = config
        self.context_builder = ContextBuilder()

        self.protected_handler = (
            SmartProtectedRegionsHandler() if preserve_protected_regions else None
        )

    def generate_all(self) -> None:
        """
        Generate all code files using project configuration.

        Requires config to be set during initialization.

        Raises:
            ValueError: If no config is provided or entities are empty
        """
        if not self.config:
            raise ValueError("Project configuration required for generate_all()")

        if not self.config.entities:
            raise ValueError("No entities defined in project configuration")

        # Build context from config
        context = self.context_builder.build_context(self.config.entities)

        # Add project-specific context
        context.update({
            "project": self.config.project.model_dump(),
            "stack": self.config.stack.model_dump(),
            "settings": self.config.settings.model_dump(),
        })

        # Generate for the configured stack
        stack = self.config.stack.back
        self._generate_project_plugin_mode(context, stack)

    def _generate_project_plugin_mode(self, context: Dict[str, Any], stack: str) -> None:
        """Generate project using plugin mode."""
        # Get available components for this stack
        try:
            components = self.template_registry.get_available_components("back", stack)
        except Exception:
            # Fallback to common components if registry doesn't support this method
            components = self._get_default_components_for_stack(stack)

        if not components:
            raise ValueError(f"No templates found for stack '{stack}'")

        try:
            self.output_dir.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            raise OSError(f"Cannot create output directory '{self.output_dir}': {e}")

        # Generate based on stack type
        if stack == "django":
            self._generate_django_project(context, components)
        else:
            # Default to FastAPI-style generation for other stacks
            self._generate_fastapi_project(context, components)

    @staticmethod
    def _get_default_components_for_stack(stack: str) -> List[str]:
        """Get default components for a stack when registry doesn't provide them."""
        components_by_stack = {
            "fastapi": ["models", "schemas", "crud", "router", "main", "db"],
            "django": ["models", "serializers", "viewsets", "urls", "admin"],
        }
        return components_by_stack.get(stack, ["models", "schemas", "crud", "router"])

    def _generate_fastapi_project(self, context: Dict[str, Any], components: List[str]) -> None:
        """Generate FastAPI-style project structure."""
        app_dir = self.output_dir / "app"
        app_dir.mkdir(parents=True, exist_ok=True)
        (app_dir / "__init__.py").write_text("", encoding="utf-8")

        # Single-file components
        single_file_components = {
            "models": "models.py",
            "schemas": "schemas.py",
            "main": "main.py",
            "db": "database.py"
        }

        for component in components:
            if component in single_file_components:
                output_path = app_dir / single_file_components[component]
                self._generate_component_file("back", "fastapi", component, context, output_path)

        # Per-entity components (crud, router)
        entities = context.get("entities", [])
        for entity in entities:
            entity_context = context.copy()
            entity_context["entity"] = entity

            if "crud" in components:
                self._generate_entity_file("crud", entity_context, entity, app_dir / "crud")
            if "router" in components:
                self._generate_entity_file("router", entity_context, entity, app_dir / "routers")

    def _generate_django_project(self, context: Dict[str, Any], components: List[str]) -> None:
        """Generate Django-style project structure."""
        apps_dir = self.output_dir / "apps" / "core"
        apps_dir.mkdir(parents=True, exist_ok=True)
        (apps_dir / "__init__.py").write_text("", encoding="utf-8")

        # Django components mapping
        django_components = {
            "models": "models.py",
            "serializers": "serializers.py",
            "viewsets": "viewsets.py",
            "urls": "urls.py",
            "admin": "admin.py"
        }

        for component in components:
            if component in django_components:
                output_path = apps_dir / django_components[component]
                self._generate_component_file("back", "django", component, context, output_path)

    def _generate_component_file(
        self,
        category: str,
        stack: str,
        component: str,
        context: Dict[str, Any],
        output_path: Path
    ) -> None:
        """Generate a single component file using plugin mode."""
        try:
            rendered = self.template_engine.render_component_to_string(
                category, stack, component, context
            )

            if self.preserve_protected_regions and self.protected_handler:
                rendered = self.protected_handler.preserve_protected_regions(output_path, rendered)

            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(rendered, encoding="utf-8")

        except FileNotFoundError:
            # Template doesn't exist, skip silently
            pass
        except Exception as e:
            raise OSError(f"Failed to generate {component}: {e}")

    def _generate_entity_file(
        self,
        component: str,
        entity_context: Dict[str, Any],
        entity: Dict[str, Any],
        output_dir: Path
    ) -> None:
        """Generate per-entity file (crud, router, etc.)."""
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "__init__.py").write_text("", encoding="utf-8")

        filename = f"{entity['names']['snake']}_{component}.py"
        output_path = output_dir / filename

        try:
            rendered = self.template_engine.render_component_to_string(
                "back", self.config.stack.back if self.config else "fastapi",
                component, entity_context
            )

            if self.preserve_protected_regions and self.protected_handler:
                rendered = self.protected_handler.preserve_protected_regions(output_path, rendered)

            output_path.write_text(rendered, encoding="utf-8")

        except FileNotFoundError:
            # Template doesn't exist, skip silently
            pass

    # Utility methods
    def disable_protected_regions(self) -> None:
        """Disable protected regions' preservation."""
        self.preserve_protected_regions = False
        self.protected_handler = None

    def enable_protected_regions(self) -> None:
        """Enable protected regions' preservation."""
        self.preserve_protected_regions = True
        self.protected_handler = SmartProtectedRegionsHandler()

    def set_config(self, config: BrickendProject) -> None:
        """Set project configuration for plugin mode."""
        self.config = config
