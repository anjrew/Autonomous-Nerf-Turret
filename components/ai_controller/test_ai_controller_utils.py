import os
import sys
import pytest

sys.path.append(os.path.dirname(os.path.abspath(__file__)) + '/..')

from ai_controller_utils import slow_start_fast_end_smoothing, get_azimuth_angle




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


@pytest.fixture
def args():
    return {
        'max_azimuth_angle': 90,
        'x_speed_max': 10,
        'x_smoothing': 0.5,
        'azimuth_dp': 2
    }

def test_azimuth_angle_no_input_range(args):
    result = get_azimuth_angle(args, 0, (0, 0))
    assert result == 0

def test_azimuth_angle_speed_adjustment(args):
    result = get_azimuth_angle(args, 100, (80, 0))
    assert result == 10
