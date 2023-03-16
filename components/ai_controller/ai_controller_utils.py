import argparse
from typing import List, Optional, Union

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
    bottom_input = input_value - min_input
    input_range = max_input - min_input
    mapped_value = (bottom_input / input_range) * (max_output - min_output) + min_output
    return mapped_value


def get_priority_target_index(targets: List[dict], type: str,  target_ids: List[str]=[]) -> Optional[int]:
    """
    Returns the index of the highest priority target in the `targets` list based on the input `ids` and `type`.

    Args:
        targets: A list of dictionaries, each representing a target with the keys 'id' and 'type'.
        type: A target type to prioritize if none of the target IDs are found.
        target_ids: A list of target IDs to prioritize over the target types.

    Returns:
        The index of the highest priority target in the `targets` list. Returns 0 if no target is found.

    Example:
        targets = [
            {"id": "001", "type": "person"},
            {"id": "002", "type": "vehicle"},
            {"id": "003", "type": "person"}
        ]
        ids = ["003", "004"]
        type = "vehicle"
        index = get_priority_target_index(targets, ids, type)
        # Returns 1 (index of the "002" target in the `targets` list)
    """
    if len(target_ids) > 0: # If there are target IDs just check if the target IDs face is in the list
        assert type == "face", "The `type` argument must be 'face' if the `ids` argument is not empty, as these are face IDs."
        for i, target in enumerate(targets):
            if target.get("id", None) in target_ids:
                return i
    else:
        for i, target in enumerate(targets):
            if target["type"] == 'person' and type == 'person':
                # If the target is a person, check if it has a face
                for index, person in enumerate(targets):
                    if person['type'] == 'face':
                        return index
                return i # If no face is found, return the person
                 
            elif target["type"] == 'face' and  type == 'person':
                return i # Because a face part of a person
            
            if target["type"] == type:
                return i
    return None
    