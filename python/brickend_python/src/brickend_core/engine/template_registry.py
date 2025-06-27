"""
template_registry.py

Scans integration directories for Jinja2 templates and provides lookup by integration key.
Enhanced with plugin discovery and triplet indexing support.
"""

from pathlib import Path
from typing import Dict, List, Tuple


class TemplateRegistry:
    """
    TemplateRegistry scans given integration directories and builds a mapping
    from integration name to a list of template file paths (.j2).

    Supports both legacy mode (direct integration directories) and new plugin mode
    (structured integrations with categories and meta.yaml files).
    """

    def __init__(self, base_dirs: List[Path] = None, base_path: Path = None, ignore_hidden: bool = True) -> None:
        """
        Initialize the TemplateRegistry.

        Args:
            base_dirs (List[Path], optional): LEGACY mode - Directories where each
                directory's name represents the integration key. For backward compatibility.
            base_path (Path, optional): NEW mode - Base path containing integrations/
                directory with category/stack structure.
            ignore_hidden (bool): If True, skip files or folders whose names start
                with a dot ('.'). Defaults to True.
        """
        # Legacy mode attributes
        self.templates: Dict[str, List[Path]] = {}
        self.ignore_hidden = ignore_hidden

        # New plugin mode attributes
        self.base_path = base_path
        self._index: Dict[Tuple[str, str, str], Path] = {}
        self._integrations: Dict[str, List[str]] = {}

        # Initialize based on mode
        if base_dirs is not None:
            # LEGACY MODE: Initialize with list of integration directories
            self._init_legacy_mode(base_dirs)
        elif base_path is not None:
            # NEW MODE: Initialize with plugin discovery
            self._init_plugin_mode(base_path)
        else:
            raise ValueError("Either base_dirs (legacy) or base_path (plugin mode) must be provided")

    def _init_legacy_mode(self, base_dirs: List[Path]) -> None:
        """Initialize registry in legacy mode for backward compatibility."""
        for base_dir in base_dirs:
            if not base_dir.is_dir():
                continue

            integration_name = base_dir.name
            collected: List[Path] = []

            for file_path in base_dir.rglob("*.j2"):
                if self.ignore_hidden:
                    relative_parts = file_path.relative_to(base_dir).parts
                    if any(part.startswith(".") for part in relative_parts):
                        continue

                collected.append(file_path)

            if collected:
                self.templates[integration_name] = collected

    def _init_plugin_mode(self, base_path: Path) -> None:
        """Initialize registry in new plugin mode with discovery."""
        self.base_path = base_path
        self._integrations = self.discover_integrations(base_path)
        self._discover_templates()

    # =============================================================================
    # LEGACY INTERFACE (maintain backward compatibility)
    # =============================================================================

    def list_integrations(self) -> List[str]:
        """
        Return a sorted list of integration keys that have at least one template.

        Returns:
            List[str]: Integration names, e.g., ["fastapi", "django", "aws_cdk"].
        """
        if self.base_path is not None:
            # NEW MODE: Return all stacks from all categories
            all_stacks = []
            for stacks in self._integrations.values():
                all_stacks.extend(stacks)
            return sorted(all_stacks)
        else:
            # LEGACY MODE
            return sorted(self.templates.keys())

    def get_template_paths(self, integration: str) -> List[Path]:
        """
        Return all template file paths for a given integration.

        Args:
            integration (str): The integration name (key) to query.

        Returns:
            List[Path]: Paths to .j2 template files.

        Raises:
            KeyError: If the integration key is not registered.
        """
        if self.base_path is not None:
            # NEW MODE: Find templates for this stack across all categories
            templates = []
            for category, stacks in self._integrations.items():
                if integration in stacks:
                    stack_path = self.base_path / "integrations" / category / integration
                    templates.extend(list(stack_path.glob("*_template.j2")))

            if not templates:
                raise KeyError(f"No templates registered for integration '{integration}'")
            return templates
        else:
            # LEGACY MODE
            if integration not in self.templates:
                raise KeyError(f"No templates registered for integration '{integration}'")
            return self.templates[integration]

    def find_template(self, integration: str, template_name: str) -> Path:
        """
        Find a specific template by filename within a given integration.

        Args:
            integration (str): The integration name (key) to search in.
            template_name (str): Exact filename of the template
                (e.g., "models_template.j2").

        Returns:
            Path: Full path to the matching template file.

        Raises:
            KeyError: If the integration key is not registered.
            FileNotFoundError: If no matching template is found under that integration.
        """
        template_paths = self.get_template_paths(integration)

        for path in template_paths:
            if path.name == template_name:
                return path

        raise FileNotFoundError(f"Template '{template_name}' not found under integration '{integration}'")

    # =============================================================================
    # NEW PLUGIN INTERFACE
    # =============================================================================

    def get_template(self, category: str, stack: str, component: str) -> Path:
        """
        Get template by triplet (category, stack, component).

        Args:
            category (str): Category name (e.g., "back", "infra")
            stack (str): Stack name (e.g., "fastapi", "django")
            component (str): Component name (e.g., "models", "schemas")

        Returns:
            Path: Full path to the template file

        Raises:
            KeyError: If the triplet is not found in the index

        Example:
            get_template("back", "fastapi", "models") -> Path to models_template.j2
        """
        if self.base_path is None:
            raise RuntimeError("get_template() requires plugin mode initialization with base_path")

        key = (category, stack, component)
        if key not in self._index:
            raise KeyError(f"Template not found: {category}/{stack}/{component}")
        return self._index[key]

    def get_available_stacks(self, category: str) -> List[str]:
        """
        Get all available stacks for a given category.

        Args:
            category (str): Category name (e.g., "back", "infra")

        Returns:
            List[str]: List of stack names
        """
        if self.base_path is None:
            raise RuntimeError("get_available_stacks() requires plugin mode initialization")

        return self._integrations.get(category, [])

    def get_available_components(self, category: str, stack: str) -> List[str]:
        """
        Get all available components for a given category/stack.

        Args:
            category (str): Category name
            stack (str): Stack name

        Returns:
            List[str]: List of component names
        """
        if self.base_path is None:
            raise RuntimeError("get_available_components() requires plugin mode initialization")

        components = []
        for (cat, stk, comp), _ in self._index.items():
            if cat == category and stk == stack:
                components.append(comp)
        return sorted(components)

    def _discover_templates(self) -> None:
        """Index all templates by triplet (category, stack, component)."""
        for category, stacks in self._integrations.items():
            for stack in stacks:
                stack_path = self.base_path / "integrations" / category / stack

                # Skip if stack directory doesn't exist
                if not stack_path.exists():
                    continue

                # Index all template files
                for template_file in stack_path.glob("*_template.j2"):
                    component = template_file.stem.replace("_template", "")
                    key = (category, stack, component)
                    self._index[key] = template_file

    @staticmethod
    def discover_integrations(base_path: Path) -> Dict[str, List[str]]:
        """
        Scans integrations/ directory and returns dict of categories->stacks.

        Expected structure:
            base_path/integrations/
            ├── back/
            │   ├── fastapi/
            │   │   └── meta.yaml
            │   └── django/
            │       └── meta.yaml
            └── infra/
                ├── aws_cdk/
                │   └── meta.yaml
                └── terraform/
                    └── meta.yaml

        Args:
            base_path (Path): Base path containing integrations/ directory

        Returns:
            Dict[str, List[str]]: Mapping of category -> list of stack names
            Example: {"back": ["fastapi", "django"], "infra": ["aws_cdk"]}
        """
        integrations = {}
        integrations_path = base_path / "integrations"

        # If integrations directory doesn't exist, return empty dict
        if not integrations_path.exists() or not integrations_path.is_dir():
            return integrations

        # Scan each category directory (back, infra, etc.)
        for category_dir in integrations_path.iterdir():
            if not category_dir.is_dir():
                continue

            category_name = category_dir.name
            stacks = []

            # Scan each stack directory within category
            for stack_dir in category_dir.iterdir():
                if not stack_dir.is_dir():
                    continue

                # Only include stacks that have meta.yaml file
                meta_file = stack_dir / "meta.yaml"
                if meta_file.exists():
                    stacks.append(stack_dir.name)

            # Only add category if it has at least one valid stack
            if stacks:
                integrations[category_name] = sorted(stacks)

        return integrations
