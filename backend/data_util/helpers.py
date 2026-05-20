def normalize_to_list[T](value: T | list[T]) -> list[T]:
    """
    Helper to normalize input value to list

    Args:
        value (T | list[T]): Input value of type T or list of values of type T

    Return:
        list[T]: List of value(s) of type T 
    """
    if not isinstance(value, list):
        return [value]
    return value
