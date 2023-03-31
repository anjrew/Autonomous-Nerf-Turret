import math
import time
from typing import Optional
import pygame
import argparse
import requests
import logging
import json
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + '/..')
from nerf_turret_utils.controller_action import ControllerAction
from nerf_turret_utils.args_utils import map_log_level
from nerf_turret_utils.number_utils import map_range
from nerf_turret_utils.constants import CONTROLLER_X_OUTPUT_RANGE, CONTROLLER_Y_OUTPUT_RANGE


parser = argparse.ArgumentParser()
parser.add_argument("--set-man", action="store_true",dest="is_man", help="Set the joystick manually instead of using the default.")
parser.add_argument("--port", help="Set the http server port.", default=5565, type=int)
parser.add_argument("--host", help="Set the http server hostname.", default="localhost")
parser.add_argument("--test", "-t", help="Test without trying to emit data.", action='store_true', default=False)
parser.add_argument("--log-level", "-ll" , help="Set the logging level by integer value.", default=logging.INFO, type=map_log_level)
parser.add_argument("--delay", "-d",help="Delay to rate the data is sent from the controller in seconds. This can help with buffering problems", default=0.05, type=float)

# Buttons
parser.add_argument("--fire-button", "-fb",help="The button code for firing\n - Macbook(5)\n - Ubuntu(5)", default=5, type=int)
parser.add_argument("--elevation-button", "-eb",help="The button code for moving elevation\n - Ubuntu(4)", default=4, type=int)
parser.add_argument("--azimuth-button", "-ab",help="The button code for moving azimuth\n - Ubuntu(0)", default=0, type=int)


args = parser.parse_args()

logging.basicConfig(level=args.log_level)

url = f"http://{args.host}:{args.port}"
logging.info(f'Forwarding controller values to host at {url}')

# Initialize the joystick module
pygame.init()
pygame.joystick.init()


# Get the number of connected joysticks
joystick_count = pygame.joystick.get_count()
logging.info(f'Found {joystick_count} joystick{ "s" if joystick_count != 1 else "" }')

selectionIdx = None
joystick = Optional[pygame.joystick.JoystickType]
if args.is_man:
        
        print("\nJoystick options: ")
        # List the names of the connected joysticks
        for i in range(joystick_count):
            joystick = pygame.joystick.Joystick(i)
            joystick.init()
            name = joystick.get_name()
            print(f"{i}: {name}")
            
        
        while selectionIdx == None or int(selectionIdx) >= joystick_count:
            selectionIdx = input("Select Joystick: ")
            if int(selectionIdx) >= joystick_count or int(selectionIdx) < 0:
                print("Invalid Joystick Selected")
            else:
                joystick = pygame.joystick.Joystick(int(selectionIdx))

selectionIdx = 0 if not selectionIdx else selectionIdx
joystick = pygame.joystick.Joystick(int(selectionIdx)) 


# Select the joystick you want to use
joystick.init()
logging.info('Initialized ' + joystick.get_name())

elevation_cache = 0 # 0 is the default speed
azimuth_cache = 0 # 0 is the default position
fire_cache = False # False is the default state

try:
    while True:
        time.sleep(args.delay)
        
        something_changed = False # Keeps track of whether or not a request should be sent to the serve        
        
        events = pygame.event.get()
        
        for event in events:
            logging.debug("Controller Event:" + str(event))
                
            if event.type == pygame.JOYAXISMOTION:

                        
                if event.axis == args.fire_button:
                    should_fire = event.value == 1
                    something_changed = should_fire != fire_cache
                    fire_cache = should_fire
                
                
                if event.axis == args.elevation_button:
                    
                    elevation = math.ceil(map_range(event.value, -1, 1, CONTROLLER_Y_OUTPUT_RANGE[0], CONTROLLER_Y_OUTPUT_RANGE[1]))
                    
                    if elevation != elevation_cache:
                        elevation_cache = elevation
                        something_changed =True                 
                    
                if event.axis == args.azimuth_button:
                   
                    azimuth_angle = math.ceil(map_range(event.value,-1, 1, CONTROLLER_X_OUTPUT_RANGE[0], CONTROLLER_X_OUTPUT_RANGE[1]))
                    
                    if azimuth_angle != azimuth_cache:
                        azimuth_cache = azimuth_angle # Minus 1 for rounding error
                        something_changed =True
     
        # if something_changed and not args.test:
        controller_state = ControllerAction(
                x=-int(azimuth_cache),# Invert the azimuth angle because with the current config it was sending it backwar
                y=int(elevation_cache),
                is_firing =  bool(fire_cache)
        )
        
        if something_changed:
            logging.info(f'Controller State: {controller_state.__dict__}')
            
            if not args.test:
                try:
                    logging.debug('Sending controller state to serial port.')
                    requests.post(url, json=controller_state.__dict__)       
                except Exception as e:
                    logging.error("Failed to send controller state to server." + str(e))
            
            
except Exception as e:
    # Close the joystick and quit Pygame
    joystick.quit()
    pygame.quit()
    raise e
