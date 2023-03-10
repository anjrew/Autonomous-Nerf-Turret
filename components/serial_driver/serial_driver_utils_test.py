import pytest

from serial_driver_utils \
    import encode,\
        encode_vals_to_byte,\
        encode_azimuth_val_to_byte,\
        decode, \
        map_range, \
        decode_byte_to_motor_vals, \
        decode_byte_to_azimuth


def assign_id_to_tests(tests: list):
    """
    Assigns a unique id to each test in the test suite.
    """
    return [ (f"TEST: {i + 1}", *test ) for i, test in enumerate(tests)]
        
        
# ================= ENCODING TESTS =================
        

@pytest.mark.parametrize("id, azimuth, expected_output", assign_id_to_tests([
    ## These are the args in order passed to the test function with the expected values in the object
    ( -90 , 0b00000000 ),
    ( 90 ,  0b10110100 ),
    ( 0 ,   0b01011010 ),

]))
def test_encode_azimuth_to_binary(id: int, azimuth:int, expected_output:int):
    encoded_command = encode_azimuth_val_to_byte(azimuth)
    
    # encoded, azimuth_byte
    assert encoded_command == expected_output, f"({id}) Encoding Failed: Expected {bin(expected_output)} but got {bin(encoded_command)}"


@pytest.mark.parametrize("id, is_clockwise, speed, is_firing, expected_output", assign_id_to_tests([
    ## These are the args in order passed to the test function with the expected values in the object
    (True, 0, False,  0b10000000),
    (False, 0, False, 0b00000000), 
    (False, 0, True,  0b01000000), 
    (True, 0, True,   0b11000000),
    (True, 1, True,   0b11000001),
    (True, 1, False,  0b10000001),
    (False, 1, False, 0b00000001),
    (False, 2, False, 0b00000010),
    (False, 3, False, 0b00000011),
    (False, 4, False, 0b00000100),
    (True, 4, False,  0b10000100),
    (True, 4, True,   0b11000100),
    (False, 4, True,  0b01000100),
    (False, 5, True,  0b01000101),
    (False, 6, True,  0b01000110),
    (False, 7, True,  0b01000111),
    (False, 8, True,  0b01001000),
    (False, 9, True,  0b01001001),
    (False, 10, True, 0b01001010),
    (False, 7, True,  0b01000111),
]))
def test_encode_vals_to_binary(is_clockwise: bool, speed: int, is_firing: bool, expected_output:int, id:int):
    encoded_command = encode_vals_to_byte(is_clockwise, speed, is_firing)
    # encoded, azimuth_byte
    assert encoded_command == expected_output, f"({id}) Encoding Failed: Expected {bin(expected_output)} but got {bin(encoded_command)}"



@pytest.mark.parametrize("id, azimuth, is_clockwise, speed, is_firing, expected_output", assign_id_to_tests([
    ## These are the args in order passed to the test function with the expected values in the object
    (0, True, 0, False,     [0b10000000, 0b01011010]),
    (90, True, 0, False,    [0b10000000, 0b10110100]),
    (90, False, 7, True,    [0b01000111, 0b10110100]),
]))
def test_encode_all_to_binary(azimuth, is_clockwise, speed, is_firing, expected_output, id):
    encoded_command = encode(azimuth, is_clockwise, speed, is_firing)
    
    # encoded, azimuth_byte
    assert encoded_command[0] == expected_output[0], f"({id}) Encoded Failed: Expected {bin(expected_output[0])} but got {bin(encoded_command[0])}"
    assert encoded_command[1] == expected_output[1], f"({id}) Azimuth_byte Failed: Expected {bin(expected_output[1])} but got {bin(encoded_command[1])}"


# ================= DECODING TESTS =================


@pytest.mark.parametrize("id, byte, expected_output", assign_id_to_tests([
    ## These are the args in order passed to the test function with the expected values in the object
    (0b10000000,     { 'is_clockwise': True, 'speed': 0, 'is_firing': False}),
    (0b11000001,     { 'is_clockwise': True, 'speed': 1, 'is_firing': True}),
    (0b01001000,     { 'is_clockwise': False, 'speed': 8, 'is_firing': True}),
    (0b00000011,     { 'is_clockwise': False, 'speed': 3, 'is_firing': False}),
   
]))
def test_decode_byte_to_motor_vals(id:int, byte: int, expected_output:dict):
    decoded_command = decode_byte_to_motor_vals(byte)
    
    is_clockwise_result = decoded_command['is_clockwise']
    speed_result = decoded_command['speed']
    is_firing_result = decoded_command['is_firing']
    # encoded, azimuth_byte
    assert is_clockwise_result == expected_output['is_clockwise'], f"{id}: is_clockwise should be {expected_output['is_clockwise']} but was {is_clockwise_result}"
    assert speed_result == expected_output['speed'], f"{id}: Speed should be {expected_output['speed']} but was {speed_result}"
    assert is_firing_result == expected_output['is_firing'], f"{id}: is_firing should be {expected_output['is_firing']} but was {is_firing_result}"


@pytest.mark.parametrize("id, byte, expected_output", assign_id_to_tests([
    ## These are the args in order passed to the test function with the expected values in the object
     ## These are the args in order passed to the test function with the expected values in the object
    (0b00000000, -90 ),
    (0b10110100, 90 ),
    (0b01011010, 0 ),
   
]))
def test_decode_byte_to_azimuth(id:int, byte: int, expected_output:dict):
    decoded_val = decode_byte_to_azimuth(byte)

    # encoded, azimuth_byte
    assert decoded_val == expected_output, f"{id}: Decoded should be {expected_output} but was {decoded_val}"
   

@pytest.mark.parametrize("id, azimuth, is_clockwise,speed, is_firing, expected_output",  assign_id_to_tests([
    ## These are the args in order passed to the test function with the expected values in the object
    (90, True, 5, False, {'azimuth': 90, 'is_clockwise': True, 'speed': 5, 'is_firing': False}),
    (0, False, 10, True, {'azimuth': 0, 'is_clockwise': False, 'speed': 10, 'is_firing': True}),
    (90, True, 0, True, {'azimuth': 90, 'is_clockwise': True, 'speed': 0, 'is_firing': True}),
    # Add more test cases here
]))
def test_encode_decode_compatibility(azimuth, is_clockwise, speed, is_firing, expected_output, id):
    encoded_command = encode(azimuth, is_clockwise, speed, is_firing)
    decoded_command = decode(encoded_command)
    azimuth_result = decoded_command['azimuth']
    is_clockwise_result = decoded_command['is_clockwise']
    speed_result = decoded_command['speed']
    is_firing_result = decoded_command['is_firing']
    
    assert azimuth_result == expected_output['azimuth'], f"{id}: Azimuth should be {expected_output['azimuth']} but was {azimuth_result}"
    assert is_clockwise_result == expected_output['is_clockwise'], f"is_clockwise should be {expected_output['is_clockwise']} but was {is_clockwise_result}"
    assert speed_result == expected_output['speed'], f"{id}: Speed should be {expected_output['speed']} but was {speed_result}"
    assert is_firing_result == expected_output['is_firing'], f"{id}: is_firing should be {expected_output['is_firing']} but was {is_firing_result}"




# ================= RANGE TESTS =================


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