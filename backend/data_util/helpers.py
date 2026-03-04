def normalize_to_list(value):
    if not isinstance(value, (int, list)):
        raise TypeError("Expected int or list")
    return value if isinstance(value, list) else [value]
