import pytest
from argparse import ArgumentTypeError
import logging
from ai_controller_utils import assert_in_int_range, map_log_level

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
        map_log_level(123) # type: ignore
