
from typing import List, TypedDict


class AiControllerArgs(TypedDict):
    """The arguments for the AiController"""
    target_padding: float
    search: bool
    target_type: str
    accuracy_threshold_x: float
    accuracy_threshold_y: float
    max_azimuth_angle: float
    max_elevation_speed: float
    elevation_dp: float
    y_speed: float
    x_speed_max: int
    x_smoothing: float
    azimuth_dp: int
    target_ids: List[str]