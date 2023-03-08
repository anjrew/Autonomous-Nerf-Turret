from typing import Optional, Union
import pygame
import argparse
import requests
import logging


parser = argparse.ArgumentParser()
parser.add_argument("--set-man", action="store_true",dest="is_man", help="Set the joystick manually instead of using the default.")
parser.add_argument("--port", help="Set the http server port.", default=5565, type=int)
parser.add_argument("--host", help="Set the http server hostname.", default="localhost")
parser.add_argument("--log-level", help="Set the logging level by integer value.", default=logging.DEBUG, type=int)
parser.add_argument("--speed-dp", help="Set how many decimal places the speed is taken too.", default=0, type=int)
parser.add_argument("--azimuth-dp", help="Set how many decimal places the azimuth is taken too.", default=0, type=int)
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


def map_range(input_value: Union[int,float], min_input: Union[int,float], max_input: Union[int,float], min_output: Union[int,float], max_output: Union[int,float]) -> Union[int,float]:
    """
    Maps an input value from one range to another range.

    Parameters:
        input_value (float): The input value to be mapped to the output range.
        min_input (float): The minimum value of the input range.
        max_input (float): The maximum value of the input range.
        min_output (float): The minimum value of the output range.
        max_output (float): The maximum value of the output range.

    Returns:
        float: The mapped value in the output range.

    Example:
        >>> map_range(-0.5, -1, 1, 0, 180)
        90.0
    """
    mapped_value = ((input_value - min_input) / (max_input - min_input)) * (max_output - min_output) + min_output
    return mapped_value




is_clockwise_cache = False # False is the default direction
speed_cache = 0 # 0 is the default speed
azimuth_cache = 90 # 90 is the default position
fire_cache = False # False is the default state

try:
    while True:
        
        something_changed = False # Keeps track of whether or not a request should be sent to the serve        
        
        for event in pygame.event.get():
            if event.type == pygame.JOYBUTTONDOWN:
                if event.button == 1:
                    # Fire gun when user presses A
                    fire_cache = True
                    something_changed =True

                        
            if event.type == pygame.JOYBUTTONUP:
                if event.button == 1:
                    # Fire gun when user presses A
                    fire_cache = False
                    something_changed =True
                
            if event.type == pygame.JOYAXISMOTION:
                if event.axis == 3:
                    
                    # Speed calculation 
                    speed = round(abs(event.value * 10), args.speed_dp)
                    
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
                        azimuth_angle = round(map_range(event.value,-1,1,-90, 90) , args.azimuth_dp)
                        if azimuth_angle != azimuth_cache:
                            azimuth_cache = azimuth_angle
                            something_changed =True
                               
                    
            if event.type == pygame.JOYHATMOTION:
                print(event)
     
        if something_changed:
            controller_state = {
                'azimuth_angle': azimuth_cache,
                'is_clockwise': is_clockwise_cache,
                'speed': speed_cache,
                'is_firing': fire_cache,
            }
            try:
                print('Sending controller state to server: ', controller_state)
                requests.post(url, json=controller_state)       
            except:
                logging.error("Failed to send controller state to server.")
        
            
except Exception as e:
    print(e)
    # Close the joystick and quit Pygame
    joystick.quit()
    pygame.quit()
