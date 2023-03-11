import argparse
import logging

def assert_in_int_range(value: int, min_val: int, max_val: int) -> int:
    """
    Check whether an input integer value is within a certain range.

    Parameters:
        value: The input value to check, as a integer.
        min_val: The minimum allowed value (inclusive).
        max_val: The maximum allowed value (inclusive).

    Returns:
        int: The input value, if it is within the allowed range.

    Raises:
        argparse.ArgumentTypeError: If the input value is not an integer or is outside the allowed range.
    """
    assert type(value) == int
    assert type(min_val) == int
    assert type(max_val) == int
    i_value = value
    if i_value < min_val or i_value > max_val:
        raise argparse.ArgumentTypeError(f"{value} is not within range [{min_val}, {max_val}]")
    return i_value




# Define the conversion function
def map_log_level(level_str: str) -> int:
    """
    Convert a logging level string to its corresponding integer value.

    Parameters:
        level_str (str): The logging level string to convert.

    Returns:
        int: The integer value corresponding to the logging level string.

    Raises:
        argparse.ArgumentTypeError: If the input value is not a valid logging level string.
    """
    if type(level_str) == int or level_str.isdigit():
        return int(level_str)
    elif level_str.isalpha():
        level_name = level_str.upper()
        try:
            level = logging.getLevelName(level_name)
            return level
        except ValueError:
            raise argparse.ArgumentTypeError(f"Invalid logging level: {level_str}")
    else:
        raise argparse.ArgumentTypeError(f"Invalid logging level: {level_str}")