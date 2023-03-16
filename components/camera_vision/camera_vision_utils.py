from typing import List, Optional, Tuple
import logging
import cv2
import face_recognition
import math
import numpy as np


def get_face_location_details(image_compression:int, face_location:tuple) -> dict:
    """
    Calculate face location details based on the given image dimensions and face location.
    
    Args:
        image_compression: The compression factor applied to the original image.
        face_location: A list containing the face bounding box coordinates [top, right, bottom, left].

    Returns:
        dict: A dictionary containing the following keys:
            - vec_delta: A list containing the x and y movement vectors of the face bounding box's center relative to the image's center.
            - box: A list containing the adjusted face bounding box coordinates [left, top, right, bottom].
    """
    top, right, bottom, left = face_location
    
    top *= image_compression
    right *= image_compression
    bottom *= image_compression
    left *= image_compression
        
                            
    target = { "box": [left, top, right, bottom], 'type': "face"}
    
    return target



def get_target_id(frame, box:list, target_names: list, target_images: list) -> Optional[str]:
    """
    Identify a target based on the face bounding box coordinates, target names, and target images.

    Args:
        frame: A frame containing the face to be identified.
        box: The bounding box coordinates for the face in the original image.
        target_name: A list of target names corresponding to the target images.
        target_image: A list of pre-encoded target face images.

    Returns:
        The name of the identified target, or None if the target is not recognized.
    """
    left, top, right, bottom = box
    t_width = right-left
    t_height = bottom-top
    sub_image = frame[top:top+t_height, left:left+t_width]
    img = cv2.cvtColor(   
                    sub_image,
                    cv2.COLOR_BGR2RGB
                )
    img_encoding = face_recognition.face_encodings(
                img
            )
            
    if len(img_encoding) >  0:
        matched_results = face_recognition.compare_faces(target_images, img_encoding[0])
        if True in matched_results:
                    # Do something with the index of the matching face
            result = matched_results.index(True)
                    
            return target_names[result]
        else:
            logging.debug("Target not recognized")
            return None




def find_faces_in_frame(frame) -> List[Tuple[int, int, int, int]]:
    """
    Detect faces in the given frame using the specified image compression factor.

    Args:
        frame: A frame containing the faces to be detected.
        image_compression: The compression factor to resize the input frame for faster face detection.

    Returns:
        List[Tuple[int, int, int, int]]: A list of tuples containing the face bounding box coordinates (top, right, bottom, left) for each detected face.
    """

    face_locations = face_recognition.face_locations(frame)
    return face_locations



def draw_face_box(frame: np.ndarray, target: dict, is_on_target: bool ) -> np.ndarray:
    left, top, right, bottom = target["box"]
    box_width = right-left
    box_center_x = (left + right) // 2
    box_center_y = (top + bottom) // 2
    # Get the image dimensions
    frame_height, frame_width = frame.shape[:2]

    # Calculate the center of the image
    frame_center_x, frame_center_y = frame_width // 2, frame_height // 2
    
    target_highlight_color = (0, 0, 255) if is_on_target else (0, 100, 0)
        
    cv2.rectangle(frame, (left, top), (right, bottom), target_highlight_color, 2)
    # Draw a label with a name below the face

    cv2.rectangle(frame, (left, bottom - 35), (right, bottom), target_highlight_color, cv2.FILLED)

    lock_text = "Lock" if is_on_target else f""
    
    movement_vector = [frame_center_x - box_center_x, frame_center_y - box_center_y]
    
    box_text = target.get("id", '') if target.get("id") \
        else f"{lock_text} {movement_vector} { math.sqrt(movement_vector[0]**2 + movement_vector[1]**2):.2f}" # Distance from center
    
    font = cv2.FONT_HERSHEY_DUPLEX
    font_scale = (box_width/frame_width) + 1
    font_size = 0.4
    scaled_font = font_size * (font_scale ** 3)
    cv2.putText(frame, box_text, (left + 6, bottom - 6), font, scaled_font, (255, 255, 255), 1)    
    
    return frame


def draw_cross_hair(frame: np.ndarray, cross_hair_size: int, target: dict, is_on_target: bool) -> np.ndarray:# Draw a red horizontal line through the center
    left, top, right, bottom = target["box"]
 
    # Get the image dimensions
    height, width = frame.shape[:2]

    # Calculate the center of the image
    center_x, center_y = width // 2, height // 2

    is_on_target = False  
    if top <= center_y <= bottom and left <= center_x <= right:
        is_on_target=True
    
    color = (0, 0, 255) if is_on_target else (0, 100, 0)
    target_highlight_size = 5 if is_on_target else 1

    cv2.line(frame, (center_x - cross_hair_size, center_y), (center_x + cross_hair_size, center_y), color, target_highlight_size)
                
    # Draw a red vertical line through the center
    cv2.line(frame, (center_x, center_y - cross_hair_size), (center_x, center_y + cross_hair_size), color, target_highlight_size)
    
    return frame