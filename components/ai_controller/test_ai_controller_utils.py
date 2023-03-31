import os
import sys
import pytest

directory = os.path.dirname(os.path.abspath(__file__))
sys.path.append(directory + '/..')
sys.path.append(directory + '/..')

from ai_controller_utils import get_x_speed, get_y_speed


def test_azimuth_angle_no_input_range():
    result = get_x_speed( 0, (0, 0))
    assert result == 0

def test_azimuth_angle_speed_adjustment_negative():
    result = get_x_speed(100, (-50, 0))
    assert result == -10
    result = get_x_speed(100, (-40, 0))
    assert result == -8
    result = get_x_speed(100, (-10, 0))
    assert result == -2

def test_azimuth_angle_speed_adjustment_positive():
    result = get_x_speed(100, (50, 0))
    assert result == 10
    result = get_x_speed(100, (40, 0))
    assert result == 8
    result = get_x_speed(100, (10, 0))
    assert result == 2


def test_elevation_angle_no_input_range():
    result = get_y_speed( 0, (0, 0), (1, 1, 1, 1))
    assert result == 0

def test_elevation_angle_speed_adjustment_negative():
    result = get_y_speed(100, (0, -50), (1, 1, 1, 1))
    assert result == -10
    result = get_y_speed(100, (0, -40), (1, 1, 1, 1))
    assert result == -8
    result = get_y_speed(100, (0, -10), (1, 1, 1, 1))
    assert result == -2

def test_elevation_angle_speed_adjustment_positive():
    result = get_y_speed(100, (0, 50), (1, 1, 1, 1))
    assert result == 10
    result = get_y_speed(100, (0, 40), (1, 1, 1, 1))
    assert result == 8
    result = get_y_speed(100, (0, 10), (1, 1, 1, 1))
    assert result == 2


def test_target_on_top_edge():
    result = get_y_speed(100, (0, 0), (1, 0, 1, 1))
    assert result == 1
    
def test_target_on_bottom_edge():
    result = get_y_speed(100, (0, 0), (1, 1, 1, 0))
    assert result == -1
