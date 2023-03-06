import time
from typing import Optional
import pygame
import argparse
import requests
import logging
import json


parser = argparse.ArgumentParser()
parser.add_argument("--set-man", action="store_true",dest="is_man", help="Set the joystick manually instead of using the default.")
parser.add_argument("--port", help="Set the http server port.", default=5565, type=int)
parser.add_argument("--host", help="Set the http server hostname.", default="localhost")
parser.add_argument("--log-level", help="Set the logging level by integer value.", default=logging.DEBUG, type=int)
parser.add_argument("--speed-dp", help="Set how many decimal places the speed is taken too.", default=0, type=int)
args = parser.parse_args()

logging.basicConfig(level=args.log_level)

url = f"http://{args.host}:{args.port}"
logging.info(f'Forwarding controller values to host at {url}')

# Initialize the joystick module
pygame.init()
pygame.joystick.init()


# Get the number of connected joysticks
joystick_count = pygame.joystick.get_count()
print(f'Found {joystick_count} joystick{ "s" if joystick_count != 1 else "" }')

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
print('Initialized ', joystick.get_name())


is_clockwise_cache = False
speed_cache = 0

try:
    while True:
        
        for event in pygame.event.get():
            if event.type == pygame.JOYBUTTONDOWN:
                if event.button == 1:
                    # Fire gun when user presses A
                    try:
                        requests.post(url, json={ 'fire': True })
                    except Exception as e:
                        logging.error(e)
                        
            if event.type == pygame.JOYBUTTONUP:
                print(event)
                
                
            if event.type == pygame.JOYAXISMOTION:
                if event.axis == 3:
                    
                    try:
                        ## Move elevation of gun
                        
                        # Speed calculation 
                        speed = round(abs(event.value * 10), args.speed_dp)
                        
                        if speed != speed_cache:
                            requests.post(url, json={
                                    'speed': speed if speed <= 10 else 10 
                                })
                            speed_cache = speed
                        
                        # Direction calculation
                        clockwise_state = event.value > 0
                        if clockwise_state != is_clockwise_cache:
                            print(clockwise_state)
                            requests.post(url, json={
                                'isClockwise': clockwise_state 
                            })
                            is_clockwise_cache = clockwise_state
                            
                    except Exception as e:
                        logging.error(e)

                    
                if event.axis == 2:
                    print('Not done yet',event)
                    try:
                        ## Move azimuth of gun
                        speed = abs(event.value * 10)
                        # requests.post(url, json={
                        #         'isClockwise': event.value > 0, 
                        #         'speed': speed if speed <= 10 else 10 
                        #     })
                    except Exception as e:
                        logging.error(e)
                    
                    
            if event.type == pygame.JOYHATMOTION:
                print(event)
            
        
            
except Exception as e:
    print(e)
    # Close the joystick and quit Pygame
    joystick.quit()
    pygame.quit()
