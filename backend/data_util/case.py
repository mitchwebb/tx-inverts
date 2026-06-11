# Helper to convert text to snake case (non-reversible)
import re


def camel_to_snake_case(string: str) -> str:
    """
    Converts a string to snake case, preserving acronyms.
    This helper is intended to work with words comprised of numbers and letters,
    formatted in a typical camelCase format.

    Random strings of characters may not convert as expected.
    """
    # Handle acronyms by skipping consecutive uppercase letters
    string = re.sub(r'(.)([A-Z][a-z]+)', r'\1_\2', string)
    string = re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', string)
    return string.lower()
