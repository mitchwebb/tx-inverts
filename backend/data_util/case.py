import re


def to_snake_case(name: str) -> str:
	# Insert underscore between lower and upper (but not in the middle of acronyms)
	name = re.sub(r'(?<=[a-z0-9])(?=[A-Z])', '_', name)
	return name.lower()