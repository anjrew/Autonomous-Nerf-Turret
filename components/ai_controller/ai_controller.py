import argparse
import logging
import socket
import json
from typing import Union
import requests
import time

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
parser.add_argument("--azimuth-dp", help="Set how many decimal places the azimuth is taken too.", default=0, type=int)
parser.add_argument("--elevation-dp", help="Set how many decimal places the elevation is taken too.", default=0, type=int)


parser.add_argument("--target-padding", "-p",help="""
                    Set the padding for when the gun will try and shoot relative to the edge of the target in %.
                    The amount of padding around the target bounding box in pixels that the gun will ignore before shooting
                    """, default=20, type=int)

# parser.add_argument('--center-threshold', '-t', type=int, default=5, 
#                     help="""
#                     The threshold of how accurate the gun will try to get the target in the center of the crosshair in pixels.
#                     """ )

# parser.add_argument('--vert-offset', '-v', type=int, default=5, 
#                     help="""
#                     The vertical offset the gun will aim for from the center of the crosshair in pixels so gravity is taken into account.
#                     """ )


args = parser.parse_args()

logging.basicConfig(level=args.log_level)

TARGET_PADDING_PERCENTAGE = args.target_padding/100
WS_HOST = args.ws_host  # IP address of the server
WS_PORT = args.ws_port  # Port number to listen on

url = f"http://{args.host}:{args.port}"
logging.info(f'Forwarding controller values to host at {url}')

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

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((WS_HOST, WS_PORT))
    s.listen()
    conn, addr = s.accept()
    with conn:
        logging.info('Connected by', addr)
        while True:
            data = conn.recv(1024)  # Receive data from the client
            if not data:
                break
            
            json_data = json.loads(data.decode('utf-8')) # Decode the received data and parse it as a JSON object
            
            center_x, center_y =  json_data['heading_vect']
            
            if len(json_data['targets']) > 0:
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
                controller_state = {
                    'azimuth_angle': round(map_range((view_width/2) + movement_vector[0], 0, view_width ,0 , 180), args.azimuth_dp),
                    'is_clockwise': movement_vector[0] > 0,
                    'speed': round(map_range((view_height / 2) - ((view_height / 2) - abs(movement_vector[1])), 0, view_height / 2, 0 , 10), args.elevation_dp),
                    'is_firing': is_on_target,
                }
                
                if logging.getLogger().isEnabledFor(logging.DEBUG):
                    print("Sending controller state:", controller_state)
                    
                try:
                    requests.post(url, json=controller_state)       
                except:
                    logging.error("Failed to send controller state to server.")
                    time.sleep(3)