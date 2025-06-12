"""
template_engine.py

Provides a simple Jinja2-based template engine for rendering templates
to strings or directly to files. This engine can load templates from one
or more directories.
"""

from pathlib import Path
from typing import Any, Dict, List

from jinja2 import Environment, FileSystemLoader, select_autoescape


class TemplateEngine:
    """
    A simple Jinja2 template engine that can load templates from multiple directories,
    render them to strings, and write rendered content to disk.
    """

    def __init__(self, template_dirs: List[Path], auto_reload: bool = False) -> None:
        """
        Initialize the TemplateEngine.

        Args:
            template_dirs (List[Path]): List of directories to search for templates.
            auto_reload (bool): If True, Jinja2 will check for updated templates on each render.
        """
        loader_paths = [str(d.resolve()) for d in template_dirs]
        self.env = Environment(
            loader=FileSystemLoader(loader_paths),
            autoescape=select_autoescape(["j2", "jinja"]),
            auto_reload=auto_reload,
        )

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
