"""
protected_regions.py

Handles extraction and preservation of protected code regions during code regeneration.
Protected regions are marked with special comments:
# BRICKEND:PROTECTED-START [region_name]
# ... custom code ...
# BRICKEND:PROTECTED-END [region_name]
"""

import re
from pathlib import Path
from typing import Dict, List


class ProtectedRegionsHandler:
    """
    Handles extraction and insertion of protected code regions.
    """

    START_PATTERN = re.compile(r'^\s*#\s*BRICKEND:PROTECTED-START\s+(\w+)\s*$')
    END_PATTERN = re.compile(r'^\s*#\s*BRICKEND:PROTECTED-END\s+(\w+)\s*$')

    def __init__(self):
        """Initialize the handler."""
        pass

    def extract_protected_regions(self, content: str) -> Dict[str, List[str]]:
        """
        Extract all protected regions from the given content.

        Args:
            content (str): The source code content to scan.

        Returns:
            Dict[str, List[str]]: Dictionary mapping region names to their content lines.
        """
        lines = content.splitlines()
        regions = {}
        current_region = None
        current_content = []

        for line in lines:
            start_match = self.START_PATTERN.match(line)
            end_match = self.END_PATTERN.match(line)

            if start_match:
                region_name = start_match.group(1)
                current_region = region_name
                current_content = [line]  # Include the start marker
            elif end_match and current_region:
                region_name = end_match.group(1)
                if region_name == current_region:
                    current_content.append(line)  # Include the end marker
                    regions[current_region] = current_content
                    current_region = None
                    current_content = []
            elif current_region:
                current_content.append(line)

        return regions

    def inject_protected_regions(self, new_content: str, protected_regions: Dict[str, List[str]]) -> str:
        """
        Inject protected regions into newly generated content.

        This method looks for insertion points in the new content and inserts
        the protected regions at appropriate locations.

        Args:
            new_content (str): The newly generated content.
            protected_regions (Dict[str, List[str]]): Protected regions to inject.

        Returns:
            str: Content with protected regions injected.
        """
        if not protected_regions:
            return new_content

        lines = new_content.splitlines()
        result_lines = []

        for line in lines:
            # Add the current line
            result_lines.append(line)

            # Check if we should inject any protected regions after this line
            for region_name, region_content in protected_regions.items():
                injection_point = self._find_injection_point(line, region_name)
                if injection_point:
                    # Add a blank line before the protected region
                    result_lines.append("")
                    # Add the protected region
                    result_lines.extend(region_content)
                    # Add a blank line after the protected region
                    result_lines.append("")

        return "\n".join(result_lines)

    def _find_injection_point(self, line: str, region_name: str) -> bool:
        """
        Determine if a protected region should be injected after the given line.

        This implements heuristics for where to place protected regions.

        Args:
            line (str): The current line being processed.
            region_name (str): The name of the protected region.

        Returns:
            bool: True if the region should be injected after this line.
        """
        # For CRUD_METHODS region, inject after imports but before the first function
        if region_name == "CRUD_METHODS":
            # Inject after the last import statement
            if (line.strip().startswith("from ") or line.strip().startswith("import ")) and \
                    not line.strip().startswith("def "):
                return True

        # Add more heuristics for other region types as needed

        return False

    def preserve_protected_regions(self, existing_file: Path, new_content: str) -> str:
        """
        Extract protected regions from existing file and inject them into new content.

        Args:
            existing_file (Path): Path to the existing file with protected regions.
            new_content (str): The newly generated content.

        Returns:
            str: New content with protected regions preserved.
        """
        if not existing_file.exists():
            return new_content

        try:
            existing_content = existing_file.read_text(encoding="utf-8")
            protected_regions = self.extract_protected_regions(existing_content)
            return self.inject_protected_regions(new_content, protected_regions)
        except Exception as e:
            # If anything goes wrong, return the new content without protection
            # This ensures code generation doesn't fail due to protection logic
            print(f"Warning: Could not preserve protected regions: {e}")
            return new_content


class SmartProtectedRegionsHandler(ProtectedRegionsHandler):
    """
    Enhanced version that uses smarter injection strategies.
    """

    def inject_protected_regions(self, new_content: str, protected_regions: Dict[str, List[str]]) -> str:
        """
        Inject protected regions using smart positioning.
        """
        if not protected_regions:
            return new_content

        lines = new_content.splitlines()
        result_lines = []
        injected_regions = set()

        for i, line in enumerate(lines):
            # Add the current line
            result_lines.append(line)

            # Check for injection points
            for region_name, region_content in protected_regions.items():
                if region_name in injected_regions:
                    continue

                if self._should_inject_here(lines, i, line, region_name):
                    # Add the protected region
                    result_lines.append("")
                    result_lines.extend(region_content)
                    result_lines.append("")
                    injected_regions.add(region_name)

        # If any regions weren't injected, add them at the end before the last function
        remaining_regions = set(protected_regions.keys()) - injected_regions
        if remaining_regions:
            # Find the last function definition to insert before it
            last_func_index = None
            for i in reversed(range(len(result_lines))):
                if result_lines[i].strip().startswith("def "):
                    last_func_index = i
                    break

            if last_func_index is not None:
                # Insert remaining regions before the last function
                for region_name in remaining_regions:
                    region_content = protected_regions[region_name]
                    result_lines.insert(last_func_index, "")
                    for line in reversed(region_content):
                        result_lines.insert(last_func_index, line)
                    result_lines.insert(last_func_index, "")
            else:
                # If no functions found, append at the end
                for region_name in remaining_regions:
                    result_lines.append("")
                    result_lines.extend(protected_regions[region_name])

        return "\n".join(result_lines)

    def _should_inject_here(self, lines: List[str], current_index: int, current_line: str, region_name: str) -> bool:
        """
        Smarter logic for determining injection points.
        """
        if region_name == "CRUD_METHODS":
            # Inject after imports, before first function
            if self._is_import_line(current_line):
                # Check if next non-empty line is a function
                for j in range(current_index + 1, len(lines)):
                    next_line = lines[j].strip()
                    if not next_line:
                        continue
                    if next_line.startswith("def "):
                        return True
                    if self._is_import_line(lines[j]):
                        break
                    return False

        return False

    def _is_import_line(self, line: str) -> bool:
        """Check if a line is an import statement."""
        stripped = line.strip()
        return (stripped.startswith("from ") or stripped.startswith("import ")) and "def " not in stripped
