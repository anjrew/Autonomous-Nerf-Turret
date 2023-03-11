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

    i_value = value
    if type(i_value) != int or type(min_val) != int or type(max_val) != int or i_value < min_val or i_value > max_val :
        raise argparse.ArgumentTypeError(f"{value} is not within range [{min_val}, {max_val}] or is not an integer")
    return i_value


def is_valid_string_log_level(level_str: str) -> bool:
    """
    Check whether an input string matches one of the log levels defined in the logging module.

    Parameters:
        level_str (str): The input string to check.

    Returns:
        bool: True if the input string matches one of the log levels, False otherwise.
    """
    assert type(level_str) == str
    try:
        level = logging.getLevelName(level_str.upper())
        return is_valid_int_log_level(int(level))
    except ValueError:
        return False


def is_valid_int_log_level(level: int) -> bool:
    """
    Check whether an input int matches one of the log levels defined in the logging module.

    Parameters:
        level (int): The input int to check.

    Returns:
        bool: True if the input int matches one of the log levels, False otherwise.
    """
    assert type(level) == int
 
    return level in (logging.CRITICAL, logging.ERROR, logging.WARNING, logging.INFO, logging.DEBUG, logging.NOTSET)
   

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
    
    if type(level_str) == int or level_str.isdigit() and is_valid_int_log_level(int(level_str)):
        return int(level_str)
    
    elif level_str.isalpha() and is_valid_string_log_level(level_str):
        
        level_name = level_str.upper()
        return logging.getLevelName(level_name)
       
    else:
        raise argparse.ArgumentTypeError(f"Invalid logging level: {level_str}")