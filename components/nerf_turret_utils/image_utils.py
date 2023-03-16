from typing import Tuple
import numpy as np

def get_frame_box_vec_delta(frame: np.ndarray, left: int,  top: int, right:  int, bottom ) -> Tuple:
     """
     Calculate the vector from the center of a bounding box to the center of a given frame.

     Args:
          frame: The input image frame.
          left: The left coordinate of the bounding box.
          top: The top coordinate of the bounding box.
          right: The right coordinate of the bounding box.
          bottom: The bottom coordinate of the bounding box.

     Returns:
          A tuple containing the x and y components of the movement vector from the bounding box center
                              to the frame center.
     """
     
    # Calculate the center of the image
     frame_height, frame_width = frame.shape[:2]
     
          # Get the image dimensions
     return get_frame_box_dimensions_delta(left, top, right, bottom, frame_width, frame_height)


def get_frame_box_dimensions_delta(left: int,  top: int, right:  int, bottom, frame_width: int, frame_height: int) -> Tuple:
     """
     Calculate the vector from the center of a bounding box to the center of a frame with given dimensions.

     Args:
          left: The left coordinate of the bounding box.
          top: The top coordinate of the bounding box.
          right: The right coordinate of the bounding box.
          bottom: The bottom coordinate of the bounding box.
          frame_width: The width of the frame.
          frame_height: The height of the frame.

     Returns:
          A tuple containing the x and y components of the movement vector from the bounding box center
                              to the frame center.
     """
     frame_center_x, frame_center_y = frame_width // 2, frame_height // 2
     box_center_x = (left + right) // 2
     box_center_y = (top + bottom) // 2
     movement_vector =(frame_center_x - box_center_x, frame_center_y - box_center_y)
     return movement_vector