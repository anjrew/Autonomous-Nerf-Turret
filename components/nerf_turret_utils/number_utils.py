from typing import Union
import argparse


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
    bottom_input = input_value - min_input
    input_range = max_input - min_input
    mapped_value = (bottom_input / input_range) * (max_output - min_output) + min_output
    return mapped_value


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
