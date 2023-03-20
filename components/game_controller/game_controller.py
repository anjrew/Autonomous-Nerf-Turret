import math
import time
from typing import Optional, Union
import pygame
import argparse
import requests
import logging
import json
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + '/..')
from nerf_turret_utils.args_utils import map_log_level
from nerf_turret_utils.number_utils import map_range


parser = argparse.ArgumentParser()
parser.add_argument("--set-man", action="store_true",dest="is_man", help="Set the joystick manually instead of using the default.")
parser.add_argument("--port", help="Set the http server port.", default=5565, type=int)
parser.add_argument("--host", help="Set the http server hostname.", default="localhost")
parser.add_argument("--speed-dp", help="Set how many decimal places the speed is taken too.", default=0, type=int)
parser.add_argument("--azimuth-dp", help="Set how many decimal places the azimuth is taken too.", default=0, type=int)
parser.add_argument("--test", "-t", help="Test without trying to emit data.", action='store_true', default=False)
parser.add_argument("--log-level", "-ll" , help="Set the logging level by integer value.", default=logging.INFO, type=map_log_level)
parser.add_argument("--delay", "-d",help="Delay to rate the data is sent from the controller in seconds. This can help with buffering problems", default=0.05, type=float)


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

is_clockwise_cache = False # False is the default direction
speed_cache = 0 # 0 is the default speed
azimuth_cache = 90 # 90 is the default position
fire_cache = False # False is the default state

try:
    while True:
        time.sleep(args.delay)
        
        something_changed = False # Keeps track of whether or not a request should be sent to the serve        
        
        for event in pygame.event.get():
            logging.debug("Controller Event:" + str(event))
            
            
            if event.type == pygame.JOYBUTTONDOWN:
                if event.button == 7:
                    # Fire gun when user presses A
                    fire_cache = True
                    something_changed =True

                        
            if event.type == pygame.JOYBUTTONUP:
                if event.button == 7:
                    fire_cache = False
                    something_changed =True
                
            if event.type == pygame.JOYAXISMOTION:
                if event.axis == 3:
                    
                    # Speed calculation 
                    speed = round(abs(event.value * 9), args.speed_dp)
                    
                    if speed != speed_cache:
                        speed_cache = speed
                        something_changed =True
                    
                    # Direction calculation
                    clockwise_state = event.value > 0
                    if clockwise_state != is_clockwise_cache:
                        is_clockwise_cache = clockwise_state
                        something_changed =True
                        
                    
                if event.axis == 2:
                   
                        # azimuth_angle = round(map_range(event.value,-1,1,0,180) , args.azimuth_dp)
                        azimuth_angle = math.ceil(map_range(event.value,-1,1,-15, 15))
                        if azimuth_angle != azimuth_cache:
                            azimuth_cache = azimuth_angle
                            something_changed =True
     
        if something_changed and not args.test:
            controller_state = {
                'azimuth_angle': -int(azimuth_cache), # Invert the azimuth angle because with the current config it was sending it backwar1010             'is_clockwise': is_clockwise_cache,
                'is_clockwise': bool(is_clockwise_cache),
                'speed': int(speed_cache),
                'is_firing': bool(fire_cache),
            }
            try:
                logging.debug('Sending controller state to server: ' + json.dumps(controller_state))
                requests.post(url, json=controller_state)       
            except:
                logging.error("Failed to send controller state to server.")
        
            
except Exception as e:
    # Close the joystick and quit Pygame
    joystick.quit()
    pygame.quit()
    raise e
