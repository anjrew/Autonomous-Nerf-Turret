# import abc
from typing import TypedDict

# class TurretController(abc.ABC):
    
    # @abs.abstractmethod()
    # def    
    
    
class TurretAction(TypedDict):
    """
    Represents an action command to send to the turret.

    azimuth_angle: The azimuth angle to try an turn the turret by.
    is_clockwise: True if the controller should move clockwise; False otherwise.
    speed: The speed of the controller's elevation movement.
    is_firing: True if the controller should firing; False otherwise.
    """
    azimuth_angle: int
    is_clockwise: bool
    speed: int
    is_firing: bool