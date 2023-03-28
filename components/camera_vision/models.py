from typing import List, Optional, Tuple, TypedDict


class CameraVisionTarget(TypedDict):
    id: Optional[str]
    """An optional identifier"""
    
    box: Tuple[int,int,int,int]
    """left, top, right, bottom coordinates of the target"""
    
    type: str
    """The type of target that was detected"""
    
    mask: Optional[List[int]]
    """An optional segmentation mask"""

class CameraVisionDetections(TypedDict):
    
    targets: List[CameraVisionTarget]
    """A list of target detections"""
    
    heading_vect: Tuple[int,int]
    """The Center x,y of the view coordinates"""
    
    view_dimensions: Tuple[int,int]
    """The frame width and frame height"""



