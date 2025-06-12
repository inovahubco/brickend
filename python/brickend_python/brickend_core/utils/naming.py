"""
naming.py

Helper functions to convert between different naming conventions:
  - snake_case
  - PascalCase
  - kebab-case

Also includes a validator to check that an entity or field name
matches a basic regex (starts with a letter, only letters/digits/underscores).
"""

import re


def to_snake_case(text: str) -> str:
    """
    Convert a string (PascalCase, camelCase, kebab-case or with spaces)
    to snake_case.

    Examples:
        to_snake_case("UserProfile")   -> "user_profile"
        to_snake_case("userProfile")   -> "user_profile"
        to_snake_case("user-profile")  -> "user_profile"
        to_snake_case("User Profile")  -> "user_profile"
        to_snake_case("HTTPServer")    -> "http_server"

    Args:
        text (str): Input string in any of the supported formats.

    Returns:
        str: Converted string in lowercase snake_case.
    """
    intermediate = re.sub(r"[\-\s]+", "_", text)
    intermediate = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", intermediate)
    intermediate = re.sub(r"([a-z\d])([A-Z])", r"\1_\2", intermediate)

    return intermediate.lower()


def to_pascal_case(text: str) -> str:
    """
    Convert a string (snake_case, kebab-case or with spaces)
    to PascalCase (UpperCamelCase).

    Examples:
        to_pascal_case("user_profile")  -> "UserProfile"
        to_pascal_case("user-profile")  -> "UserProfile"
        to_pascal_case("user profile")  -> "UserProfile"
        to_pascal_case("HTTP server")   -> "HttpServer"

    Args:
        text (str): Input string in any of the supported formats.

    Returns:
        str: Converted string in PascalCase.
    """
    parts = re.split(r"[_\-\s]+", text)
    return "".join(part.capitalize() for part in parts if part)


def to_kebab_case(text: str) -> str:
    """
    Convert a string (PascalCase, camelCase, snake_case or with spaces)
    to kebab-case.

    Examples:
        to_kebab_case("UserProfile")    -> "user-profile"
        to_kebab_case("user_profile")   -> "user-profile"
        to_kebab_case("user profile")   -> "user-profile"
        to_kebab_case("HTTPServer")     -> "http-server"

    Args:
        text (str): Input string in any of the supported formats.

    Returns:
        str: Converted string in kebab-case (all lowercase).
    """
    snake = to_snake_case(text)
    return snake.replace("_", "-")


def validate_name(name: str) -> bool:
    """
    Validate that a given name (entity or field) matches the pattern:
      - Starts with an ASCII letter [A-Za-z]
      - Followed by zero or more letters, digits, or underscores [A-Za-z0-9_]*

    This forbids names that begin with a digit, underscore, hyphen, etc.

    Examples:
        validate_name("User")       -> True
        validate_name("user1")      -> True
        validate_name("_user")      -> False
        validate_name("1User")      -> False
        validate_name("User-Name")  -> False

    Args:
        name (str): The name to validate.

    Returns:
        bool: True if the name is valid, False otherwise.
    """
    pattern = r"^[A-Za-z][A-Za-z0-9_]*$"
    return bool(re.match(pattern, name))
