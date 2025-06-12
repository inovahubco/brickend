"""
template_registry.py

Scans integration directories for Jinja2 templates and provides lookup by integration key.
"""

from pathlib import Path
from typing import Dict, List


class TemplateRegistry:
    """
    TemplateRegistry scans given integration directories and builds a mapping
    from integration name to a list of template file paths (.j2). It allows
    querying available integrations, listing all templates for an integration,
    and finding a specific template by filename.
    """

    def __init__(self, base_dirs: List[Path], ignore_hidden: bool = True) -> None:
        """
        Initialize the TemplateRegistry.

        Args:
            base_dirs (List[Path]): Directories where each directory’s name represents
                the integration key (e.g., 'fastapi', 'django'). Each directory is
                scanned recursively for .j2 files.
            ignore_hidden (bool): If True, skip files or folders whose names start
                with a dot ('.'). Defaults to True.
        """
        self.templates: Dict[str, List[Path]] = {}
        self.ignore_hidden = ignore_hidden

        for base_dir in base_dirs:
            if not base_dir.is_dir():
                continue

            integration_name = base_dir.name
            collected: List[Path] = []

            for file_path in base_dir.rglob("*.j2"):
                if ignore_hidden:
                    relative_parts = file_path.relative_to(base_dir).parts
                    if any(part.startswith(".") for part in relative_parts):
                        continue

                collected.append(file_path)

            if collected:
                self.templates[integration_name] = collected

    def list_integrations(self) -> List[str]:
        """
        Return a sorted list of integration keys that have at least one template.

        Returns:
            List[str]: Integration names, e.g., ["fastapi", "django", "aws_cdk"].
        """
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
        if integration not in self.templates:
            raise KeyError(f"No templates registered for integration '{integration}'")

        for path in self.templates[integration]:
            if path.name == template_name:
                return path

        raise FileNotFoundError(f"Template '{template_name}' not found under integration '{integration}'")
