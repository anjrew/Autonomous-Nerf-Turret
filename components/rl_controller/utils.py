
from typing import List, Optional


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
    
    
    