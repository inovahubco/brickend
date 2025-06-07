"""
test_init_project.py

Unit tests for the 'init project' CLI command in cli.commands.init_command.
Covers:
  1. Successful initialization of a fastapi skeleton.
  2. Error when target folder already exists.
  3. Error when skeleton type is invalid.
"""

import pytest
from pathlib import Path
from typer.testing import CliRunner

from brickend_cli.main import app as cli_app


@pytest.fixture(autouse=True)
def ensure_skeletons_exist(monkeypatch):
    """
    Ensure that the CLI can find the 'templates/skeletons/fastapi' folder
    by setting the working directory to the project root.
    """
    real_project_root = Path(__file__).parents[2]
    monkeypatch.chdir(real_project_root)
    fastapi_skel = real_project_root / "templates" / "skeletons" / "fastapi"
    assert fastapi_skel.is_dir(), "FastAPI skeleton directory must exist"
    yield


def test_init_project_success(tmp_path):
    """
    Given a valid skeleton type 'fastapi', init should create the target folder
    with expected files and directories.
    """
    runner = CliRunner()

    with runner.isolated_filesystem():
        project_root = Path.cwd()
        (project_root / "templates" / "skeletons" / "fastapi").mkdir(parents=True, exist_ok=True)
        (project_root / "templates" / "skeletons" / "fastapi" / "app").mkdir(parents=True, exist_ok=True)
        (project_root / "templates" / "skeletons" / "fastapi" / "app" / "__init__.py").write_text("", encoding="utf-8")
        (project_root / "templates" / "skeletons" / "fastapi" / "migrations").mkdir(parents=True, exist_ok=True)
        (project_root / "templates" / "skeletons" / "fastapi" / "migrations" / "env.py").write_text("# alembic env", encoding="utf-8")
        (project_root / "templates" / "skeletons" / "fastapi" / "migrations" / "script.py.mako").write_text("# script", encoding="utf-8")
        (project_root / "templates" / "skeletons" / "fastapi" / "migrations" / "versions").mkdir(parents=True, exist_ok=True)
        (project_root / "templates" / "skeletons" / "fastapi" / "alembic.ini").write_text("[alembic]", encoding="utf-8")
        (project_root / "templates" / "skeletons" / "fastapi" / "entities.yaml").write_text("entities: []", encoding="utf-8")
        (project_root / "templates" / "skeletons" / "fastapi" / "requirements.txt").write_text("fastapi\nsqlalchemy", encoding="utf-8")
        (project_root / "templates" / "skeletons" / "fastapi" / "README.md").write_text("# README", encoding="utf-8")
        (project_root / "templates" / "skeletons" / "fastapi" / "templates_user").mkdir(parents=True, exist_ok=True)

        result = runner.invoke(cli_app, ["init", "project", "demo_app", "--type", "fastapi"])
        assert result.exit_code == 0, f"CLI failed: {result.stdout}\n{result.stderr}"
        assert "✅ Project 'demo_app' created using skeleton 'fastapi'." in result.stdout

        demo_dir = Path("demo_app")

        assert (demo_dir / "app" / "__init__.py").exists()
        assert (demo_dir / "migrations" / "env.py").exists()
        assert (demo_dir / "migrations" / "script.py.mako").exists()
        assert (demo_dir / "migrations" / "versions").is_dir()
        assert (demo_dir / "alembic.ini").exists()
        assert (demo_dir / "entities.yaml").exists()
        assert (demo_dir / "requirements.txt").exists()
        assert (demo_dir / "README.md").exists()
        assert (demo_dir / "templates_user").is_dir()


def test_init_project_folder_exists(tmp_path):
    """
    If the target folder already exists, init should exit with an error.
    """
    runner = CliRunner()

    with runner.isolated_filesystem():
        project_root = Path.cwd()
        (project_root / "templates" / "skeletons" / "fastapi" / "app").mkdir(parents=True, exist_ok=True)
        (project_root / "templates" / "skeletons" / "fastapi" / "app" / "__init__.py").write_text("", encoding="utf-8")
        Path("existing_app").mkdir()

        result = runner.invoke(cli_app, ["init", "project", "existing_app", "--type", "fastapi"])
        assert result.exit_code != 0
        assert "Error: The folder 'existing_app' already exists." in result.stdout


def test_init_project_invalid_type(tmp_path):
    """
    If the skeleton type is invalid, init should exit with an error indicating missing skeleton.
    """
    runner = CliRunner()

    with runner.isolated_filesystem():
        project_root = Path.cwd()
        (project_root / "templates" / "skeletons" / "fastapi" / "app").mkdir(parents=True, exist_ok=True)
        (project_root / "templates" / "skeletons" / "fastapi" / "app" / "__init__.py").write_text("", encoding="utf-8")

        result = runner.invoke(cli_app, ["init", "project", "new_app", "--type", "invalid_type"])
        assert result.exit_code != 0
        assert "Error: No skeleton found for type 'invalid_type'." in result.stdout
