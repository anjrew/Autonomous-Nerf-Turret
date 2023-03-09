import argparse
import logging
import socket
import json
from typing import Union
import requests
import time
import math

# Define the conversion function
def map_log_level(level_str) -> int:
    if type(level_str) == int or level_str.isdigit():
        return int(level_str)
    elif level_str.isalpha():
        level_name = level_str.upper()
        try:
            level = logging.getLevelName(level_name)
            return level
        except ValueError:
            raise argparse.ArgumentTypeError(f"Invalid logging level: {level_str}")
    else:
        raise argparse.ArgumentTypeError(f"Invalid logging level: {level_str}")


parser = argparse.ArgumentParser()
parser.add_argument("--ws-port", help="Set the web socket server port to recieve messages from.", default=6565, type=int)
parser.add_argument("--ws-host", help="Set the web socket server hostname to recieve messages from.", default="localhost")
parser.add_argument("--port", help="Set the web server server port to send commands too.", default=5565, type=int)
parser.add_argument("--host", help="Set the web server server hostname. to send commands too", default="localhost")
parser.add_argument("--log-level", help="Set the logging level by integer value or string representation.", default=logging.INFO, type=map_log_level)
parser.add_argument("--azimuth-dp", help="Set how many decimal places the azimuth is taken too.", default=2, type=int)
parser.add_argument("--elevation-dp", help="Set how many decimal places the elevation is taken too.", default=2, type=int)
parser.add_argument("--delay","-d", help="Delay to limit the data flow into the websocket server.", default=0, type=int)
parser.add_argument("--test","-t", help="For testing it will not send requests to the driver.", action="store_true")
parser.add_argument("--speed","-s", help="Set the speed factor o multiply the speed", default=0.28)
parser.add_argument("--smoothing","-sm", help="The amount of smoothing factor for speed to optimal position", default=1, type=float )


parser.add_argument("--target-padding", "-p",help="""
                    Set the padding for when the gun will try and shoot relative to the edge of the target in %.
                    The amount of padding around the target bounding box in pixels that the gun will ignore before shooting
                    """, default=10, type=int)

parser.add_argument('--accuracy-threshold', '-th', type=int, default=45, 
                    help="""
                    The threshold of how accurate the gun will try to get the target in the center of the crosshair in pixels.
                    """ )

# parser.add_argument('--vert-offset', '-v', type=int, default=5, 
#                     help="""
#                     The vertical offset the gun will aim for from the center of the crosshair in pixels so gravity is taken into account.
#                     """ )


args = parser.parse_args()

logging.basicConfig(level=args.log_level)

TARGET_PADDING_PERCENTAGE = args.target_padding/100
ACCURACY_THRESHOLD= args.accuracy_threshold/100
WS_HOST = args.ws_host  # IP address of the server
WS_PORT = args.ws_port  # Port number to listen on


url = f"http://{args.host}:{args.port}"
logging.info(f'Forwarding controller values to host at {url}')

# Cache the controller state to prevent sending the same values over and over again
cached_controller_state ={
    'azimuth_angle': 0, # The angle of the gun in the horizontal plane adjustment
    'is_clockwise': False,
    'speed': 0,
    'is_firing': False,
} 

def map_range(
    input_value: Union[int,float], 
    min_input: Union[int,float], 
    max_input: Union[int,float], 
    min_output: Union[int,float], 
    max_output: Union[int,float]
    ) -> Union[int,float]:
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


def slow_start_fast_end_smoothing(x: float, p: float, max_value: int) -> float:
    """
    Maps an input value to an output value using a power function with a slow start and fast end.

    The output value increases slowly at the beginning when the input value is small,
    but increases more rapidly as the input value approaches the maximum value of 10.

    Args:
        x (float): The input value to be mapped, in the range of 0 to 10.
        p (float): The exponent of the power function used to map the input value to the output value.
            A larger value of p will result in a faster increase in the output value towards the end of the range.

    Returns:
        float: The mapped output value, in the range of 0 to 10.
    """
    
    ratio = x / max_value
    output = ratio ** p * max_value
    return output if x >= 0 else -abs(output)



already_sent_no_targets=False # Flag to prevent sending the same message over and over again

## Set up this service as a websocket server
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((WS_HOST, WS_PORT))
    s.listen()
    conn, addr = s.accept()
    with conn:
        logging.info(f'Connected by {addr}')
        while True:
            time.sleep(args.delay)
            data = conn.recv(1024)  # Receive data from the client
            if not data:
                break
            
            json_data = json.loads(data.decode('utf-8')) # Decode the received data and parse it as a JSON object
            
            # Check if there are any targets in the frame
            if len(json_data['targets']) > 0:
                logging.debug('Data obtained:' + json.dumps(data.decode('utf-8')))
                already_sent_no_targets=False 
                center_x, center_y =  json_data['heading_vect']
                
                first_target = json_data['targets'][0] # Extract the first target from the targets list
                # vec_delta = first_target['vec_delta'] # Extract the vec_delta data
                id = first_target.get('id', None) # Extract the id data
                
                left, top, right, bottom = first_target['box']
                
                # calculate box coordinates
                box_center_x = (left + right) / 2
                box_center_y = (top + bottom) / 2
                box_width = right - left
                box_height = bottom - top

                # Get movement vector to align gun with center of target
                movement_vector = [box_center_x - center_x, box_center_y - center_y]
                
                # Add padding as a percentage of the original dimensions
                padding_width = box_width * TARGET_PADDING_PERCENTAGE
                padding_height = box_height * TARGET_PADDING_PERCENTAGE

                # Calculate box coordinates
                padded_left = left + padding_width
                padded_right = right - padding_width
                padded_top = top + padding_height
                padded_bottom = bottom - padding_height
                    
                is_on_target = False  
                if padded_top <= center_y <= padded_bottom and padded_left <= center_x <= padded_right:
                    is_on_target=True      

                view_width = json_data['view_dimensions'][0]
                view_height = json_data['view_dimensions'][1]
                
                current_distance_from_the_middle = movement_vector[0]
                max_distance_from_the_middle_left = -(view_width / 2)
                max_distance_from_the_middle_right = view_width / 2
            
                
                predicted_azimuth_angle = map_range(
                    current_distance_from_the_middle,
                    max_distance_from_the_middle_left, 
                    max_distance_from_the_middle_right ,
                    -90 ,
                    90
                )
                azimuth_speed_adjusted = -(predicted_azimuth_angle * float(args.speed))
                smoothed_speed_adjusted_azimuth = slow_start_fast_end_smoothing(azimuth_speed_adjusted, float(args.smoothing) + 1.0, 90)
                
                elevation_speed_adjusted = map_range((view_height / 2) - ((view_height / 2) - abs(movement_vector[1])), 0, view_height / 2, 0 , 10) * float(args.speed)
                smooth_elevation_speed_adjusted = slow_start_fast_end_smoothing(elevation_speed_adjusted, float(args.smoothing) + 1.0, 10)
                
                azimuth_formatted = round(smoothed_speed_adjusted_azimuth, args.azimuth_dp)
                
                controller_state = cached_controller_state = {
                    'azimuth_angle': 0 if abs(movement_vector[0]) <= args.accuracy_threshold else azimuth_formatted,
                    'is_clockwise': movement_vector[1] > 0,
                    'speed': 0 if abs(movement_vector[1]) <= args.accuracy_threshold else round(elevation_speed_adjusted / 2 , args.elevation_dp),
                    'is_firing': is_on_target,
                }
                
                logging.debug("Sending controller state: " + json.dumps(controller_state))
                
                if not args.test:
                    try:
                        requests.post(url, json=controller_state)       
                    except:
                        logging.error("Failed to send controller state to server.")

                    
            else:
                if not already_sent_no_targets and not args.test:
                    ## No targets detected, so stop the gun but hold its current position
                    requests.post(url, json={
                        **cached_controller_state,
                        'speed': 0,
                        'is_firing': False,
                    })      
                    already_sent_no_targets=True 
