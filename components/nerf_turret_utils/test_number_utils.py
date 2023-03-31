import pytest
from argparse import ArgumentTypeError
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + '/..')
from nerf_turret_utils.number_utils import map_range, assert_in_int_range



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

    # Test case where min_input and max_input are equal so raise error
    with pytest.raises(ZeroDivisionError):
        map_range(50, 0, 0, 0, 1)

    # Test case where min_output and max_output are equal
    assert map_range(50, 0, 100, 0, 0) == 0

    # Test case where input_value is smaller than min_input
    assert map_range(-5, 0, 100, 0, 1) == pytest.approx(-0.05, 1e-5)

    # Test case where input_value is larger than max_input
    assert map_range(105, 0, 100, 0, 1) == pytest.approx(1.05, 1e-5)


    

def test_zero_position():
    assert map_range(0, -1, 1, -10, 10) == 0
    