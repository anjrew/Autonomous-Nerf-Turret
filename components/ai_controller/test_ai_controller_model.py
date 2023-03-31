import os
import sys

directory = os.path.dirname(os.path.abspath(__file__))
sys.path.append(directory)
sys.path.append(directory + '/..')
sys.path.append(directory + '/../..')

import pytest
from argparse import Namespace
from ai_controller_model import AiController
from nerf_turret_utils.controller_action import ControllerAction
from camera_vision.models import CameraVisionDetection, CameraVisionTarget


@pytest.fixture
def mock_args():
    return Namespace(
        target_padding=10, 
        search=True,
        target_type='person', 
        target_ids=[],
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

    assert ai_controller.search_state.is_active== mock_args.__dict__['search']


def test_get_action_with_valid_detection(mock_args, mock_detection):
    ai_controller = AiController(mock_args.__dict__)
    action = ai_controller.get_action(mock_detection)
    assert hasattr(action, 'x') and hasattr(action, 'y') and hasattr(action ,'is_firing')


def test_get_action_for_target_center(mock_args, ):
    ai_controller = AiController(mock_args.__dict__)
    frame = (1000, 1000)
    target = CameraVisionTarget(box=(250, 250, 750, 750)) # type: ignore
    expected_action = ControllerAction(
        x=0,
        y=0,
        is_firing=True,
    )

    action = ai_controller.get_action_for_target(target, frame)
    
    # Expected action number values are within 1 of the actual action
    expected_azimuth = expected_action.x
    assert expected_azimuth == action.x
    expected_speed = action.y
    assert expected_speed == action.y
    assert action.is_firing == expected_action.is_firing

    
