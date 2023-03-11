import argparse
import logging
from typing import Union

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
    
    
    
def slow_start_fast_end_smoothing(x: float, p: float, max_value: int) -> float:
    """
    Maps an input value to an output value using a power function with a slow start and fast end.

    The output value increases slowly at the beginning when the input value is small,
    but increases more rapidly as the input value approaches the maximum value of 10.

    Args:
        x (float): The input value to be mapped, in the range of 0 to 10.
        p (float): The exponent of the power function used to map the input value to the output value.
            A larger value of p will result in a faster increase in the output value towards the end of the range.

    Returns:
        float: The mapped output value, in the range of 0 to 10.
    """
    
    ratio = x / max_value
    output = ratio ** p * max_value
    return output if x >= 0 else -abs(output)


def map_range(
    input_value: Union[int,float], 
    min_input: Union[int,float], 
    max_input: Union[int,float], 
    min_output: Union[int,float], 
    max_output: Union[int,float]
    ) -> Union[int,float]:
    """
    Maps an input value from one range to another range.

    Parameters:
        input_value (float): The input value to be mapped to the output range.
        min_input (float): The minimum value of the input range.
        max_input (float): The maximum value of the input range.
        min_output (float): The minimum value of the output range.
        max_output (float): The maximum value of the output range.

    Returns:
        float: The mapped value in the output range.

    Example:
        >>> map_range(-0.5, -1, 1, 0, 180)
        90.0
    """
    mapped_value = ((input_value - min_input) / (max_input - min_input)) * (max_output - min_output) + min_output
    return mapped_value

