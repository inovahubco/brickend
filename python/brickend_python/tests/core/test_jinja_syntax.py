"""
test_jinja_syntax.py

Ensure that each Jinja2 template in brickend_core/integrations/back/fastapi/ compiles
without syntax errors.
"""

import pytest
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, TemplateSyntaxError


TEMPLATES_DIR = Path("brickend_core/integrations/back/fastapi")


@pytest.mark.parametrize("tpl_path", list(TEMPLATES_DIR.rglob("*.j2")))
def test_jinja_syntax(tpl_path: Path):
    """
    Load each .j2 template under brickend_core/integrations/back/fastapi/
    and verify it compiles without raising TemplateSyntaxError.
    """
    loader = FileSystemLoader(str(tpl_path.parent))
    env = Environment(loader=loader)

    try:
        env.get_template(tpl_path.name)
    except TemplateSyntaxError as e:
        pytest.fail(f"Syntax error in template '{tpl_path.name}': {e}")
