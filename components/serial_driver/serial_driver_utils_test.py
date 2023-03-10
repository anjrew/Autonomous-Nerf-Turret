import pytest

from serial_driver_utils import encode, decode, map_range

@pytest.mark.parametrize("azimuth, is_clockwise,speed, is_firing, expected_output", [
    (90, True, 5, False, {'azimuth': 90, 'is_clockwise': True, 'speed': 5, 'is_firing': False}),
    (0, False, 10, True, {'azimuth': -90, 'is_clockwise': False, 'speed': 10, 'is_firing': True}),
    (180, True, 0, True, {'azimuth': 90, 'is_clockwise': True, 'speed': 0, 'is_firing': True}),
    # Add more test cases here
])
def test_encode_decode_compatibility(azimuth, is_clockwise, speed, is_firing, expected_output):
    azimuth = 90
    is_clockwise = True
    speed = 5
    is_firing = False

    encoded_command = encode(azimuth, is_clockwise, speed, is_firing)
    decoded_command = decode(encoded_command)

    assert decoded_command['azimuth'] == azimuth, "Azimuth should be 90"
    assert decoded_command['is_clockwise'] == is_clockwise, "is_clockwise should be True"
    assert decoded_command['speed'] == speed,   "Speed should be 5"
    assert decoded_command['is_firing'] == is_firing, "is_firing should be False"



def test_map_range():
    # Test case 1: Map a value in the middle of the input range to the middle of the output range
    input_value = 50
    min_value = 0
    max_value = 100
    new_min_value = 0
    new_max_value = 10
    expected_output = 5

    assert map_range(input_value, min_value, max_value, new_min_value, new_max_value) == expected_output

    # Test case 2: Map a value at the low end of the input range to the low end of the output range
    input_value = 0
    min_value = 0
    max_value = 100
    new_min_value = 0
    new_max_value = 10
    expected_output = 0

    assert map_range(input_value, min_value, max_value, new_min_value, new_max_value) == expected_output

    # Test case 3: Map a value at the high end of the input range to the high end of the output range
    input_value = 100
    min_value = 0
    max_value = 100
    new_min_value = 0
    new_max_value = 10
    expected_output = 10

    assert map_range(input_value, min_value, max_value, new_min_value, new_max_value) == expected_output

    input_value = 0
    min_value = -90
    max_value = 90
    new_min_value = 0
    new_max_value = 180
    expected_output = 90

    assert map_range(input_value, min_value, max_value, new_min_value, new_max_value) == expected_output
    
    
    input_value = 90
    min_value = -90
    max_value = 90
    new_min_value = 0
    new_max_value = 180
    expected_output = 180

    assert map_range(input_value, min_value, max_value, new_min_value, new_max_value) == expected_output
    
    input_value = -90
    min_value = -90
    max_value = 90
    new_min_value = 0
    new_max_value = 180
    expected_output = 0

    assert map_range(input_value, min_value, max_value, new_min_value, new_max_value) == expected_output
    
    input_value = 1000
    min_value = 1000
    max_value = 0
    new_min_value = 0
    new_max_value = 10
    expected_output = 0

    assert map_range(input_value, min_value, max_value, new_min_value, new_max_value) == expected_output
    
    input_value = 0
    min_value = 1000
    max_value = 0
    new_min_value = 0
    new_max_value = 10
    expected_output = 10

    assert map_range(input_value, min_value, max_value, new_min_value, new_max_value) == expected_output