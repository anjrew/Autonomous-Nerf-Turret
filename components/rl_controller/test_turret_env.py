import os
import sys
import numpy as np


sys.path.append(os.path.dirname(os.path.abspath(__file__)) + '/..')
from nerf_turret_utils.controller_action import ControllerAction

import pytest
from typing import Callable
from rl_controller.models import TurretObservationSpace
from turret_env import TurretEnv
import logging

logger = logging.getLogger(__name__)


# A simple target provider function for testing
def dummy_target_provider(target = { 'box': (0, 0, 0, 0), 'view_dimensions': (100, 100)}) -> Callable[[], TurretObservationSpace]:
    def target_producer() -> TurretObservationSpace:
        return target
    return target_producer

# A dummy action dispatcher for testing
def dummy_action_dispatcher(_: ControllerAction) -> None:
    return None

def test_turret_environment_init():
    provider = dummy_target_provider()
    env = TurretEnv(provider, dummy_action_dispatcher)
    assert env.target_provider != provider # Should be a mapped version of the provider so not the exact same
    assert env.state == env.INITIAL_STATE
    assert env.step_n == 0


def test_turret_environment_step_no_target():
    env = TurretEnv(dummy_target_provider(), dummy_action_dispatcher)
    test_action: np.ndarray = np.array((0, 0, 0))
    state, reward, done, info = env.step(test_action)
    assert reward == 1 # Get base reward for doing nothing wrong
    assert done == False
    assert info['step'] == 1

def test_turret_environment_step_right_on_target_and_firing():
    env = TurretEnv(dummy_target_provider({ 'box': (25, 25, 75, 75,), 'view_dimensions': (100, 100)}), dummy_action_dispatcher)
    test_action: np.ndarray = np.array((1, 0, 1))
    state, reward, done, info = env.step(test_action)
    assert reward == 2 # because firing
    assert done == False
    assert info['step'] == 1

def test_turret_environment_reset():
    env = TurretEnv(dummy_target_provider(), dummy_action_dispatcher)
    env.step_n = 5
  
    env.reset()
    assert env.step_n == 0


def test_get_accuracy_reward():
    env = TurretEnv(dummy_target_provider(), dummy_action_dispatcher)

    # Test when frame center and box center are the same
    reward = env.get_accuracy_reward(100, 100, 50, 50, 50, 50)
    assert reward == 0.5

    # Test when frame center and box center have the maximum possible distance
    reward = env.get_accuracy_reward(100, 100, 50, 50, 0, 0)
    assert reward == pytest.approx(0, abs=1e-4)

    # Test when frame center and box center are closer
    reward = env.get_accuracy_reward(100, 100, 50, 50, 60, 60)
    assert reward == pytest.approx(0.4, abs=1e-4)


# Test calc reward
def test_calc_reward_no_target_no_shooting():
    target = (0, 0, 0, 0, 0, 0)
    env = TurretEnv(dummy_target_provider(target), dummy_action_dispatcher)
    action=ControllerAction(
        x=10,
        y=0,
        is_firing=False,
    )
    reward = env.calc_reward(target, action)
    assert reward == 1 # No target, no shooting should be base reward

def test_calc_reward_no_target_with_shooting():
    target = (0, 0, 0, 0, 0, 0)
    env = TurretEnv(dummy_target_provider(target), dummy_action_dispatcher)
    action=ControllerAction(
        x= 10,
        y=0,
        is_firing=True,)

    reward = env.calc_reward(target, action)
    assert reward == 0 # No target, no shooting should be base reward

def test_calc_reward_on_target_shooting():
    # (left, top, right, bottom, height, width)
    target = (10, 10, 20, 20, 30, 30) # Target in the center of the frame
    env = TurretEnv(dummy_target_provider(target), dummy_action_dispatcher)
    action=ControllerAction(
        x= 10,
        y=0,
        is_firing=True,)
    
    is_on_target = env.check_is_on_target(target)
    assert is_on_target == True
    
    # Test when frame center and box center are the same
    left, top, right, bottom, frame_height, frame_width =  target
        
    frame_center_x, frame_center_y = frame_width // 2, frame_height // 2
    box_center_x = (left + right) // 2
    box_center_y = (top + bottom) // 2
    reward = env.get_accuracy_reward(frame_height, frame_width, frame_center_x, frame_center_y, box_center_x, box_center_y)
    assert reward == 0.5
    
    assert env.check_is_on_target(target) and action.is_firing
    
    reward = env.calc_reward(target, action)
    # 1 basic + 0.5 for the accuracy and 0.5 for firing on target = 2
    assert reward == 2

def test_calc_reward_on_target_not_shooting():
    target = (10, 10, 20, 20, 30, 30) # Target in the center of the frame
    env = TurretEnv(dummy_target_provider(target), dummy_action_dispatcher)
    action=ControllerAction(
        x= 10,
        y=0,
        is_firing=False,
    )
    reward = env.calc_reward(target, action)
    assert reward == 1.5

def test_calc_reward_off_target_shooting():
    target = (10, 10, 20, 20, 100, 100) # Target in the center of the frame
    env = TurretEnv(dummy_target_provider(target), dummy_action_dispatcher)
    action=ControllerAction(
        x= 10,
        y=0,
        is_firing=True,
    )
    reward = env.calc_reward(target, action)
    assert reward == 0


# TEST is on target

def test_check_is_on_target_in_center():
    env = TurretEnv(dummy_target_provider(), dummy_action_dispatcher)
    target_state = (10, 10, 20, 20, 30, 30)

    is_on_target = env.check_is_on_target(target_state)
    assert is_on_target == True

def test_check_is_on_target__offset_top_left():
    env = TurretEnv(dummy_target_provider(), dummy_action_dispatcher)
    target_state = (5, 5, 20, 20, 30, 30)

    is_on_target = env.check_is_on_target(target_state)
    assert is_on_target == True

def test_check_is_on_target_border_left():
    env = TurretEnv(dummy_target_provider(), dummy_action_dispatcher)
    target_state = (15, 10, 25, 20, 30, 30)

    is_on_target = env.check_is_on_target(target_state)
    assert is_on_target == True

def test_check_is_on_target_border_top():
    env = TurretEnv(dummy_target_provider(), dummy_action_dispatcher)
    target_state = (10, 5, 20, 15, 30, 30)

    is_on_target = env.check_is_on_target(target_state)
    assert is_on_target == True

def test_check_is_on_target_border_right():
    env = TurretEnv(dummy_target_provider(), dummy_action_dispatcher)
    target_state = (5, 10, 15, 20, 30, 30)

    is_on_target = env.check_is_on_target(target_state)
    assert is_on_target == True

def test_check_is_on_target_border_bottom():
    env = TurretEnv(dummy_target_provider(), dummy_action_dispatcher)
    target_state = (10, 15, 20, 25, 30, 30)

    is_on_target = env.check_is_on_target(target_state)
    assert is_on_target == True


# Test compare centers

def test_compare_centers_true():
    env = TurretEnv(dummy_target_provider(), dummy_action_dispatcher)
    left, top, right, bottom = 10, 10, 20, 20
    center_x, center_y = 15, 15

    result = env.check_center_within_bounds(left, top, right, bottom, center_x, center_y)
    assert result == True

def test_compare_centers_false_outside_top_left():
    env = TurretEnv(dummy_target_provider(), dummy_action_dispatcher)
    left, top, right, bottom = 5, 5, 20, 20
    center_x, center_y = 4, 4

    result = env.check_center_within_bounds(left, top, right, bottom, center_x, center_y)
    assert result == False

def test_compare_centers_false_outside_bottom_right():
    env = TurretEnv(dummy_target_provider(), dummy_action_dispatcher)
    left, top, right, bottom = 10, 10, 25, 25
    center_x, center_y = 26, 26

    result = env.check_center_within_bounds(left, top, right, bottom, center_x, center_y)
    assert result == False



# Test get frame centers

def test_get_center_coords_even_dimensions():
    env = TurretEnv(dummy_target_provider(), dummy_action_dispatcher)
    frame_height, frame_width = 20, 40

    center_x, center_y = env.get_center_coords(frame_height, frame_width)
    assert center_x == 20
    assert center_y == 10

def test_get_center_coords_odd_dimensions():
    env = TurretEnv(dummy_target_provider(), dummy_action_dispatcher)
    frame_height, frame_width = 21, 41

    center_x, center_y = env.get_center_coords(frame_height, frame_width)
    assert center_x == 20
    assert center_y == 10

def test_get_center_coords_zero_dimensions():
    env = TurretEnv(dummy_target_provider(), dummy_action_dispatcher)
    frame_height, frame_width = 0, 0

    center_x, center_y = env.get_center_coords(frame_height, frame_width)
    assert center_x == 0
    assert center_y == 0

def test_get_center_coords_large_dimensions():
    env = TurretEnv(dummy_target_provider(), dummy_action_dispatcher)
    frame_height, frame_width = 1080, 1920

    center_x, center_y = env.get_center_coords(frame_height, frame_width)
    assert center_x == 960
    assert center_y == 540
    
    

def test_map_action_tuple_to_dict():
    env = TurretEnv(dummy_target_provider(), dummy_action_dispatcher)

    # Test case 1: valid input
    action_tuple = np.array((0, 1, 0))
    expected_output = ControllerAction(
        x=-10,
        y=10,
        is_firing=False
    )
    
    result = env.map_action_vector_to_object(action_tuple)
    assert result.__dict__ == expected_output.__dict__, f'{result.__dict__} != {expected_output.__dict__}'

    # Test case 2: invalid input (wrong number of elements)
    # action_tuple = (45, 1, 10)
    # with pytest.raises(ValueError):
    #     env.map_action_vector_to_object(action_tuple) # type: ignore

    # TODO: implement these test cases
    # Test case 3: invalid input (invalid type)
    # action_tuple = (45, 1, "10", 0)
    # with pytest.raises(TypeError):
    #     env.map_action_tuple_to_dict(action_tuple) # type: ignore

    # # Test case 4: invalid input (out of range value)
    # action_tuple = (450, 1, 10, 0)
    # with pytest.raises(ValueError):
    #     env.map_action_tuple_to_dict(action_tuple)
    
    
def test_map_action_object_to_vector():
    env = TurretEnv(dummy_target_provider(), dummy_action_dispatcher)
    
    # Test case 1: all values are valid
    controller_action=ControllerAction(
        x=env.ENV_ACTION_SPACE_RANGE['x'][1],
        y=1,
        is_firing=False)
    expected_output = np.array((1, 0.55, 0))
    result = env.map_action_object_to_vector(controller_action)
    
    assert np.array_equal(result ,expected_output)

    with pytest.raises(AssertionError):
        # Test case 2: is_clockwise and is_firing are strings
        controller_action=ControllerAction(
            x=8,
            y=0,
            is_firing= "False" # type: ignore
        ) # type: ignore
    

    with pytest.raises(TypeError):
        # Test case 3: missing azimuth_angle value
        controller_action=ControllerAction(
            y=100,
            is_firing=True
        ) # type: ignore
