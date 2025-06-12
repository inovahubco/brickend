"""
test_protected_regions.py

Unit tests for protected regions functionality in CodeGenerator and SmartProtectedRegionsHandler.
Covers:
  - Preservation of a single protected region across regenerations.
  - Direct testing of SmartProtectedRegionsHandler.extract_protected_regions and inject_protected_regions.
  - Verification of project file structure generation.
  - Disabling of protected regions.
  - Handling of multiple protected regions in one file.
  - Robustness against malformed protected region markers.
  - Debugging context structure for template expectations.
  - Edge cases for extraction and injection with empty or missing files.
"""

from pathlib import Path

from brickend_core.engine.context_builder import ContextBuilder
from brickend_core.engine.template_registry import TemplateRegistry
from brickend_core.engine.template_engine import TemplateEngine
from brickend_core.engine.code_generator import CodeGenerator
from brickend_core.engine.protected_regions import SmartProtectedRegionsHandler


def test_protected_regions(tmp_path):
    """
    Ensure that a protected region in user_crud.py is preserved across regenerations.

    Steps:
      1. Generate initial CRUD file for a User entity.
      2. Manually insert a CRUD_METHODS protected region.
      3. Regenerate code.
      4. Verify the custom protected block remains in the regenerated file.

    Args:
        tmp_path (Path): Temporary directory fixture for output generation.
    """
    entities_dict = {
        "entities": [
            {
                "name": "User",
                "fields": [
                    {"name": "id", "type": "uuid", "primary_key": True, "unique": True, "nullable": False}
                ]
            }
        ]
    }
    builder = ContextBuilder()
    context = builder.build_context(entities_dict)

    template_dir = (
        Path(__file__)
        .parents[2]
        / "brickend_core"
        / "integrations"
        / "back"
        / "fastapi"
    )
    registry = TemplateRegistry([template_dir])
    engine = TemplateEngine([template_dir], auto_reload=False)

    output_dir = tmp_path / "output"
    generator = CodeGenerator(engine, registry, output_dir, preserve_protected_regions=True)
    generator.generate_project(context, "fastapi")

    # Path to the generated CRUD file (now in app/crud/ directory)
    crud_path = output_dir / "app" / "crud" / "user_crud.py"
    assert crud_path.exists(), f"user_crud.py was not generated at {crud_path}"

    original_content = crud_path.read_text(encoding="utf-8")
    print("=== ORIGINAL CONTENT ===")
    print(original_content)

    original_lines = original_content.splitlines()

    insert_index = None
    for i, line in enumerate(original_lines):
        stripped = line.strip()
        if stripped.startswith("from ") or stripped.startswith("import "):
            for j in range(i + 1, len(original_lines)):
                next_line = original_lines[j].strip()
                if not next_line:
                    continue
                if next_line.startswith("def "):
                    insert_index = i + 1
                    break
                if next_line.startswith("from ") or next_line.startswith("import "):
                    break
            if insert_index:
                break

    if insert_index is None:
        for i, line in enumerate(original_lines):
            stripped = line.strip()
            if not (stripped.startswith("from ") or stripped.startswith("import ")) and stripped:
                insert_index = i
                break

    assert insert_index is not None, "Could not find insertion point for protected region"

    protected_block = [
        "",  # blank line before
        "# BRICKEND:PROTECTED-START CRUD_METHODS",
        "# Custom user logic here",
        "def custom_user_function():",
        "    pass",
        "# BRICKEND:PROTECTED-END CRUD_METHODS",
        ""   # blank line after
    ]

    modified_lines = (
        original_lines[:insert_index]
        + protected_block
        + original_lines[insert_index:]
    )

    modified_content = "\n".join(modified_lines)
    crud_path.write_text(modified_content, encoding="utf-8")

    print("=== MODIFIED CONTENT WITH PROTECTED REGION ===")
    print(modified_content)

    generator.generate_project(context, "fastapi")

    new_content = crud_path.read_text(encoding="utf-8")
    print("=== CONTENT AFTER REGENERATION ===")
    print(new_content)

    assert "# Custom user logic here" in new_content, "Protected region was not preserved after regeneration"
    assert "def custom_user_function():" in new_content, "Protected function was not preserved"
    assert "# BRICKEND:PROTECTED-START CRUD_METHODS" in new_content, "Protected region start marker missing"
    assert "# BRICKEND:PROTECTED-END CRUD_METHODS" in new_content, "Protected region end marker missing"


def test_protected_regions_handler_directly():
    """
    Test the SmartProtectedRegionsHandler functionality directly.

    Verifies:
      - extract_protected_regions correctly identifies a well-formed region.
      - inject_protected_regions reinserts the region into new content at the correct point.
    """
    handler = SmartProtectedRegionsHandler()

    content_with_regions = """from sqlalchemy.orm import Session
from app.models.user import User

# BRICKEND:PROTECTED-START CRUD_METHODS
# Custom user logic here
def custom_user_function():
    pass
# BRICKEND:PROTECTED-END CRUD_METHODS

def get_user(db: Session, id: str):
    return db.query(User).first()
"""

    regions = handler.extract_protected_regions(content_with_regions)
    assert "CRUD_METHODS" in regions
    assert "# Custom user logic here" in "\n".join(regions["CRUD_METHODS"])

    new_content = """from sqlalchemy.orm import Session
from app.models.user import User

def get_user(db: Session, id: str):
    return db.query(User).first()

def create_user(db: Session, user_data):
    return user_data
"""

    injected_content = handler.inject_protected_regions(new_content, regions)
    assert "# Custom user logic here" in injected_content
    assert "def custom_user_function():" in injected_content


def test_project_structure_generation(tmp_path):
    """
    Test that the correct file structure is generated for multiple entities.

    Verifies single-file templates under app/ and per-entity files in app/crud/ and app/routers/.

    Args:
        tmp_path (Path): Temporary directory fixture for output generation.
    """
    entities_dict = {
        "entities": [
            {
                "name": "User",
                "fields": [
                    {"name": "id", "type": "uuid", "primary_key": True, "unique": True, "nullable": False},
                    {"name": "email", "type": "string", "unique": True, "nullable": False}
                ]
            },
            {
                "name": "Post",
                "fields": [
                    {"name": "id", "type": "uuid", "primary_key": True, "unique": True, "nullable": False},
                    {"name": "title", "type": "string", "nullable": False}
                ]
            }
        ]
    }
    builder = ContextBuilder()
    context = builder.build_context(entities_dict)

    template_dir = (
        Path(__file__)
        .parents[2]
        / "brickend_core"
        / "integrations"
        / "back"
        / "fastapi"
    )
    registry = TemplateRegistry([template_dir])
    engine = TemplateEngine([template_dir], auto_reload=False)

    output_dir = tmp_path / "output"
    generator = CodeGenerator(engine, registry, output_dir)
    generator.generate_project(context, "fastapi")

    # Verify single files are generated under app/ directory
    assert (output_dir / "app" / "models.py").exists(), "models.py not generated under app/"
    assert (output_dir / "app" / "schemas.py").exists(), "schemas.py not generated under app/"
    assert (output_dir / "app" / "main.py").exists(), "main.py not generated under app/"
    assert (output_dir / "app" / "database.py").exists(), "database.py not generated under app/"

    # Verify per-entity CRUD files
    assert (output_dir / "app" / "crud" / "user_crud.py").exists(), "user_crud.py not generated"
    assert (output_dir / "app" / "crud" / "post_crud.py").exists(), "post_crud.py not generated"

    # Verify per-entity Router files
    assert (output_dir / "app" / "routers" / "user_router.py").exists(), "user_router.py not generated"
    assert (output_dir / "app" / "routers" / "post_router.py").exists(), "post_router.py not generated"


def test_disable_protected_regions(tmp_path):
    """
    Test that protected regions can be disabled and are overwritten on regeneration.

    Args:
        tmp_path (Path): Temporary directory fixture for output generation.
    """
    entities_dict = {
        "entities": [
            {
                "name": "User",
                "fields": [
                    {"name": "id", "type": "uuid", "primary_key": True, "unique": True, "nullable": False}
                ]
            }
        ]
    }
    builder = ContextBuilder()
    context = builder.build_context(entities_dict)

    template_dir = (
        Path(__file__)
        .parents[2]
        / "brickend_core"
        / "integrations"
        / "back"
        / "fastapi"
    )
    registry = TemplateRegistry([template_dir])
    engine = TemplateEngine([template_dir], auto_reload=False)

    output_dir = tmp_path / "output"

    # Generate with protection disabled
    generator = CodeGenerator(engine, registry, output_dir, preserve_protected_regions=False)
    generator.generate_project(context, "fastapi")

    crud_path = output_dir / "app" / "crud" / "user_crud.py"

    # Add protected region
    original_content = crud_path.read_text(encoding="utf-8")
    modified_content = original_content + "\n# BRICKEND:PROTECTED-START TEST\n# Custom code\n# BRICKEND:PROTECTED-END TEST\n"
    crud_path.write_text(modified_content, encoding="utf-8")

    # Regenerate - should overwrite everything since protection is disabled
    generator.generate_project(context, "fastapi")

    new_content = crud_path.read_text(encoding="utf-8")
    assert "# Custom code" not in new_content, "Protected region should not be preserved when protection is disabled"


def test_multiple_protected_regions(tmp_path):
    """
    Test handling of multiple protected regions in the same file.

    Verifies that all inserted regions are preserved after code regeneration.

    Args:
        tmp_path (Path): Temporary directory fixture for output generation.
    """
    entities_dict = {
        "entities": [
            {
                "name": "User",
                "fields": [
                    {"name": "id", "type": "uuid", "primary_key": True, "unique": True, "nullable": False}
                ]
            }
        ]
    }
    builder = ContextBuilder()
    context = builder.build_context(entities_dict)

    template_dir = (
        Path(__file__)
        .parents[2]
        / "brickend_core"
        / "integrations"
        / "back"
        / "fastapi"
    )
    registry = TemplateRegistry([template_dir])
    engine = TemplateEngine([template_dir], auto_reload=False)

    output_dir = tmp_path / "output"
    generator = CodeGenerator(engine, registry, output_dir, preserve_protected_regions=True)
    generator.generate_project(context, "fastapi")

    crud_path = output_dir / "app" / "crud" / "user_crud.py"

    # Add multiple protected regions
    original_content = crud_path.read_text(encoding="utf-8")
    lines = original_content.splitlines()

    # Insert first protected region after imports
    insert_index1 = None
    for i, line in enumerate(lines):
        if line.strip().startswith("from ") or line.strip().startswith("import "):
            insert_index1 = i + 1

    assert insert_index1 is not None

    region1 = [
        "",
        "# BRICKEND:PROTECTED-START HELPERS",
        "def custom_helper():",
        "    return 'helper'",
        "# BRICKEND:PROTECTED-END HELPERS",
        ""
    ]

    region2 = [
        "",
        "# BRICKEND:PROTECTED-START VALIDATORS",
        "def validate_user(user):",
        "    return True",
        "# BRICKEND:PROTECTED-END VALIDATORS",
        ""
    ]

    # Insert both regions
    modified_lines = lines[:insert_index1] + region1 + region2 + lines[insert_index1:]
    crud_path.write_text("\n".join(modified_lines), encoding="utf-8")

    # Regenerate
    generator.generate_project(context, "fastapi")

    # Verify both regions are preserved
    new_content = crud_path.read_text(encoding="utf-8")
    assert "def custom_helper():" in new_content, "First protected region not preserved"
    assert "def validate_user(user):" in new_content, "Second protected region not preserved"
    assert "# BRICKEND:PROTECTED-START HELPERS" in new_content
    assert "# BRICKEND:PROTECTED-START VALIDATORS" in new_content


def test_protected_regions_with_syntax_errors():
    """
    Test that malformed protected region markers are ignored during extraction.

    Verifies that only properly closed regions are extracted and others are skipped.
    """
    handler = SmartProtectedRegionsHandler()

    malformed_content = """from sqlalchemy.orm import Session

# BRICKEND:PROTECTED-START REGION1
# Some code
# Missing end marker

# BRICKEND:PROTECTED-START REGION2  
# Some other code
# BRICKEND:PROTECTED-END REGION2

# BRICKEND:PROTECTED-END REGION3  # End without start

def some_function():
    pass
"""

    # Should only extract properly formed regions
    regions = handler.extract_protected_regions(malformed_content)
    assert len(regions) == 1, f"Expected 1 region, got {len(regions)}"
    assert "REGION2" in regions, "REGION2 should be extracted"
    assert "REGION1" not in regions, "REGION1 should not be extracted (no end marker)"
    assert "REGION3" not in regions, "REGION3 should not be extracted (no start marker)"


def test_debug_context_structure(tmp_path):
    """
    Debug test to inspect the context dictionary produced by ContextBuilder.

    Prints out keys, entity count, and naming structures for manual inspection.

    Args:
        tmp_path (Path): Temporary directory fixture (unused in content).
    """
    entities_dict = {
        "entities": [
            {
                "name": "User",
                "fields": [
                    {"name": "id", "type": "uuid", "primary_key": True, "unique": True, "nullable": False}
                ]
            }
        ]
    }
    builder = ContextBuilder()
    context = builder.build_context(entities_dict)

    print("=== CONTEXT STRUCTURE ===")
    print(f"Context keys: {list(context.keys())}")
    print(f"Entity count: {context.get('entity_count', 0)}")

    if 'entities' in context:
        print(f"Found {len(context['entities'])} entities:")
        for i, entity in enumerate(context['entities']):
            print(f"  Entity {i}: {entity.get('original_name', 'Unknown')}")
            if 'names' in entity:
                print(f"    Names: {entity['names']}")
                print(f"    Fields count: {entity.get('field_count', 0)}")
            else:
                print("    No 'names' field found!")

    entities = context.get('entities', [])
    if entities:
        entity_context = context.copy()
        entity_context['entity'] = entities[0]
        print(f"\n=== ENTITY-SPECIFIC CONTEXT ===")
        print(f"Entity context keys: {list(entity_context.keys())}")
        print(f"Entity name: {entity_context['entity']['names']['snake']}")


def test_edge_cases_protected_regions():
    """
    Test edge cases for protected regions handling.

    Verifies:
      - extract_protected_regions returns empty dict on empty content.
      - No injection errors when injecting into content without functions.
      - preserve_protected_regions returns new_content unchanged for non-existent files.
    """
    handler = SmartProtectedRegionsHandler()

    regions = handler.extract_protected_regions("")
    assert len(regions) == 0

    normal_content = """from sqlalchemy.orm import Session

def get_user():
    pass
"""
    regions = handler.extract_protected_regions(normal_content)
    assert len(regions) == 0

    new_content = "# Just a comment"
    test_regions = {
        "TEST": ["# BRICKEND:PROTECTED-START TEST", "# code", "# BRICKEND:PROTECTED-END TEST"]
    }

    result = handler.inject_protected_regions(new_content, test_regions)
    assert "# code" in result

    from pathlib import Path
    import tempfile

    with tempfile.TemporaryDirectory() as tmp_dir:
        non_existent_file = Path(tmp_dir) / "does_not_exist.py"
        result = handler.preserve_protected_regions(non_existent_file, "new content")
        assert result == "new content"
