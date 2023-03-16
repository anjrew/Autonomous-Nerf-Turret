from typing import Tuple
import numpy as np

def get_vec_delta(frame: np.ndarray, left: int,  top: int, right:  int, bottom ) -> Tuple:
     # Get the image dimensions
    box_center_x = (left + right) // 2
    box_center_y = (top + bottom) // 2
    # Calculate the center of the image
    frame_height, frame_width = frame.shape[:2]
    frame_center_x, frame_center_y = frame_width // 2, frame_height // 2
    movement_vector =(frame_center_x - box_center_x, frame_center_y - box_center_y)
    return movement_vector