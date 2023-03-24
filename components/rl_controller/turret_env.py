import os
import sys
from typing import Callable, Optional, Tuple
import math
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + '/..')

from nerf_turret_utils.turret_controller import TurretAction

import gym
from gym import spaces
from typing import TypedDict


class TurretEnvState(TypedDict):
    previous_action: TurretAction
    target: Tuple[int,int,int,int, int, int]
    previous_state: Optional['TurretEnvState']  # use forward reference for recursive type


class TurretEnv(gym.Env):
    
    NO_TARGET_STATE = (0, 0, 0, 0, 0, 0)
    """A tuple representing the observation state of the environment when there is no target.
    The format of the tuple is (left, top, right, bottom, height, width) with all values set to 0.0.
    """
    
    INITIAL_STATE: TurretEnvState = {
            'target': NO_TARGET_STATE,
            'previous_action': {
                'azimuth_angle': 90,
                'is_clockwise': False,
                'speed': 0,
                'is_firing': False
            },
            'previous_state': None
        }
    """The state object with its initial values"""
    
    state = INITIAL_STATE
    
    action_space = spaces.Discrete(4)
    
    
    observation_space = spaces.Tuple(
            (
                spaces.Box(low=-1, high=1, shape=(1,), dtype=float),
                spaces.Box(low=-1, high=1, shape=(1,), dtype=float),
                spaces.Box(low=-1, high=1, shape=(1,), dtype=float),
                spaces.Box(low=-1, high=1, shape=(1,), dtype=float),
            )
        )
    
    
    """The observation space of the environment.
    This property is an instance of the `Tuple` class from the `gym.spaces` module,
    which represents a tuple of spaces.
    The tuple contains four instances of the `Box` class, each of which represents
    a continuous space with values between -1 and 1.
    """
    
    step_n = 0
    """The number of steps that have been taken in the environment.
    This property is an integer representing the number of steps that have been taken
    in the environment so far.
    """
    
    
    def __init__(self, 
                 target_provider: Callable[[], Tuple[int, int, int, int,int, int]], 
                 action_dispatcher: Callable[[TurretAction], None],
                 episode_step_limit = 100 
        ) -> None:
        super(TurretEnv, self).__init__()
        self.episode_time = episode_step_limit
        self.target_provider = target_provider 
        self.action_dispatcher = action_dispatcher
        

        
    def step(self, action: TurretAction) -> Tuple:
        
        # Finish the episode if the step limit is reached
        done = self.step_n >= self.episode_time
        
        # Get the new information from the camera on the turret
        target = self.target_provider()
        
        reward = self.calc_reward(target, action) # type: ignore
        
        self.state = {
            'target': target,
            'previous_action': action,
            'previous_state': self.state
        }
        
        self.step_n += 1
        # observation (object): agent's observation of the current environment
        # reward (float) : amount of reward returned after previous action
        # done (bool): whether the episode has ended, in which case further step() calls will return undefined results
        # info (dict): contains auxiliary diagnostic information (helpful for debugging, and sometimes learning)
        return self.state, reward, done, { 'step': self.step_n }    
    
    
    def calc_reward(self, new_target_state: Tuple[int, int, int, int, int, int], action:TurretAction) -> float:
        """Calculates the reward for the current state of the environment.
        
        Args:
            target: A tuple of integers representing the original coordinates of the target box
                with the height and width in the format (left, top, right, bottom, frame_height, frame_width).
        
        Returns:
            A float representing the reward for the current state of the environment.
        """
        left, top, right, bottom, frame_height, frame_width =  new_target_state
        
        frame_center_x, frame_center_y = frame_width // 2, frame_height // 2
        box_center_x = (left + right) // 2
        box_center_y = (top + bottom) // 2
        
        # Get the original coordinates of the box with the height and width
        is_on_target = self.check_is_on_target(new_target_state)
        
        is_shooting = action['is_firing']
        # Return nothing as punishment for shooting with no target or shooting off target
        if (new_target_state == self.NO_TARGET_STATE and is_shooting) \
            or (not is_on_target and is_shooting):
            return 0 
        
        # Start off with a base reward so things can be taken away from it if need be
        reward = 1
        
        if new_target_state == self.NO_TARGET_STATE and not is_shooting:
            return reward # Return most basic reward without punishing if there is no target
        
        # Get a reward which is higher when the distance is closer to zero
        reward += self.get_accuracy_reward(frame_height, frame_width, frame_center_x, frame_center_y, box_center_x, box_center_y)
        
        if is_on_target and is_shooting:
            reward += 0.5 # Add reward if is on target
            
            
        return reward


    def check_is_on_target(self, new_target_state) -> bool:
        """Checks if the target is on the target with the given coordinates."""
        left, top, right, bottom, frame_height, frame_width= new_target_state
        center_x, center_y = self.get_center_coords(frame_height, frame_width)
        
        # if the center of the frame is within the target box, then it is on target
        return self.check_center_within_bounds(left, top, right, bottom, center_x, center_y)


    def get_center_coords(self, frame_height, frame_width):
        center_x = frame_width // 2
        center_y = frame_height // 2
        return center_x,center_y
    

    def check_center_within_bounds(self, left, top, right, bottom, center_x, center_y) -> bool:
        return top <= center_y <= bottom and left <= center_x <= right


    def get_accuracy_reward(  
            self,                      
            frame_height: int, 
            frame_width: int, 
            frame_center_x: int, 
            frame_center_y: int, 
            box_center_x: int, 
            box_center_y: int
        ) -> float:
        """Calculates the accuracy reward based on the distance between the frame center and the target box center.
        
        Args:
            frame_height: An integer representing the height of the frame.
            frame_width: An integer representing the width of the frame.
            frame_center_x: An integer representing the x-coordinate of the center of the frame.
            frame_center_y: An integer representing the y-coordinate of the center of the frame.
            box_center_x: An integer representing the x-coordinate of the center of the target box.
            box_center_y: An integer representing the y-coordinate of the center of the target box.
            
        Returns:
            A float representing the accuracy reward based on the distance between the frame center and the target box center.
        """

        reward =+ (1 - self.get_normalized_distance_to_target(frame_height, frame_width, frame_center_x, frame_center_y, box_center_x, box_center_y))
        return reward - 0.5 # Remove half so if max distance from the center no reward is given
        

    def get_normalized_distance_to_target(self, 
            frame_height: int, 
            frame_width: int, 
            frame_center_x: int, 
            frame_center_y: int,
            box_center_x: int, 
            box_center_y: int
        ) -> float:
        """Calculates the normalized distance between the center of the frame and the center of the target box.
        
        Args:
            frame_height: An integer representing the height of the frame.
            frame_width: An integer representing the width of the frame.
            frame_center_x: An integer representing the x-coordinate of the center of the frame.
            frame_center_y: An integer representing the y-coordinate of the center of the frame.
            box_center_x: An integer representing the x-coordinate of the center of the target box.
            box_center_y: An integer representing the y-coordinate of the center of the target box.
        
        Returns:
            A float representing the normalized distance between the center of the frame and the center of the target box.
        """
        movement_vector = (frame_center_x - box_center_x, frame_center_y - box_center_y)
        # Calculate the distance of the movement vector using the Pythagorean theorem
        distance = math.sqrt(movement_vector[0]**2 + movement_vector[1]**2)
        # Normalize the distance between 0 and 1
        max_distance = math.sqrt(frame_width**2 + frame_height**2)
        return distance / max_distance # return the normalized distance

    
    def reset(self) -> TurretEnvState:
        """Resets the environment to the initial state to start a new episode"""

        # reset environment state to initial state
        self.state = self.INITIAL_STATE
        self.step_n = 0
        return self.state