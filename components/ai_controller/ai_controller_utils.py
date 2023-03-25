from typing import Any, List, Optional, Tuple
from nerf_turret_utils.number_utils import map_range
    
    
def slow_start_fast_end_smoothing(x: float, p: float, max_value: int) -> float:
    """
    Maps an input value to an output value using a power function with a slow start and fast end.

    The output value increases slowly at the beginning when the input value is small,
    but increases more rapidly as the input value approaches the maximum value of 10.

    Args:
        x (float): The input value to be mapped, in the range of 0 to 10.
        p (float): The exponent of the power function used to map the input value to the output value.
            A larger value of p will result in a faster increase in the output value towards the end of the range.

    Returns:
        float: The mapped output value, in the range of 0 to 10.
    """
    
    ratio = x / max_value
    output = ratio ** p * max_value
    return output if x >= 0 else -abs(output)


def get_priority_target_index(targets: List[dict], type: str,  target_ids: List[str]=[]) -> Optional[int]:
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
    
    
    
def get_elevation_speed(args: Any, view_height:int, movement_vector:Tuple, target_box: Tuple[int,int,int,int]) -> int:
    """
    Calculates the elevation speed of a Nerf turret.

    Args:
        args: Any object containing the necessary arguments for the calculation.
        view_heigh: The height of the camera view in pixels.
        movement_vector : A tuple containing x,y movement vector of the turret to te center of the view.
        target_box: A tuple containing the coordinates of the target box [left, top, right, bottom].

    Returns:
        int: The elevation speed of the turret.
    """
    top = target_box[1]
    max_elevation = (view_height/2)
    abs_movement_vector = abs(movement_vector[1])

    if top == 0:
        return 1 # Do this of the target is to the edge of the camera view but filling it up
    
    elevation_speed_adjusted = map_range(abs_movement_vector - args.accuracy_threshold_y, 0, max_elevation, 0 , args.max_elevation_speed) * float(args.y_speed)
    # TODO: implement a smoothing function to smooth out the speed
    # smooth_elevation_speed_adjusted = min(0,slow_start_fast_end_smoothing(elevation_speed_adjusted, float(args.y_smoothing) + 1.0, 10))                
    final_speed = round(elevation_speed_adjusted / 2 , args.elevation_dp)
    return int(final_speed)


def get_elevation_clockwise(movement_vector: Tuple[float, float]) -> bool:
    """
    Determines whether the Nerf turret elevation stepper motor should rotate clockwise based on its movement vector.

    Args:
        movement_vector (Tuple[float, float]): A tuple containing the movement vector of the turret,
            where the first element is the horizontal movement and the second element is the vertical movement.

    Returns:
        bool: True if the turret elevation should rotate clockwise, False otherwise.
    """

    is_clockwise = movement_vector[1] < 0
    return is_clockwise