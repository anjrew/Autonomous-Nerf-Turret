import logging
import argparse
from typing import Union

# Define the conversion function
def map_log_level(level_str) -> int:
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
    
# def limit_value(value: Union[int,float], minimum=-90, maximum=90):
def limit_value(value: Union[int,float], minimum:Union[int,float], maximum: Union[int,float]) -> Union[int,float]:
    """Limits the value to the min and max values"""
    if value < minimum:
        return minimum
    elif value > maximum:
        return maximum
    else:
        return value
    


# def map_range(value=0, min_value=SLOWEST_HALF_STEP_MICROSECONDS, max_value=FASTEST_HALF_STEP_MICROSECONDS, new_min_value=SLOWEST_SPEED, new_max_value=FASTEST_SPEED):
def map_range(
    value:Union[int,float], 
    value_min: Union[int,float], 
    value_max:Union[int,float], 
    new_min_value: Union[int,float], 
    new_max_value: Union[int,float]
) -> Union[int,float]:
    """Converts a value from on range to another

    Args:
        value (int, optional): Value to convert to the base range. Defaults to 0.
        min_value (int, optional): The slowest range of the stepper motor step. Defaults to SLOWEST_HALF_STEP_MICROSECONDS.
        max_value (int, optional): The fastest range of the stepper motor step. Defaults to FASTEST_HALF_STEP_MICROSECONDS.
        new_min_value (int, optional): The min value to be input here that is human comprehendible. Defaults to 0.
        new_max_value (int, optional): The max value to be input here that is human comprehendible. Defaults to 10.

    Returns:
        int: The value of the half step time in micro seconds to be sent to the stepper motor controller
    """    
    original_range = value_max - value_min
    new_range = new_max_value - new_min_value   
    scaling_factor = original_range / new_range
    place_in_original_range = value - value_min
    scaled = place_in_original_range / scaling_factor
    mapped_value = scaled

    return round(mapped_value)


def encode(azimuth: int, is_clockwise: bool = True, speed: int = 0, is_firing: bool = False) -> bytes:
    """
    Encodes a motor command as two bytes.

    Parameters:
        azimuth (int): The azimuth of the motor, from 0 to 180.
        is_clockwise (bool): Whether the motor should turn clockwise (True) or counterclockwise (False).
            Default is True.
        speed (int): The speed of the motor, from 0 (off) to 10 (maximum speed).
            Default is 0.
        is_firing (bool): Whether the motor should be fired (True) or not (False).
            Default is False.

    Returns:
        bytes: Two bytes representing the encoded motor command.

    Example:
        >>> encode(90, True, 5)
        b'\x5f\x08'
    """
    assert type(speed) == int, "Speed must be an integer"
    assert type(azimuth) == int, "azimuth must be an integer"
    assert type(is_clockwise) == bool, "is_clockwise must be an bool"
    assert type(is_firing) == bool, "is_firing must be an is_firing"
    
    azimuth_degrees = limit_value(azimuth, -90, 90) + 90  # Convert the input angle to a range of 0-180 degrees
    azimuth_byte = round((azimuth_degrees / 180.0) * 255.0)  # Scale the azimuth value to fit in a byte (0-255)
    encoded_value = 0
    if is_clockwise:
        encoded_value |= (1 << 7)  # Set the 8th bit to 1 for clockwise
        is_clockwise = bool(encoded_value & 0x80)
        
        
    encoded_value |= (round(speed) & 0x0F)  # Mask the lower 4 bits for speed (0-10)
   
    if is_firing:
        encoded_value |= (1 << 2)  # Set the 3rd bit to 1 for is_firing
    return bytes([encoded_value, azimuth_byte])


def decode(encoded_motor_command: bytes) -> dict:
    """
    Decodes a two-byte motor command and returns its values as a dictionary.

    Parameters:
        encoded_motor_command (bytes): Two bytes representing the encoded motor command.

    Returns:
        dict: A dictionary containing the decoded values of the motor command.

    Example:
        >>> decode(b'\x5f\x08')
        {'azimuth': 90, 'is_clockwise': True, 'speed': 5, 'is_firing': False}
    """
    assert len(encoded_motor_command) == 2, "Encoded motor command must be two bytes long"
    
    encoded_value, azimuth_byte = encoded_motor_command
    
    is_clockwise = bool(encoded_value & 0x80)  # Check the 8th bit for clockwise
    speed = encoded_value & 0x0F  # Mask the lower 4 bits for speed (0-10)
    is_firing = bool(encoded_value & 0b00000100) >> 2  # Check the 3rd bit for is_firing
    
    azimuth_degrees = round((azimuth_byte / 255.0) * 180.0) - 90  # Scale the azimuth value back to its original range (-90 to 90)
    
    return {'azimuth': azimuth_degrees, 'is_clockwise': is_clockwise, 'speed': speed, 'is_firing': is_firing}
