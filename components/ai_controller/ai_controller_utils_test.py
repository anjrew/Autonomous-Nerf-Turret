import pytest
from argparse import ArgumentTypeError
import logging
from ai_controller_utils \
    import assert_in_int_range, map_log_level, is_valid_string_log_level, is_valid_int_log_level, slow_start_fast_end_smoothing, map_range



def test_int_range_valid():
    assert assert_in_int_range(5, 0, 10) == 5

def test_int_range_lower_bound():
    assert assert_in_int_range(0, 0, 10) == 0

def test_int_range_upper_bound():
    assert assert_in_int_range(10, 0, 10) == 10

def test_int_range_below_min():
    with pytest.raises(ArgumentTypeError):
        assert_in_int_range(-1, 0, 10)

def test_int_range_above_max():
    with pytest.raises(ArgumentTypeError):
        assert_in_int_range(11, 0, 10)

def test_int_range_non_integer():
    with pytest.raises(ArgumentTypeError):
        assert_in_int_range('not an integer', 0, 10) # type: ignore


def test_map_log_level_numeric():
    assert map_log_level('10') == 10

def test_map_log_level_valid_string():
    assert map_log_level('debug') == logging.DEBUG

def test_map_log_level_invalid_string():
    with pytest.raises(ArgumentTypeError):
        map_log_level('invalid_level')

def test_map_log_level_invalid_type():
    with pytest.raises(ArgumentTypeError):
        map_log_level('123') # type: ignore



def test_is_valid_log_level_valid():
    assert is_valid_string_log_level('INFO') == True

def test_is_valid_log_level_invalid():
    assert is_valid_string_log_level('not_a_log_level') == False

def test_is_valid_log_level_numeric():
    assert is_valid_string_log_level('10') == False

def test_is_valid_log_level_case_insensitive():
    assert is_valid_string_log_level('debug') == True
    assert is_valid_string_log_level('DEBUG') == True

def test_is_valid_log_level_all_levels():
    for level_name in logging._nameToLevel.keys():
        assert is_valid_string_log_level(level_name) == True
        
        

def test_int_is_valid_log_level_valid():
    assert is_valid_int_log_level(logging.DEBUG) == True

def test_int_is_valid_log_level_invalid():
    assert is_valid_int_log_level(12345) == False

def test_int_is_valid_log_level_string():
    with pytest.raises(AssertionError):
        is_valid_int_log_level('ERROR') # type: ignore




def test_slow_start_fast_end_smoothing():
    # Test case where x is at the beginning of the range, p=1
    assert slow_start_fast_end_smoothing(0, 1, 10) == 0

    # Test case where x is at the end of the range, p=1
    assert slow_start_fast_end_smoothing(10, 1, 10) == 10
    
    #TODO: Fix this test case
    # Test case where x is in the middle of the range, p=1
    # assert slow_start_fast_end_smoothing(5, 1, 10) == pytest.approx(3.1622776602, 1e-5)

    # Test case where x is at the beginning of the range, p=2
    assert slow_start_fast_end_smoothing(0, 2, 10) == 0

    # Test case where x is at the end of the range, p=2
    assert slow_start_fast_end_smoothing(10, 2, 10) == 10

    #TODO: Fix this test case
    # Test case where x is in the middle of the range, p=2
    # assert slow_start_fast_end_smoothing(5, 2, 10) == pytest.approx(7.0710678119, 1e-5)

    #TODO: Fix this test case
    # Test case where x is negative, p=1
    # assert slow_start_fast_end_smoothing(-5, 1, 10) == -3.1622776602

    # Test case where x is negative, p=2
    # assert slow_start_fast_end_smoothing(-5, 2, 10) == -7.0710678119



def test_map_range():
    # Test case where input_value is in the middle of the input range
    assert map_range(50, 0, 100, 0, 1) == pytest.approx(0.5, 1e-5)

    # Test case where input_value is at the minimum of the input range
    assert map_range(0, 0, 100, 0, 1) == 0

    # Test case where input_value is at the maximum of the input range
    assert map_range(100, 0, 100, 0, 1) == 1

    # Test case where input_value is negative and in the middle of the input range
    assert map_range(-50, -100, 0, 0, 1) == pytest.approx(0.5, 1e-5)

    # Test case where input_value is negative and at the minimum of the input range
    assert map_range(-100, -100, 0, 0, 1) == 0

    # Test case where input_value is negative and at the maximum of the input range
    assert map_range(0, -100, 0, 0, 1) == 1

    # Test case where min_input and max_input are equal
    with pytest.raises(ZeroDivisionError):
        map_range(50, 0, 0, 0, 1)

    # Test case where min_output and max_output are equal
    assert map_range(50, 0, 100, 0, 0) == 0

    # Test case where input_value is smaller than min_input
    assert map_range(-5, 0, 100, 0, 1) == pytest.approx(-0.05, 1e-5)

    # Test case where input_value is larger than max_input
    assert map_range(105, 0, 100, 0, 1) == pytest.approx(1.05, 1e-5)
