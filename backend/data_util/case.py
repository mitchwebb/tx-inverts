import re


def to_snake_case(string: str) -> str:
    """Converts string to snake case, preserving acronyms"""
    # Handle acronyms and consecutive uppercase letters
    string = re.sub(r'(.)([A-Z][a-z]+)', r'\1_\2', string)
    string = re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', string)
    return string.lower()
