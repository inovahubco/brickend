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

    Protected regions allow user-customized code to be preserved across regenerations.
    """

    START_PATTERN = re.compile(r'^\s*#\s*BRICKEND:PROTECTED-START\s+(\w+)\s*$')
    END_PATTERN = re.compile(r'^\s*#\s*BRICKEND:PROTECTED-END\s+(\w+)\s*$')

    def __init__(self) -> None:
        """Initialize the ProtectedRegionsHandler."""
        pass

    def extract_protected_regions(self, content: str) -> Dict[str, List[str]]:
        """
        Extract all protected regions from the given content.

        Args:
            content (str): Source code to scan for protected regions.

        Returns:
            Dict[str, List[str]]: Mapping from region name to list of lines
                including the START and END markers.
        """
        lines = content.splitlines()
        regions: Dict[str, List[str]] = {}
        current_region: str = ""
        current_content: List[str] = []

        for line in lines:
            start_match = self.START_PATTERN.match(line)
            end_match = self.END_PATTERN.match(line)

            if start_match:
                current_region = start_match.group(1)
                current_content = [line]
            elif end_match and current_region:
                if end_match.group(1) == current_region:
                    current_content.append(line)
                    regions[current_region] = current_content
                    current_region = ""
                    current_content = []
            elif current_region:
                current_content.append(line)

        return regions

    def inject_protected_regions(self, new_content: str, protected_regions: Dict[str, List[str]]) -> str:
        """
        Inject protected regions into newly generated content.

        Args:
            new_content (str): Newly generated file content.
            protected_regions (Dict[str, List[str]]): Regions extracted from existing file.

        Returns:
            str: Combined content with protected regions injected.
        """
        if not protected_regions:
            return new_content

        lines = new_content.splitlines()
        result_lines: List[str] = []

        for line in lines:
            result_lines.append(line)
            for region_name, region_content in protected_regions.items():
                if self._find_injection_point(line, region_name):
                    result_lines.append("")  # blank line before
                    result_lines.extend(region_content)
                    result_lines.append("")  # blank line after

        return "\n".join(result_lines)

    def _find_injection_point(self, line: str, region_name: str) -> bool:
        """
        Determine if a protected region should be injected after the given line.

        Implements simple heuristics, e.g., for CRUD_METHODS inject after imports.

        Args:
            line (str): Current line of generated content.
            region_name (str): Name of the region to inject.

        Returns:
            bool: True if injection should occur after this line.
        """
        stripped = line.strip()
        if region_name == "CRUD_METHODS":
            if (stripped.startswith("from ") or stripped.startswith("import ")) and not stripped.startswith("def "):
                return True
        return False

    def preserve_protected_regions(self, existing_file: Path, new_content: str) -> str:
        """
        Extract protected regions from an existing file and inject into new content.

        Args:
            existing_file (Path): Path to the file with existing protected regions.
            new_content (str): Newly generated content.

        Returns:
            str: New content with existing protected regions preserved.
        """
        if not existing_file.exists():
            return new_content

        try:
            existing_content = existing_file.read_text(encoding="utf-8")
            regions = self.extract_protected_regions(existing_content)
            return self.inject_protected_regions(new_content, regions)
        except Exception as e:
            # On failure, return new content unchanged
            print(f"Warning: Could not preserve protected regions: {e}")
            return new_content


class SmartProtectedRegionsHandler(ProtectedRegionsHandler):
    """
    Enhanced handler with smarter injection strategies for protected regions.
    """

    def inject_protected_regions(self, new_content: str, protected_regions: Dict[str, List[str]]) -> str:
        """
        Inject protected regions using advanced heuristics and avoid duplicate insertion.

        Args:
            new_content (str): Newly generated file content.
            protected_regions (Dict[str, List[str]]): Regions extracted from existing file.

        Returns:
            str: Combined content with protected regions injected.
        """
        if not protected_regions:
            return new_content

        lines = new_content.splitlines()
        result_lines: List[str] = []
        injected = set()

        for idx, line in enumerate(lines):
            result_lines.append(line)
            for name, content in protected_regions.items():
                if name in injected:
                    continue
                if self._should_inject_here(lines, idx, line, name):
                    result_lines.append("")  # blank before
                    result_lines.extend(content)
                    result_lines.append("")  # blank after
                    injected.add(name)

        # Insert any remaining regions before the last function or at end
        remaining = set(protected_regions.keys()) - injected
        if remaining:
            # Find last function definition
            last_func = None
            for i in reversed(range(len(result_lines))):
                if result_lines[i].strip().startswith("def "):
                    last_func = i
                    break
            for name in remaining:
                content = protected_regions[name]
                if last_func is not None:
                    # Insert before last function
                    result_lines.insert(last_func, "")
                    for line in reversed(content):
                        result_lines.insert(last_func, line)
                    result_lines.insert(last_func, "")
                else:
                    # Append at end
                    result_lines.append("")
                    result_lines.extend(content)

        return "\n".join(result_lines)

    def _should_inject_here(self, lines: List[str], index: int, line: str, region_name: str) -> bool:
        """
        Advanced logic to determine injection points for protected regions.

        Args:
            lines (List[str]): All lines of generated content.
            index (int): Current line index.
            line (str): Current line content.
            region_name (str): Name of the region to inject.

        Returns:
            bool: True if injection should occur at this point.
        """
        if region_name == "CRUD_METHODS" and self._is_import_line(line.strip()):
            # Look ahead for first function definition
            for j in range(index + 1, len(lines)):
                nxt = lines[j].strip()
                if not nxt:
                    continue
                if nxt.startswith("def "):
                    return True
                if self._is_import_line(nxt):
                    break
                return False
        return False

    def _is_import_line(self, line: str) -> bool:
        """
        Check if a line is an import statement (excluding function definitions).

        Args:
            line (str): Line to check.

        Returns:
            bool: True if the line is an import statement.
        """
        return (line.startswith("from ") or line.startswith("import ")) and not line.startswith("def ")
