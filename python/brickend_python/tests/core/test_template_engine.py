"""
test_template_engine.py

Unit tests for the TemplateEngine class in brickend_core.engine.template_engine.
Covers:
  - Rendering a Jinja2 template to a string.
  - Writing rendered output to a file and creating parent directories.
  - Error handling when a template is not found.
"""

import pytest
from brickend_core.engine.template_engine import TemplateEngine


@pytest.fixture
def simple_template_dir(tmp_path):
    """
    Create a temporary directory with a single Jinja2 template for testing.

    The template will be named 'greeting.j2' and contain:
        Hello, {{ name }}!
    """
    tpl_dir = tmp_path / "templates_test"
    tpl_dir.mkdir()
    (tpl_dir / "greeting.j2").write_text("Hello, {{ name }}!", encoding="utf-8")
    return tpl_dir


def test_render_to_string(simple_template_dir):
    """
    Test that TemplateEngine.render_to_string returns the correctly rendered text.

    Given a template directory containing 'greeting.j2' with content "Hello, {{ name }}!",
    calling render_to_string with context {"name": "Alice"} should return "Hello, Alice!".
    """
    engine = TemplateEngine([simple_template_dir], auto_reload=False)
    output = engine.render_to_string("greeting.j2", {"name": "Alice"})
    assert isinstance(output, str)
    assert output.strip() == "Hello, Alice!"


def test_render_to_file(simple_template_dir, tmp_path):
    """
    Test that TemplateEngine.render_to_file writes rendered output to the specified file.

    Verifies:
      1. The destination directory is created if it does not exist.
      2. The rendered content "Hello, Bob!" is written to 'result.txt' under the output folder.
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
    Test that requesting a non-existent template raises a TemplateNotFound error.

    Calling render_to_string with "nonexistent.j2" should raise an exception
    mentioning that 'nonexistent.j2' could not be found.
    """
    engine = TemplateEngine([simple_template_dir], auto_reload=False)
    with pytest.raises(Exception) as exc_info:
        engine.render_to_string("nonexistent.j2", {"name": "Test"})
    assert "nonexistent.j2" in str(exc_info.value)
