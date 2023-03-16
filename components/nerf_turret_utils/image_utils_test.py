import numpy as np

from image_utils import get_frame_box_vec_delta, get_frame_box_dimensions_delta

def test_get_vec_delta():
    # Create a dummy frame
    frame = np.zeros((480, 640, 3), dtype=np.uint8)

    # Bounding box coordinates
    left, right, top, bottom = 100, 200, 50, 150

    # Expected movement vector
    expected_vector = (170, 140)

    # Test the function
    result_vector = get_frame_box_vec_delta(frame, left, top, right, bottom)
    assert result_vector == expected_vector, f"Expected {expected_vector}, but got {result_vector}"


def test_get_frame_box_dimensions_delta():
    # Bounding box coordinates
    left, right, top, bottom = 100, 200, 50, 150

    # Frame dimensions
    frame_width, frame_height = 640, 480

    # Expected movement vector
    expected_vector = (170, 140)

    # Test the function
    result_vector = get_frame_box_dimensions_delta(left, top, right, bottom, frame_width, frame_height)
    assert result_vector == expected_vector, f"Expected {expected_vector}, but got {result_vector}"
