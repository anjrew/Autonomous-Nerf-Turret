from typing import List, Optional, Tuple
import logging
import cv2
import face_recognition
import math


def get_face_location_details(image_compression:int, height:int, width:int, face_location:tuple) -> dict:
    """
    Calculate face location details based on the given image dimensions and face location.
    
    Args:
        image_compression: The compression factor applied to the original image.
        height: The height of the image in pixels.
        width: The width of the image in pixels.
        face_location: A list containing the face bounding box coordinates [top, right, bottom, left].

    Returns:
        dict: A dictionary containing the following keys:
            - vec_delta: A list containing the x and y movement vectors of the face bounding box's center relative to the image's center.
            - locked: A boolean indicating whether the face is centered within the image.
            - box: A list containing the adjusted face bounding box coordinates [left, top, right, bottom].
    """
    top, right, bottom, left = face_location
    
    top *= image_compression
    right *= image_compression
    bottom *= image_compression
    left *= image_compression
        
    # Calculate the center coordinates
    center_x = width // 2
    center_y = height // 2
    is_on_target = False  
    if top <= center_y <= bottom and left <= center_x <= right:
        is_on_target=True
        
    box_center_x = (left + right) / 2
    box_center_y = (top + bottom) / 2
        
    movement_vector = [box_center_x - center_x, box_center_y - center_y]
                    
    target = { "vec_delta": movement_vector, "locked": is_on_target, "box": [left, top, right, bottom]}
    
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




def find_faces_in_frame(frame, image_compression: int) -> List[Tuple[int, int, int, int]]:
    """
    Detect faces in the given frame using the specified image compression factor.

    Args:
        frame: A frame containing the faces to be detected.
        image_compression: The compression factor to resize the input frame for faster face detection.

    Returns:
        List[Tuple[int, int, int, int]]: A list of tuples containing the face bounding box coordinates (top, right, bottom, left) for each detected face.
    """
    small_frame = cv2.resize(frame, (0, 0), fx=1/image_compression, fy=1/image_compression) #type: ignore

    face_locations = face_recognition.face_locations(small_frame)
    return face_locations



def draw_face_box(cross_hair_size, frame, height, width, target):
    left, top, right, bottom = target["box"]
    is_on_target = target.get('locked', False)
    movement_vector = target['vec_delta']
    center_x = width // 2
    center_y = height // 2
                
    lock_text = "Lock" if is_on_target else f""
    font_size = 500
    target_highlight_size = 5 if is_on_target else 1
    target_highlight_color = (0, 0, 255) if is_on_target else (0, 100, 0)
                # Draw a box around the face
    cv2.rectangle(frame, (left, top), (right, bottom), target_highlight_color, 2)
                # Draw a label with a name below the face
    cv2.rectangle(frame, (left, bottom - 35), (right, bottom), target_highlight_color, cv2.FILLED)
    font = cv2.FONT_HERSHEY_DUPLEX
    box_text = target.get("id") if target.get("id") else f"{lock_text} {movement_vector} { math.sqrt(movement_vector[0]**2 + movement_vector[1]**2):.2f}" # Distance from center

    font_size = 0.6 if len(box_text) > 20 else 1
    cv2.putText(frame, box_text, (left + 6, bottom - 6), font, font_size, (255, 255, 255), 1)

    # Draw a red horizontal line through the center
    cv2.line(frame, (center_x - cross_hair_size, center_y), (center_x + cross_hair_size, center_y), target_highlight_color, target_highlight_size)
                
    # Draw a red vertical line through the center
    cv2.line(frame, (center_x, center_y - cross_hair_size), (center_x, center_y + cross_hair_size), target_highlight_color, target_highlight_size)
    return frame