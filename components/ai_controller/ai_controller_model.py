import sys
import os
import json
import logging
from typing import List, Optional, Tuple, Union, get_type_hints, cast

upper_dir = os.path.dirname(os.path.abspath(__file__)) + '/..'
sys.path.append(upper_dir)
root_dir = os.path.dirname(os.path.abspath(__file__)) + '/../..'
sys.path.append(root_dir)
curr_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(curr_dir)

from nerf_turret_utils.controller_action import ControllerAction
from camera_vision.models import CameraVisionDetection, CameraVisionTarget
from nerf_turret_utils.image_utils import get_frame_box_dimensions_delta
from ai_controller_args import AiControllerArgs
from ai_controller_utils import get_priority_target_index, get_y_speed, get_x_speed


AI_CONTROLLER_KEY_TYPES = get_type_hints(AiControllerArgs)


class AiControllerSearchState:
    is_active: bool
    clockwise: bool
    heading: int
    
    def __init__(self, 
        is_active: bool = False,
        clockwise: bool = False,
        heading: int = 0, 
    ):  
        self.is_active = is_active
        self.clockwise = clockwise
        self.heading = heading
       
        assert self.is_valid(), 'Invalid AiControllerSearchState created'

    def is_valid(self):
        return all(getattr(self, prop, None) is not None for prop in get_type_hints(AiControllerSearchState))
    
class AiController:
    """A class to control the Nerf Turret based on the input from a Camera Vision Detection system. """
    
    already_sent_no_targets=False
    """Flag to track if no target message has been sent."""
    
    cached_action_state = ControllerAction(
         x=0,
         y=0,
         is_firing=False,
    ) 
    """The last Controller action that was generated"""
    
    
    search_state = AiControllerSearchState()
    """The state of the search behavior of the turret"""
    
    
    def __init__(self, args: Union[AiControllerArgs, dict] ):
        """Initialize the AiController with the given arguments"""
        if isinstance(args, AiControllerArgs):
            self.args  = args
        else:
            for prop in AI_CONTROLLER_KEY_TYPES.keys():
                if prop not in args: 
                    raise KeyError(f'Invalid arguments passed to AiController. Missing key "{prop}"')
            
            self.args = AiControllerArgs(**args)
             
        self.search_state.is_active = self.args.search
        self.args.target_padding = self.args.target_padding/100
        
      
    def get_action(self, detection: CameraVisionDetection) -> ControllerAction:
        """Generate a ControllerAction based on the input detection"""
        
        args = self.args
        
        # Check if there are any targets in the frame
        if detection is not None and len(detection['targets']) > 0:
            logging.debug('Data obtained:' + json.dumps(detection))
            target_index = self.get_priority_target_index(detection['targets'])
            
            if target_index is None:
                logging.debug(f'No valid target found from type {args.target_type} with ids {args.target_ids}')
                # If no valid target was found, then just move onto the next frame
                return self.handle_no_target(self.search_state)
            
            else:
            
                target: CameraVisionTarget = detection['targets'][target_index] # Extract the first target from the targets list
                
                if self.is_void_target(target, detection['view_dimensions']):
                    return self.handle_no_target(self.search_state)
                
                else:
                    logging.debug('Targeting:' + json.dumps(target))

                    return self.get_action_for_target(target, detection['view_dimensions'])

        else:
            return self.handle_no_target(self.search_state)
           
           
    def is_void_target(self, target: CameraVisionTarget, frame: Tuple[int,int]) -> bool:
        """Check if the target is a void target"""
        return target['box'] == (0,0,0,0) and frame == (0,0)
    
                
    def get_action_for_target(self, target: CameraVisionTarget, frame: Tuple[int,int]) -> ControllerAction:
        """Handle the case where a target is found in the frame"""
        
        if target['box'] == (0, 0, 0, 0) or frame == (0, 0):
            return self.handle_no_target(self.search_state)
        
        args = self.args

        view_width = frame[0]
        view_height = frame[1]
        
        center_x, center_y =  view_width//2, view_height//2
        
        left, top, right, bottom = target['box']
        
        # calculate box coordinates
        box_width = right - left
        box_height = bottom - top
        
        # Get movement vector to align gun with center of target
        movement_vector = get_frame_box_dimensions_delta(left, top, right, bottom, view_width, view_height)
        
        # Add padding as a percentage of the original dimensions
        padding_width = box_width * args.target_padding
        padding_height = box_height * args.target_padding

        # Calculate box coordinates
        padded_left = left + padding_width
        padded_right = right - padding_width
        padded_top = top + padding_height
        padded_bottom = bottom - padding_height
            
        is_on_target = False  
        if padded_top <= center_y <= padded_bottom and padded_left <= center_x <= padded_right:
            is_on_target=True

        action = ControllerAction(
                x=get_x_speed(view_width, movement_vector),
                y=get_y_speed(view_height, movement_vector, target['box']),
                is_firing=is_on_target,
            )
        self.cached_action_state = action
                        
        return action           
    
             
    def handle_no_target(self, search: AiControllerSearchState) -> ControllerAction:
        """
        Handle the scenario where the turret has no target to aim at. 
        
        Makes the turret search the environment for targets if 'is_active' otherwise just returns the cached state 
        """
        if search.is_active:
                    
            if search.heading > 180:
                search.heading = 0
                search.clockwise = not search.clockwise
            else:
                search.heading += 1                  
            return ControllerAction(
                x=1 if search.clockwise else -1,
                y=0,
                is_firing=False
            )
        else:
            return ControllerAction(
                x=0,
                y=0,
                is_firing=False
            )
            
            
    def get_priority_target_index(self, targets: List[CameraVisionTarget]) -> Optional[int]:
        """Get the index of the target that has the highest priority"""
        return  get_priority_target_index(targets, self.args.target_type, self.args.target_ids)
    
    def is_valid(self):
        return all(getattr(self, prop, None) is not None for prop in get_type_hints(AiController))