"""
test_naming.py

Unit tests for naming helper functions:
- to_snake_case
- to_pascal_case
- to_kebab_case
- validate_name

Verifies that each function correctly transforms or validates input strings
across a variety of edge cases and formats.
"""

import pytest

from brickend_core.utils.naming import (
    to_snake_case,
    to_pascal_case,
    to_kebab_case,
    validate_name,
)


@pytest.mark.parametrize(
    "input_str, expected",
    [
        ("UserProfile", "user_profile"),
        ("userProfile", "user_profile"),
        ("user-profile", "user_profile"),
        ("User Profile", "user_profile"),
        ("HTTPServer", "http_server"),
        ("HTTP Server", "http_server"),
        ("already_snake_case", "already_snake_case"),
    ],
)
def test_to_snake_case_various(input_str, expected):
    """
    Parametrized test for `to_snake_case`.

    Ensures conversion of various input formats to lowercase snake_case, including:
      - PascalCase and camelCase.
      - Kebab-case and space-separated words.
      - Acronyms and already snake_case strings.
    """
    assert to_snake_case(input_str) == expected


@pytest.mark.parametrize(
    "input_str, expected",
    [
        ("user_profile", "UserProfile"),
        ("user-profile", "UserProfile"),
        ("user profile", "UserProfile"),
        ("HTTP server", "HttpServer"),
        ("multiple   spaces here", "MultipleSpacesHere"),
        ("mixed_CASE-example", "MixedCaseExample"),
    ],
)
def test_to_pascal_case_various(input_str, expected):
    """
    Parametrized test for `to_pascal_case`.

    Ensures conversion of various input formats to PascalCase (upper camel case), including:
      - snake_case and kebab-case.
      - Space-separated words.
      - Mixed-case and multiple spaces scenarios.
    """
    assert to_pascal_case(input_str) == expected


@pytest.mark.parametrize(
    "input_str, expected",
    [
        ("UserProfile", "user-profile"),
        ("user_profile", "user-profile"),
        ("user profile", "user-profile"),
        ("HTTPServer", "http-server"),
        ("mixed_CaseExample", "mixed-case-example"),
    ],
)
def test_to_kebab_case_various(input_str, expected):
    """
    Parametrized test for `to_kebab_case`.

    Ensures conversion of various input formats to lowercase kebab-case, including:
      - PascalCase and snake_case.
      - Space-separated and mixed-case inputs.
      - Acronyms handling.
    """
    assert to_kebab_case(input_str) == expected


@pytest.mark.parametrize(
    "name, is_valid",
    [
        ("User", True),
        ("user1", True),
        ("_user", False),
        ("1User", False),
        ("User-Name", False),
        ("user_name_123", True),
        ("userName", True),
        ("", False),
        ("A", True),
        ("a_b_c", True),
        ("with space", False),
    ],
)
def test_validate_name(name, is_valid):
    """
    Parametrized test for `validate_name`.

    Validates that names:
      - Start with a letter and contain only letters, digits, or underscores.
      - Reject names beginning with digits, underscores, hyphens, or containing spaces.
      - Accept single letters and mixed-case alphanumeric patterns.
    """
    assert validate_name(name) is is_valid
