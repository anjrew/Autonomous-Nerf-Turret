import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)) + '/..')

import pytest
from argparse import Namespace
from ai_controller_model import AiController
from camera_vision.models import CameraVisionDetection


@pytest.fixture
def mock_args():
    return Namespace(
        target_padding=10, 
        search=True,
        target_type='person', 
        # targets=[], 
        target_ids=[],
        accuracy_threshold_x=3, 
        accuracy_threshold_y=30,
        max_azimuth_angle=90, 
        max_elevation_speed=10,
        elevation_dp=0,
        y_speed=2,
        x_speed=10, 
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
    ai_controller = AiController(mock_args)

    assert ai_controller.args == mock_args
    assert ai_controller.search_state['active'] == mock_args.search


def test_get_action_with_valid_detection(mock_args, mock_detection):
    ai_controller = AiController(mock_args)
    action = ai_controller.get_action(mock_detection)

    assert 'speed' in action and 'azimuth_angle' in action and 'is_clockwise' in action and 'is_firing' in action

