from typing import List, Optional, Tuple, TypedDict


class CameraVisionTarget(TypedDict):
    """Object representing a target detected by the camera vision component"""
    
    id: Optional[str]
    """An optional identifier"""
    
    box: Tuple[int,int,int,int]
    """left, top, right, bottom coordinates of the target"""
    
    type: str
    """The type of target that was detected"""
    
    mask: Optional[List[int]]
    """An optional segmentation mask"""


class CameraVisionDetection(TypedDict):
    """Object representing a detection by the camera vision component"""
    
    targets: List[CameraVisionTarget]
    """A list of target detections"""
    
    view_dimensions: Tuple[int,int]
    """The frame width and frame height"""



