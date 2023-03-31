from typing import Any, List, Optional, Tuple
from camera_vision.models import CameraVisionTarget
from nerf_turret_utils.constants import CONTROLLER_X_OUTPUT_RANGE, CONTROLLER_Y_OUTPUT_RANGE
from nerf_turret_utils.number_utils import map_range
    

def get_priority_target_index(targets: List[CameraVisionTarget], type: str,  target_ids: List[str]=[]) -> Optional[int]:
    """
    Returns the index of the highest priority target in the `targets` list based on the input `ids` and `type`.

    Args:
        targets: A list of dictionaries, each representing a target with the keys 'id' and 'type'.
        type: A target type to prioritize if none of the target IDs are found.
        target_ids: A list of target IDs to prioritize over the target types.

    Returns:
        The index of the highest priority target in the `targets` list. Returns 0 if no target is found.

    Example:
        targets = [
            {"id": "001", "type": "person"},
            {"id": "002", "type": "vehicle"},
            {"id": "003", "type": "person"}
        ]
        ids = ["003", "004"]
        type = "vehicle"
        index = get_priority_target_index(targets, ids, type)
        # Returns 1 (index of the "002" target in the `targets` list)
    """
    
    if len(target_ids) > 0: # If there are target IDs just check if the target IDs face is in the list
        assert type == "face", "The `type` argument must be 'face' if the `ids` argument is not empty, as these are face IDs."
        for i, target in enumerate(targets):
            if target.get("id", None) in target_ids:
                return i
    else:
        for i, target in enumerate(targets):
            if target["type"] == 'person' and type == 'person':
                # If the target is a person, check if it has a face
                for index, person in enumerate(targets):
                    if person['type'] == 'face':
                        return index
                return i # If no face is found, return the person
                 
            elif target["type"] == 'face' and  type == 'person':
                return i # Because a face part of a person
            
            if target["type"] == type:
                return i
    return None
    
    
def get_x_speed(view_width:int, movement_vector: Tuple[int,int]) -> int:
    """
    Gets the azimuth angle of the turret from the movement vector and returns the angle in degrees.
    Taking into account the smoothing and speed settings.
    """
    current_distance_from_the_middle = movement_vector[0]

    max_distance_from_the_middle = view_width / 2
    azimuth_speed = 0 if view_width == 0 else map_range(
        current_distance_from_the_middle,
        -max_distance_from_the_middle, # ;eft extreme
        max_distance_from_the_middle, # right extreme
        CONTROLLER_X_OUTPUT_RANGE[0],
        CONTROLLER_X_OUTPUT_RANGE[1] 
    )
    return int(azimuth_speed)
    
    
def get_y_speed(view_height:int, movement_vector:Tuple[int,int], target_box: Tuple[int,int,int,int]) -> int:
    """
    Calculates the elevation speed of a Nerf turret.

    Returns:
        int: The elevation speed of the turret.
    """
    top = target_box[1]
    bottom = target_box[3]
    max_elevation = (view_height/2)
    movement_scalar = movement_vector[1]

    if top == 0:
        return 1 # Do this of the target is to the top edge of the camera view but filling it up
    if bottom == 0:
        return -1 # Do this of the target is to the bottom edge of the camera view but filling it up
    
    elevation_speed = 0 if view_height == 0 else map_range(
        movement_scalar, 
        -max_elevation, 
        max_elevation, 
        CONTROLLER_Y_OUTPUT_RANGE[0],
        CONTROLLER_Y_OUTPUT_RANGE[1]                                  
    )              
    return int(elevation_speed)


