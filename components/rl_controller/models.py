# Standard library imports
import os
import sys
from typing import Optional, Tuple, TypedDict

# Local application imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + '/..')
from nerf_turret_utils.turret_controller import TurretAction


class TurretEnvState(TypedDict):
    """
    TurretEnvState holds information about the current state of the Turret environment.

    Attributes:
        previous_action: The previous action taken by the turret.
        target: A tuple representing the target's position and size.
        previous_state: The previous state of the environment, or None if this is the initial state.
            Use forward reference for recursive typing.
    """
    previous_action: TurretAction
    target: Tuple[int, int, int, int, int, int]
    previous_state: Optional['TurretEnvState']



class TurretObservationSpace(TypedDict):
    """
    TurretObservationSpace holds information about the bounding box of the target and the image dimensions.

    Attributes:
        box: A tuple representing the left,top,right,bottom bounding box coords of the target.
        frame_height: The height of the image view's frame.
        frame_width: The width of the image view's frame.
    """
    box: Tuple[int, int, int, int]
    view_dimensions: Tuple[int,int]
    """The frame width and frame height"""