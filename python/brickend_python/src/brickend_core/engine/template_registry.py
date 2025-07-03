"""
template_registry.py

Scans integration directories for Jinja2 templates and provides lookup with triplet indexing support.
Uses plugin discovery with structured integrations containing categories and meta.yaml files.
"""

from pathlib import Path
from typing import Dict, List, Tuple


class TemplateRegistry:
    """
    TemplateRegistry scans integration directories and builds a mapping
    from triplet (category, stack, component) to template file paths (.j2).

    Uses structured integrations with categories and meta.yaml files.
    """

    def __init__(self, base_path: Path, ignore_hidden: bool = True) -> None:
        """
        Initialize the TemplateRegistry.

        Args:
            base_path: Base path containing integrations/ directory with category/stack structure.
            ignore_hidden: If True, skip files or folders whose names start with a dot ('.').
        """
        self.base_path = base_path
        self.ignore_hidden = ignore_hidden
        self._index: Dict[Tuple[str, str, str], Path] = {}
        self._integrations: Dict[str, List[str]] = {}

        # Initialize with plugin discovery
        self._integrations = self.discover_integrations(base_path)
        self._discover_templates()

    # =============================================================================
    # MAIN INTERFACE
    # =============================================================================

    def list_integrations(self) -> List[str]:
        """
        Return a sorted list of integration keys that have at least one template.

        Returns:
            List[str]: Integration names, e.g., ["fastapi", "django", "aws_cdk"].
        """
        all_stacks = []
        for stacks in self._integrations.values():
            all_stacks.extend(stacks)
        return sorted(set(all_stacks))

    def get_template_paths(self, integration: str) -> List[Path]:
        """
        Return all template file paths for a given integration.

        Args:
            integration: The integration name (key) to query.

        Returns:
            List[Path]: Paths to .j2 template files.

        Raises:
            KeyError: If the integration key is not registered.
        """
        templates = []
        for category, stacks in self._integrations.items():
            if integration in stacks:
                stack_path = self.base_path / "integrations" / category / integration
                if stack_path.exists():
                    templates.extend(list(stack_path.glob("*_template.j2")))

        if not templates:
            raise KeyError(f"No templates registered for integration '{integration}'")
        return templates

    def find_template(self, integration: str, template_name: str) -> Path:
        """
        Find a specific template by filename within a given integration.

        Args:
            integration: The integration name (key) to search in.
            template_name: Exact filename of the template (e.g., "models_template.j2").

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
    # TRIPLET INTERFACE
    # =============================================================================

    def get_template(self, category: str, stack: str, component: str) -> Path:
        """
        Get template by triplet (category, stack, component).

        Args:
            category: Category name (e.g., "back", "infra")
            stack: Stack name (e.g., "fastapi", "django")
            component: Component name (e.g., "models", "schemas")

        Returns:
            Path: Full path to the template file

        Raises:
            KeyError: If the triplet is not found in the index

        Example:
            get_template("back", "fastapi", "models") -> Path to models_template.j2
        """
        key = (category, stack, component)
        if key not in self._index:
            raise KeyError(f"Template not found: {category}/{stack}/{component}")
        return self._index[key]

    def get_available_stacks(self, category: str) -> List[str]:
        """
        Get all available stacks for a given category.

        Args:
            category: Category name (e.g., "back", "infra")

        Returns:
            List[str]: List of stack names
        """
        return self._integrations.get(category, [])

    def get_available_components(self, category: str, stack: str) -> List[str]:
        """
        Get all available components for a given category/stack.

        Args:
            category: Category name
            stack: Stack name

        Returns:
            List[str]: List of component names
        """
        components = []
        for (cat, stk, comp), _ in self._index.items():
            if cat == category and stk == stack:
                components.append(comp)
        return sorted(components)

    def get_all_categories(self) -> List[str]:
        """
        Get all available categories.

        Returns:
            List[str]: List of category names
        """
        return sorted(self._integrations.keys())

    def get_template_info(self, category: str, stack: str, component: str) -> Dict[str, any]:
        """
        Get detailed information about a template.

        Args:
            category: Category name
            stack: Stack name
            component: Component name

        Returns:
            Dict with template information including path, existence, etc.
        """
        key = (category, stack, component)
        if key in self._index:
            template_path = self._index[key]
            return {
                'path': template_path,
                'exists': template_path.exists(),
                'category': category,
                'stack': stack,
                'component': component,
                'filename': template_path.name
            }
        else:
            return {
                'path': None,
                'exists': False,
                'category': category,
                'stack': stack,
                'component': component,
                'filename': None
            }

    # =============================================================================
    # INTERNAL METHODS
    # =============================================================================

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
                    if self.ignore_hidden and template_file.name.startswith('.'):
                        continue

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
            base_path: Base path containing integrations/ directory

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
