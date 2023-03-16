from typing import Union


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