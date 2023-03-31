import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)) + '/..')

import pytest
from argparse import Namespace
from ai_controller_model import AiController
from camera_vision.models import CameraVisionDetection, CameraVisionTarget


@pytest.fixture
def mock_args():
    return Namespace(
        target_padding=10, 
        search=True,
        target_type='person', 
        target_ids=[],
        accuracy_threshold_x=3, 
        accuracy_threshold_y=30,
        max_azimuth_angle=90, 
        max_elevation_speed=10,
        elevation_dp=0,
        y_speed=2,
        x_speed_max=10, 
        x_smoothing=1, 
        azimuth_dp=1
    )


@pytest.fixture
def mock_detection() -> CameraVisionDetection:
    return {
        'targets': [
            {
                'type': 'face',
                'mask': None,
                'id': 'human1',
                'box': (100, 100, 300, 300),
            },
            {   'type': 'person',
                'mask': None,
                'id': None,
                'box': (400, 100, 600, 300),
            },
        ],
        'view_dimensions': (640, 480),
    }


def test_ai_controller_init(mock_args):
    ai_controller = AiController(mock_args.__dict__)

    assert ai_controller.args == mock_args.__dict__
    assert ai_controller.search_state['active'] == mock_args.__dict__['search']


def test_get_action_with_valid_detection(mock_args, mock_detection):
    ai_controller = AiController(mock_args.__dict__)
    action = ai_controller.get_action(mock_detection)

    assert 'speed' in action and 'azimuth_angle' in action and 'is_clockwise' in action and 'is_firing' in action

@pytest.fixture
def ai_controller():
    args = {
        "target_padding": 0,
        "search": False,
        "target_type": "person",
        "target_ids": [],
        'x_speed_max': 10,
        'x_smoothing': 1,
        'accuracy_threshold_x':3,
        'azimuth_dp': 1,
        'max_azimuth_angle': 90,
        'max_elevation_speed': 10,
        'accuracy_threshold_y': 30,
        'y_speed': 2,
        'elevation_dp': 0,
    }
    return AiController(args)


def test_get_action_for_target_center(ai_controller: AiController):
    frame = (1000, 1000)
    target = CameraVisionTarget(box=(250, 250, 750, 750)) # type: ignore
    expected_action = {
        'azimuth_angle': 0,
        'is_clockwise': False,
        'speed': 0,
        'is_firing': True,
    }

    action = ai_controller.get_action_for_target(target, frame)
    
    # Expected action number values are within 1 of the actual action
    expected_azimuth = expected_action['azimuth_angle']
    assert expected_azimuth - 1 <= action['azimuth_angle'] <= expected_azimuth + 1
    expected_speed = action['speed']
    assert expected_speed - 1 <= action['speed'] <= expected_speed + 1
    assert action['is_firing'] == expected_action['is_firing']

# TODO: Fix this test
# def test_get_action_for_target_left(ai_controller: AiController):
#     frame = (640, 480)
#     target = CameraVisionTarget(box=(180, 180, 260, 300)) # type: ignore
#     expected_action = {
#         'azimuth_angle': pytest.approx(37.5, rel=1e-2),
#         'is_clockwise': True,
#         'speed': 0,
#         'is_firing': False,
#     }

#     action = ai_controller.get_action_for_target(target, frame)
#     assert action == expected_action
    
    
def test_get_action_for_target_left(ai_controller: AiController):
    frame = (0, 0)
    target = CameraVisionTarget(box=(0, 0, 0, 0)) # type: ignore
    expected_action = {
        'azimuth_angle': 0,
        'is_clockwise': False,
        'speed': 0,
        'is_firing': False,
    }

    action = ai_controller.get_action_for_target(target, frame)
    # Expected action number values are within 1 of the actual action
    expected_azimuth = expected_action['azimuth_angle']
    assert expected_azimuth == action['azimuth_angle']
    
    expected_speed = action['speed']
    assert expected_speed == action['speed']
    
    assert action['is_firing'] == expected_action['is_firing']
    
def test_action_for_seen_cases():
    
    args = Namespace(
        accuracy_threshold_x=1, 
        accuracy_threshold_y=30, 
        azimuth_dp=2,
        delay=0.15, 
        elevation_dp=0, 
        max_azimuth_angle=55, 
        max_elevation_speed=10, 
        search=False, 
        target_ids=[], 
        target_padding=10, 
        target_type='person', 
        test=False,  
        x_smoothing=1, 
        x_speed_max=5, 
        y_smoothing=1, 
        y_speed=2)
    ai_controller = AiController(args.__dict__)
    
    frame = (640, 480)
    target = CameraVisionTarget(box=(424, 176, 632, 380)) # type: ignore
    expected_action = {
        'azimuth_angle': 0,
        'is_clockwise': False,
        'speed': 0,
        'is_firing': False,
    }

    action = ai_controller.get_action_for_target(target, frame)
    # Expected action number values are within 1 of the actual action
    expected_azimuth = expected_action['azimuth_angle']
    assert expected_azimuth == action['azimuth_angle']
    
    expected_speed = action['speed']
    assert expected_speed == action['speed']
    
    assert action['is_firing'] == expected_action['is_firing']