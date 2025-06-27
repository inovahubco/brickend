"""
template_engine.py

Provides a Jinja2-based template engine for rendering templates to strings or files.
Supports both legacy mode (multiple template directories) and plugin mode with
user template priority system (templates_user/ > core_templates).
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from jinja2 import Environment, FileSystemLoader, select_autoescape


class TemplateEngine:
    """
    A Jinja2 template engine that supports multiple operation modes:

    1. LEGACY MODE: Load templates from multiple directories (backward compatibility)
    2. PLUGIN MODE: Priority-based loading (templates_user/ > core_templates) with triplet access
    """

    def __init__(
        self,
        template_dirs: Optional[List[Path]] = None,
        base_path: Optional[Path] = None,
        user_templates_dir: Optional[Path] = None,
        auto_reload: bool = False
    ) -> None:
        """
        Initialize the TemplateEngine in legacy or plugin mode.

        LEGACY MODE (for backward compatibility):
            template_dirs: List of directories to search for templates

        PLUGIN MODE (new functionality):
            base_path: Base path containing integrations/ directory
            user_templates_dir: Directory for user custom templates (defaults to "./templates_user")

        Args:
            template_dirs (List[Path], optional): LEGACY mode - List of template directories
            base_path (Path, optional): PLUGIN mode - Base path with integrations/
            user_templates_dir (Path, optional): PLUGIN mode - User templates directory
            auto_reload (bool): If True, Jinja2 will check for updated templates on each render
        """
        self.auto_reload = auto_reload

        # Determine operation mode
        if template_dirs is not None:
            # LEGACY MODE - Initialize with multiple template directories
            self._init_legacy_mode(template_dirs)
        elif base_path is not None:
            # PLUGIN MODE - Initialize with priority system
            self._init_plugin_mode(base_path, user_templates_dir)
        else:
            raise ValueError("Either template_dirs (legacy) or base_path (plugin mode) must be provided")

    def _init_legacy_mode(self, template_dirs: List[Path]) -> None:
        """Initialize engine in legacy mode for backward compatibility."""
        self.mode = "legacy"
        self.template_dirs = template_dirs
        self.base_path = None
        self.user_templates_dir = None

        # Set up Jinja2 environment with multiple directories
        loader_paths = [str(d.resolve()) for d in template_dirs]
        self.env = Environment(
            loader=FileSystemLoader(loader_paths),
            autoescape=select_autoescape(["j2", "jinja"]),
            auto_reload=self.auto_reload,
        )

    def _init_plugin_mode(self, base_path: Path, user_templates_dir: Optional[Path]) -> None:
        """Initialize engine in plugin mode with priority system."""
        self.mode = "plugin"
        self.base_path = base_path.resolve()

        if user_templates_dir is not None:
            if user_templates_dir.is_absolute():
                self.user_templates_dir = user_templates_dir
            else:
                self.user_templates_dir = self.base_path / user_templates_dir
        else:
            self.user_templates_dir = self.base_path / "templates_user"

        self.template_dirs = None

        # Build prioritized template directories for Jinja2
        search_paths = []

        # 1. User templates directory (highest priority)
        if self.user_templates_dir.exists():
            search_paths.append(str(self.user_templates_dir.resolve()))

        # 2. Core integrations directory (fallback)
        core_integrations = self.base_path / "integrations"
        if core_integrations.exists():
            search_paths.append(str(core_integrations.resolve()))

        # 3. Add any other core template directories
        for possible_dir in [self.base_path / "templates", self.base_path / "core"]:
            if possible_dir.exists():
                search_paths.append(str(possible_dir.resolve()))

        if not search_paths:
            # Create minimal environment with current directory
            search_paths = [str(Path(".").resolve())]

        self.env = Environment(
            loader=FileSystemLoader(search_paths),
            autoescape=select_autoescape(["j2", "jinja"]),
            auto_reload=self.auto_reload,
        )

    # =============================================================================
    # LEGACY INTERFACE (maintain backward compatibility)
    # =============================================================================

    def render_to_string(self, template_name: str, context: Dict[str, Any]) -> str:
        """
        Render a template with the given context and return the result as a string.

        Args:
            template_name (str): The filename of the template (e.g., "model_template.j2").
            context (Dict[str, Any]): Mapping of variable names to values for rendering.

        Returns:
            str: The rendered template as a Unicode string.

        Raises:
            jinja2.TemplateNotFound: If the template file cannot be found in any of the template_dirs.
            jinja2.TemplateSyntaxError: If there is a syntax error in the template.
        """
        template = self.env.get_template(template_name)
        return template.render(**context)

    def render_to_file(self, template_name: str, context: Dict[str, Any], destination: Path) -> None:
        """
        Render a template with the given context and write the output to a file.

        This method will create parent directories of the destination path if they do not exist.

        Args:
            template_name (str): The filename of the template (e.g., "router_template.j2").
            context (Dict[str, Any]): Mapping of variable names to values for rendering.
            destination (Path): Full path (including filename) where rendered output will be written.

        Raises:
            jinja2.TemplateNotFound: If the template file cannot be found.
            jinja2.TemplateSyntaxError: If there is a syntax error in the template.
            OSError: If the file cannot be written due to filesystem issues.
        """
        rendered_content = self.render_to_string(template_name, context)
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("w", encoding="utf-8") as f:
            f.write(rendered_content)

    # =============================================================================
    # PLUGIN MODE INTERFACE (new functionality with priority system)
    # =============================================================================

    def get_template_path(self, category: str, stack: str, component: str) -> Path:
        """
        Find template with priority: templates_user/ > core_templates.

        Search order:
        1. {user_templates_dir}/{category}/{stack}/{component}_template.j2
        2. {base_path}/integrations/{category}/{stack}/{component}_template.j2

        Args:
            category (str): Template category (e.g., "back", "infra")
            stack (str): Stack name (e.g., "fastapi", "django")
            component (str): Component name (e.g., "models", "schemas")

        Returns:
            Path: Full path to the template file with the highest priority

        Raises:
            RuntimeError: If engine is not in plugin mode
            FileNotFoundError: If no template is found in any location

        Example:
            engine.get_template_path("back", "fastapi", "models")
            # Returns: templates_user/back/fastapi/models_template.j2 (if exists)
            # Or: src/brickend_core/integrations/back/fastapi/models_template.j2
        """
        if self.mode != "plugin":
            raise RuntimeError("get_template_path() requires plugin mode initialization")

        template_filename = f"{component}_template.j2"

        # 1. Check user templates directory (highest priority)
        user_template = self.user_templates_dir / category / stack / template_filename
        if user_template.exists():
            return user_template

        # 2. Check core integrations directory (fallback)
        core_template = self.base_path / "integrations" / category / stack / template_filename
        if core_template.exists():
            return core_template

        # Template not found in any location
        raise FileNotFoundError(
            f"Template not found: {category}/{stack}/{component}\n"
            f"Searched in:\n"
            f"  - {user_template}\n"  
            f"  - {core_template}"
        )

    def render_template_by_path(self, template_path: Path, context: Dict[str, Any]) -> str:
        """
        Render a template using its full file path.

        Args:
            template_path (Path): Full path to the template file
            context (Dict[str, Any]): Template context variables

        Returns:
            str: Rendered template content

        Raises:
            FileNotFoundError: If template file doesn't exist
            jinja2.TemplateSyntaxError: If template has syntax errors
        """
        if not template_path.exists():
            raise FileNotFoundError(f"Template file not found: {template_path}")

        # Get relative path for Jinja2 template loading
        template_name = None

        # Try to find template in configured search paths
        for search_path_str in self.env.loader.searchpath:
            search_path = Path(search_path_str)
            try:
                # Calculate relative path from search path to template
                relative_path = template_path.resolve().relative_to(search_path.resolve())
                template_name = str(relative_path).replace("\\", "/")  # Normalize path separators
                break
            except ValueError:
                # Template is not under this search path, continue
                continue

        if template_name is None:
            # Template is not in any search path, read and render directly
            template_content = template_path.read_text(encoding="utf-8")
            template = self.env.from_string(template_content)
            return template.render(**context)

        # Template found in search path, use standard Jinja2 loading
        template = self.env.get_template(template_name)
        return template.render(**context)

    def render_component_to_string(self, category: str, stack: str, component: str, context: Dict[str, Any]) -> str:
        """
        Render a component template using the priority system.

        Args:
            category (str): Template category
            stack (str): Stack name
            component (str): Component name
            context (Dict[str, Any]): Template context variables

        Returns:
            str: Rendered template content
        """
        if self.mode != "plugin":
            raise RuntimeError("render_component_to_string() requires plugin mode initialization")

        template_path = self.get_template_path(category, stack, component)
        return self.render_template_by_path(template_path, context)

    def render_component_to_file(
        self,
        category: str,
        stack: str,
        component: str,
        context: Dict[str, Any],
        destination: Path
    ) -> None:
        """
        Render a component template to a file using the priority system.

        Args:
            category (str): Template category
            stack (str): Stack name
            component (str): Component name
            context (Dict[str, Any]): Template context variables
            destination (Path): Output file path
        """
        if self.mode != "plugin":
            raise RuntimeError("render_component_to_file() requires plugin mode initialization")

        rendered_content = self.render_component_to_string(category, stack, component, context)
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("w", encoding="utf-8") as f:
            f.write(rendered_content)

    # =============================================================================
    # UTILITY METHODS
    # =============================================================================

    def list_available_templates(self, category: Optional[str] = None, stack: Optional[str] = None) -> Dict[str, List[str]]:
        """
        List all available templates, organized by category and stack.

        Args:
            category (str, optional): Filter by specific category
            stack (str, optional): Filter by specific stack (requires category)

        Returns:
            Dict[str, List[str]]: Nested dict of {category: {stack: [components]}}
        """
        if self.mode != "plugin":
            raise RuntimeError("list_available_templates() requires plugin mode initialization")

        templates = {}

        # Scan both user and core template directories
        search_dirs = []
        if self.user_templates_dir.exists():
            search_dirs.append(("user", self.user_templates_dir))

        core_integrations = self.base_path / "integrations"
        if core_integrations.exists():
            search_dirs.append(("core", core_integrations))

        for source, base_dir in search_dirs:
            if not base_dir.exists():
                continue

            for cat_dir in base_dir.iterdir():
                if not cat_dir.is_dir():
                    continue
                if category and cat_dir.name != category:
                    continue

                cat_name = cat_dir.name
                if cat_name not in templates:
                    templates[cat_name] = {}

                for stack_dir in cat_dir.iterdir():
                    if not stack_dir.is_dir():
                        continue
                    if stack and stack_dir.name != stack:
                        continue

                    stack_name = stack_dir.name
                    if stack_name not in templates[cat_name]:
                        templates[cat_name][stack_name] = []

                    # Find all template files
                    for template_file in stack_dir.glob("*_template.j2"):
                        component = template_file.stem.replace("_template", "")
                        if component not in templates[cat_name][stack_name]:
                            templates[cat_name][stack_name].append(component)

        # Sort everything for consistent output
        for cat_name in templates:
            for stack_name in templates[cat_name]:
                templates[cat_name][stack_name].sort()

        return templates

    def has_user_template(self, category: str, stack: str, component: str) -> bool:
        """Check if a user template exists (in templates_user/ directory)."""
        if self.mode != "plugin":
            return False

        user_template = self.user_templates_dir / category / stack / f"{component}_template.j2"
        return user_template.exists()

    def get_template_info(self, category: str, stack: str, component: str) -> Dict[str, Any]:
        """
        Get information about a template (source, path, priority).

        Returns:
            Dict with keys: 'path', 'source' ('user' or 'core'), 'exists'
        """
        if self.mode != "plugin":
            raise RuntimeError("get_template_info() requires plugin mode initialization")

        user_template = self.user_templates_dir / category / stack / f"{component}_template.j2"
        core_template = self.base_path / "integrations" / category / stack / f"{component}_template.j2"

        if user_template.exists():
            return {
                'path': user_template,
                'source': 'user',
                'exists': True,
                'priority': 1
            }
        elif core_template.exists():
            return {
                'path': core_template,
                'source': 'core',
                'exists': True,
                'priority': 2
            }
        else:
            return {
                'path': None,
                'source': None,
                'exists': False,
                'priority': None
            }
