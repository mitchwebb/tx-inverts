# Helper to convert text to snake case (non-reversible)
import re


def to_snake_case(string: str) -> str:
    '''Converts a string to snake case, preserving acronyms'''
    # Handle acronyms by skipping consecutive uppercase letters
    string = re.sub(r'(.)([A-Z][a-z]+)', r'\1_\2', string)
    string = re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', string)
    return string.lower()
