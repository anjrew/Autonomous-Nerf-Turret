from argparse import Namespace
import sys
import os
import json
import logging
from typing import List, Optional, Tuple

upper_dir = os.path.dirname(os.path.abspath(__file__)) + '/..'
sys.path.append(upper_dir)
root_dir = os.path.dirname(os.path.abspath(__file__)) + '/../..'
sys.path.append(root_dir)
curr_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(curr_dir)

from nerf_turret_utils.turret_controller import TurretAction
from camera_vision.models import CameraVisionDetection, CameraVisionTarget
from nerf_turret_utils.image_utils import get_frame_box_dimensions_delta
from nerf_turret_utils.number_utils import map_range
from ai_controller_utils import slow_start_fast_end_smoothing, get_priority_target_index, get_elevation_speed, get_elevation_clockwise


class AiController:
    """A class to control the Nerf Turret based on the input from a Camera Vision Detection system. """
    
    already_sent_no_targets=False
    """Flag to track if no target message has been sent."""
    
    cached_action_state: TurretAction = {
        'azimuth_angle': 0,
        'is_clockwise': True,
        'speed': 0,
        'is_firing': False,
    }
    """The last TurretAction instance that was generated"""
    
    
    search_state = {
        'is_active': False,
        'clockwise': True,
        'heading': 0,
    }
    """The state of the search behavior of the turret"""
    
    
    def __init__(self, args: dict):
        """Initialize the AiController with the given arguments"""
        self.args = args
        self.args['target_padding'] = args['target_padding']/100
        self.search_state['active'] = args['search']
        
        self.args['target_ids'] =  args.get('targets') or args.get('target_ids') or []
      
      
    def get_action(self, detection: CameraVisionDetection) -> TurretAction:
        """Generate a TurretAction based on the input detection"""
        
        args = self.args
        
        # Check if there are any targets in the frame
        if detection is not None and len(detection['targets']) > 0:
            logging.debug('Data obtained:' + json.dumps(detection))
            target_index = self.get_priority_target_index(detection['targets'])
            
            if target_index is None:
                logging.debug(f'No valid target found from type {args["target_type"]} with ids {args["targets"]}')
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
    
                
    def get_action_for_target(self, target: CameraVisionTarget, frame: Tuple[int,int]) -> TurretAction:
        """Handle the case where a target is found in the frame"""
        
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
        padding_width = box_width * args['target_padding']
        padding_height = box_height * args['target_padding']

        # Calculate box coordinates
        padded_left = left + padding_width
        padded_right = right - padding_width
        padded_top = top + padding_height
        padded_bottom = bottom - padding_height
            
        is_on_target = False  
        if padded_top <= center_y <= padded_bottom and padded_left <= center_x <= padded_right:
            is_on_target=True
        
        current_distance_from_the_middle = movement_vector[0]
        max_distance_from_the_middle_left = -(view_width / 2)
        max_distance_from_the_middle_right = view_width / 2
    
        predicted_azimuth_angle = map_range(
            current_distance_from_the_middle - args['accuracy_threshold_x'],
            max_distance_from_the_middle_left, 
            max_distance_from_the_middle_right ,
            -args['max_azimuth_angle'] ,
            args['max_azimuth_angle']
        )
        azimuth_speed_adjusted = min(predicted_azimuth_angle , args['x_speed'])
        smoothed_speed_adjusted_azimuth = slow_start_fast_end_smoothing(azimuth_speed_adjusted, float(args['x_smoothing']) + 1.0, 90)
        azimuth_formatted = round(smoothed_speed_adjusted_azimuth, args['azimuth_dp'])

        action: TurretAction = {
            'azimuth_angle': int(azimuth_formatted),
            'is_clockwise': get_elevation_clockwise(movement_vector),
            'speed': get_elevation_speed(args, view_height, movement_vector, target['box']),
            'is_firing': is_on_target,
        }
        self.cached_action_state = action
                        
        return action                
    
             
    def handle_no_target(self, search: dict) -> TurretAction:
        """
        Handle the scenario where the turret has no target to aim at. 
        
        Makes the turret search the environment for targets if 'is_active' otherwise just returns the cached state 
        """
        if search['is_active']:
                    
            if search['heading'] > 180:
                search['heading'] = 0
                search["clockwise"] = not search["clockwise"]
            else:
                search['heading'] += 1                  
            return {
                **self.cached_action_state,
                'azimuth_angle': 1 if search["clockwise"] else -1,
                'speed': 0,
                'is_firing': False,
            }
        else:
            return {
                **self.cached_action_state,
                'azimuth_angle': 1 if search["clockwise"] else -1,
                'speed': 0,
                'is_firing': False,
            }
            
            
    def get_priority_target_index(self, targets: List[CameraVisionTarget]) -> Optional[int]:
        """Get the index of the target that has the highest priority"""
        return  get_priority_target_index(targets, self.args['target_type'], self.args['target_ids'])