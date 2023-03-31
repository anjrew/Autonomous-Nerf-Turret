import logging
import argparse
from typing import Tuple, Union

import os
import sys

directory = os.path.dirname(os.path.abspath(__file__))
sys.path.append(directory + '/..')
from nerf_turret_utils.turret_controller import TurretAction
from nerf_turret_utils.controller_action import ControllerAction
from nerf_turret_utils.constants import CONTROLLER_X_OUTPUT_RANGE, CONTROLLER_Y_OUTPUT_RANGE


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


def encode(azimuth: int, is_clockwise: bool, speed: int, is_firing: bool) -> bytes:
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
    
    azimuth_byte = encode_azimuth_val_to_byte(azimuth)  # Scale the azimuth value to fit in a byte (0-255)
    encoded_value = encode_vals_to_byte(is_clockwise, speed, is_firing)  # Encode the other values into a single byte
    return bytes([azimuth_byte, encoded_value ])


def encode_vals_to_byte(is_clockwise: bool, speed: int, is_firing: bool):
    """
    Encodes motor command values as a single byte.

    This function takes in three values that define a motor command: a boolean value
    indicating whether the motor should turn clockwise (`is_clockwise`), an integer
    value representing the speed of the motor (`speed`), and a boolean value indicating
    whether the motor should be fired (`is_firing`). These values are encoded into a
    single byte using bitwise operations, and the resulting byte is returned.

    Parameters:
        is_clockwise (bool): Whether the motor should turn clockwise (True) or counterclockwise (False).
        speed (int): The speed of the motor, from 0 (off) to 10 (maximum speed).
        is_firing (bool): Whether the motor should be fired (True) or not (False).

    Returns:
        int: A single byte representing the encoded motor command.

    Example:
        >>> encode_vals_to_byte(True, 5, False)
        160
    """
    encoded_value = 0b00000000
    if is_clockwise:
        encoded_value |= (1 << 7)  # Set the 8th bit to 1 for clockwise
        
    if is_firing:
        encoded_value |= (1 << 6)  # Set the 7th bit to 1 for is_firing
        
    encoded_value |= (speed & 0b00001111)  # Mask the lower 1-4(4) bits for speed (0-10)
   
    return encoded_value


def decode_byte_to_motor_vals(encoded_value: int):
    """
    Decodes a byte value to motor values in Python.

    Args:
        encoded_value (int): An integer representing the byte value to decode.

    Returns:
        dict: A dictionary with the decoded motor values, including keys for 'is_clockwise', 'speed', and 'is_firing'.

    Example:
        >>> decode_byte_to_motor_vals(0b10101000)
        {'is_clockwise': True, 'speed': 8, 'is_firing': False}
    """
    is_clockwise = bool((encoded_value & 0b10000000) >> 7)  # Check the 8th bit for clockwise
    is_firing = bool((encoded_value & 0b01000000) >> 6)  # Check the 7th bit for is_firing
    speed = (encoded_value & 0b00001111) # Mask the lower 4 bits for speed (0-10)
    
    return { 'is_clockwise': is_clockwise, 'speed': speed, 'is_firing': is_firing }


def encode_azimuth_val_to_byte(azimuth: int) -> int:
    """
    Encodes an azimuth value as a single byte.

    The input azimuth value is first converted to a range of 0-180 degrees using the
    `limit_value()` function. The resulting angle is then scaled to fit in a single
    byte (0-255) and rounded to the nearest integer.

    Parameters:
        azimuth (int): The azimuth value to encode, in degrees.

    Returns:
        int: A single byte representing the encoded azimuth value.

    Example:
        >>> encode_azimuth_val_to_byte(90)
        143
    """
    # Convert the input angle to a range of 0-180 degrees so it can fit in a byte rather than a signed value
    azimuth_degrees = round(limit_value(azimuth, -90, 90) + 90) 
    return azimuth_degrees


def decode_byte_to_azimuth(byte: int) -> int: 
    """
    Decodes a byte value to an azimuth in Python.

    Args:
        byte (int): An integer representing the byte value to decode.

    Returns:
        int: The azimuth value encoded in the lower 4 bits of the byte.

    Example:
        >>> decode_byte_to_azimuth(0b01010100)
        4
    """
    return (byte & 0b11111111) - 90  # Mask the lower 4 bits for azimuth (0-180)

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
    
    azimuth_byte, encoded_value = encoded_motor_command
    
    decoded_motor_vals = decode_byte_to_motor_vals(encoded_value)
    
    
    return { 
        'azimuth': decode_byte_to_azimuth(azimuth_byte), 
        'is_clockwise': decoded_motor_vals['is_clockwise'], 
        'speed': decoded_motor_vals['speed'], 
        'is_firing': decoded_motor_vals['is_firing'] 
    }

def get_elevation_clockwise(movement_vector: Tuple[float, float]) -> bool:
    """
    Determines whether the Nerf turret elevation stepper motor should rotate clockwise based on its movement vector.

    Args:
        movement_vector (Tuple[float, float]): A tuple containing the movement vector of the turret,
            where the first element is the horizontal movement and the second element is the vertical movement.

    Returns:
        bool: True if the turret elevation should rotate clockwise, False otherwise.
    """

    is_clockwise = movement_vector[1] < 0
    return is_clockwise


def map_controller_action_to_turret_action(
        action: ControllerAction, 
        azimuth_speed_range: Tuple[int,int],
        elevation_speed_range: Tuple[int,int]
    ) -> TurretAction:
    return {
        'azimuth_angle': int(map_range(
            action.x,
            CONTROLLER_X_OUTPUT_RANGE[0],
            CONTROLLER_X_OUTPUT_RANGE[1],
            azimuth_speed_range[0],
            azimuth_speed_range[1]
        )),
        'speed': int(map_range(
            action.x,
            CONTROLLER_Y_OUTPUT_RANGE[0],
            CONTROLLER_Y_OUTPUT_RANGE[1],
            elevation_speed_range[0],
            elevation_speed_range[1]
        )),
        'is_firing': action.is_firing,
        'is_clockwise': action.y > 0, 
    }