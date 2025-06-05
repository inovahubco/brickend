"""
test_template_engine.py

Unit tests for the TemplateEngine class in core.engine.template_engine.
Covers rendering to string and writing rendered output to a file.
"""

import pytest
from brickend_core.engine.template_engine import TemplateEngine


@pytest.fixture
def simple_template_dir(tmp_path):
    """
    Create a temporary directory with a single Jinja2 template for testing.
    The template will be named 'greeting.j2' with content:
        Hello, {{ name }}!
    """
    tpl_dir = tmp_path / "templates_test"
    tpl_dir.mkdir()
    (tpl_dir / "greeting.j2").write_text("Hello, {{ name }}!", encoding="utf-8")
    return tpl_dir


def test_render_to_string(simple_template_dir):
    """
    Given a template directory containing 'greeting.j2',
    TemplateEngine.render_to_string should return the rendered text.
    """
    engine = TemplateEngine([simple_template_dir], auto_reload=False)
    output = engine.render_to_string("greeting.j2", {"name": "Alice"})
    assert isinstance(output, str)
    assert output.strip() == "Hello, Alice!"


def test_render_to_file(simple_template_dir, tmp_path):
    """
    Given a template directory with 'greeting.j2', render_to_file should:
      1. Create the destination directory if it doesn't exist.
      2. Write the rendered output to the specified file.
    """
    engine = TemplateEngine([simple_template_dir], auto_reload=False)
    destination = tmp_path / "output_folder" / "result.txt"

    assert not (tmp_path / "output_folder").exists()

    engine.render_to_file("greeting.j2", {"name": "Bob"}, destination)

    assert (tmp_path / "output_folder").exists()

    assert destination.exists()
    content = destination.read_text(encoding="utf-8").strip()
    assert content == "Hello, Bob!"


def test_template_not_found(simple_template_dir):
    """
    If the requested template name does not exist in any of the configured
    template directories, TemplateEngine.render_to_string should raise a TemplateNotFound error.
    """
    engine = TemplateEngine([simple_template_dir], auto_reload=False)
    with pytest.raises(Exception) as exc_info:
        engine.render_to_string("nonexistent.j2", {"name": "Test"})
    assert "nonexistent.j2" in str(exc_info.value)
