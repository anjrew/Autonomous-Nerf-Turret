from typing import Tuple
import numpy as np
import cv2

def draw_object_mask(frame: np.ndarray, target_highlight_color: Tuple[int, int, int], mask: np.ndarray) -> np.ndarray:
    """
    Draws a segmentation mask on an image frame.

    Args:
        frame: A NumPy array representing the image frame.
        target_highlight_color: A NumPy array representing the color to highlight the segmentation mask.
        mask: A NumPy array representing the segmentation mask to be drawn.

    Returns:
        A NumPy array representing the image frame with the segmentation mask drawn on it.
    """
    mask = cv2.resize(mask, (frame.shape[1], frame.shape[0]))
                    # Draw a mask
    if len(mask.shape) == 2:
                        # Create a color mask using the segmented area
        color_mask = np.zeros_like(frame)
        color_mask[mask == 1] = target_highlight_color  # Set the color for the segmented area

                        # Blend the color mask with the original image
        alpha = 0.5  # Adjust the alpha value for the blending
        beta = 1 - alpha
        frame = cv2.addWeighted(frame, alpha, color_mask, beta, 0)
    return frame


def draw_object_box(frame: np.ndarray, left: int, top: int, right: int, bottom: int, box_text: str, target_highlight_color: Tuple[int, int, int]) -> np.ndarray:
    """
    Draws a bounding box around an object in the given frame, with a label and name.

    Args:
        frame: The input image frame as a numpy array.
        left: The left pixel coordinate of the bounding box as an integer.
        top: The top pixel coordinate of the bounding box as an integer.
        right: The right pixel coordinate of the bounding box as an integer.
        bottom: The bottom pixel coordinate of the bounding box as an integer.
        box_text: The text to display as the label for the bounding box.
        target_highlight_color: The color to use for the bounding box as a tuple of three integers (R, G, B).

    Returns:
        The input frame with the bounding box and label drawn.
    """
    # Draw a bounding box
    cv2.rectangle(frame, (int(left), int(top)), (int(right), int(bottom)), target_highlight_color, 2)
    
    # Draw a label with a name below the face
    cv2.rectangle(frame, (left, top - 55), (right, top), target_highlight_color, cv2.FILLED)
    
    font_size = 445
    font = cv2.FONT_HERSHEY_DUPLEX
    cv2.putText(frame, box_text, (left + 6, top - 6), font, (right - left)/font_size, (255, 255, 255) if False else (10, 10, 10), 1)
    
    return frame