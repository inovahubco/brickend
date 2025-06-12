"""
test_jinja_syntax.py

Unit tests for verifying that all Jinja2 templates in the FastAPI integration
compile without syntax errors.
"""

import pytest
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, TemplateSyntaxError


TEMPLATES_DIR = Path("brickend_core/integrations/back/fastapi")


@pytest.mark.parametrize("tpl_path", list(TEMPLATES_DIR.rglob("*.j2")))
def test_jinja_syntax(tpl_path: Path):
    """
    Ensure a given Jinja2 template compiles without syntax errors.

    This test loads the template using Jinja2's Environment and FileSystemLoader,
    and fails if a TemplateSyntaxError is raised during compilation.

    Args:
        tpl_path (Path): Path to the .j2 template file to validate.

    Raises:
        AssertionError: If compiling tpl_path raises a TemplateSyntaxError.
    """
    loader = FileSystemLoader(str(tpl_path.parent))
    env = Environment(loader=loader)

    try:
        env.get_template(tpl_path.name)
    except TemplateSyntaxError as e:
        pytest.fail(f"Syntax error in template '{tpl_path.name}': {e}")
