import argparse
import logging
import socket
import json
from typing import Optional
import requests
import time
import traceback
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)) + '/..')

from camera_vision.models import CameraVisionDetection
from ai_controller_model import AiController
from nerf_turret_utils.turret_controller import TurretAction
from nerf_turret_utils.logging_utils import map_log_level
from nerf_turret_utils.number_utils import assert_in_int_range


parser = argparse.ArgumentParser("AI Controller for the Nerf Turret")
parser.add_argument("--udp-port", help="Set the web socket server port to recieve messages from.", default=6565, type=int)
parser.add_argument("--udp-host", help="Set the web socket server hostname to recieve messages from.", default="localhost")
parser.add_argument("--web-port", help="Set the web server server port to send commands too.", default=5565, type=int)
parser.add_argument("--web-host", help="Set the web server server hostname. to send commands too", default="localhost")
parser.add_argument("--log-level", "-ll" , help="Set the logging level by integer value or string representation.", default=logging.WARNING, type=map_log_level)
parser.add_argument("--azimuth-dp", help="Set how many decimal places the azimuth is taken too.", default=2, type=int)
parser.add_argument("--elevation-dp", help="Set how many decimal places the elevation is taken too.", default=0, type=int)
parser.add_argument("--delay", "-d", help="Delay to limit the data flow into the websocket server.", default=0, type=int)
parser.add_argument("--test", "-t", help="For testing it will not send requests to the driver.", action="store_true")
parser.add_argument("--x-speed", "-xs", help="Set the limit for the the azimuth speed", default=30, type=int)
parser.add_argument("--x-smoothing", "-smx", help="The amount of smoothing factor for speed to optimal position on the azimuth angle", default=1, type=int)
parser.add_argument("--max-azimuth-angle", "-ma", help="The maximum angle that the turret will try to turn in one step on the azimuth plane", default=55, type=int)
parser.add_argument("--y-speed", "-ys", help="Set the factor to multiply the elevation speed", default=2, type=int)
parser.add_argument("--y-smoothing", "-smy", help="The amount of smoothing factor for speed to optimal position on the elevation angle", default=1, type=int)
parser.add_argument("--max-elevation-speed", "-mes", 
                    help="The maximum speed at which the elevation of the gun angle can change as an integrer value between [1-10]", 
                    default=10, 
                    type=lambda x: assert_in_int_range(int(x), 1, 10), ) # type: ignore

parser.add_argument("--benchmark", "-b",help="Wether to measure the script performance and output in the logs.", action='store_true', default=False)

parser.add_argument('--search',  action='store_true', help='If this flag is set the gun will try to find targets if there are none currently in sight', default=False)

parser.add_argument("--target-padding", "-p",help="""
                    Set the padding for when the gun will try and shoot relative to the edge of the target in %.
                    The amount of padding around the target bounding box in pixels that the gun will ignore before shooting
                    """, default=10, type=int)

parser.add_argument('--accuracy-threshold-x', '-atx', type=int, default=1, 
                    help="""
                    The threshold of how accurate the gun will try to get the target in the center of the crosshair in pixels horizontally.
                    """ )

parser.add_argument('--accuracy-threshold-y', '-aty', type=int, default=30, 
                    help="""
                    The threshold of how accurate the gun will try to get the target in the center of the crosshair in pixels vertically.
                    """ )

parser.add_argument('--target-type', '-ty', type=lambda x: str(x.lower()), default='person', 
                    help="""
                    The type of object to shoot at. This can be anything available in yolov8 objects but it will default to shoot people, preferably in the face'.
                    """ )

parser.add_argument('--targets', nargs='+', type=lambda x: str(x.lower().replace(" ", "_")), 
                    help='List of target ids to track. This will only be valid if a target type of "person" is selected', default=[])


# TODO: Implement this feature
# parser.add_argument('--vert-offset', '-v', type=int, default=5, 
#                     help="""
#                     The percentage of vertical offset the gun will aim for from the center of the crosshair in negative correlation to the size of the target box so gravity is taken into account. 
#                     This means that the smaller the target the further it must be form the gun and therefore the higher the gun will aim.
#                     """ )


args = parser.parse_args()


if args.target_type != 'face' and len(args.targets) > 0 :
    raise argparse.ArgumentTypeError(
        f'You can only track specific targets if the target type is set to \'face\', but it is set to \'{args.target_type}\'')


logging.basicConfig(level=args.log_level)

logging.debug(f"\nArgs: {args}\n")

TARGET_PADDING_PERCENTAGE = args.target_padding/100

UDP_HOST = args.udp_host  # IP address of the server
UDP_PORT = args.udp_port  # Port number to listen on

url = f"http://{args.web_host}:{args.web_port}"

logging.info(f'{"Mocking" if args.test else "" } Forwarding controller values to host at {url}')

if args.targets:
    logging.info(f'Tracking targets with ids: {args.targets}')

# Cache the controller state to prevent sending the same values over and over again
cached_action: TurretAction =  {
    'azimuth_angle': 0, # The angle of the gun in the horizontal plane adjustment
    'is_clockwise': False,
    'speed': 0,
    'is_firing': False,
} 

sock: Optional[socket.socket] = None
controller = AiController(args)

    
def try_to_bind_to_socket():
    """Try to bind to the socket and accept the connection"""
    global sock
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_address = (UDP_HOST, UDP_PORT)
    logging.info(f"Binding to host {server_address}")
    sock.bind(server_address)

    logging.info(f'Connected by {server_address}')


start_time=None

while True:
    time.sleep(args.delay)
    if args.benchmark:
        start_time = time.time()
    try:
        if not sock:
            try_to_bind_to_socket()
        
        else:
    
             # Receive data from a client
            data, addr = sock.recvfrom(1024) # type: ignore
            if not data:
                continue
            
            object_detections:Optional[CameraVisionDetection] = None
            try:
                object_detections = json.loads(data.decode('utf-8'))
                if not object_detections:
                    raise  ValueError('Object detection failed')
            except json.JSONDecodeError as e:
                logging.error(f"Error decoding JSON: {e}")
                continue
            except ValueError as e:
                logging.error(e)
                continue
            
            action = controller.get_action(object_detections)
            
            if not args.test and action != cached_action:
                # Only send requests on new action states    
                requests.post(url, json=action)      
            
    
    except KeyboardInterrupt as e:
        # On a keyboard interrupt
        requests.post(url, json={
            'azimuth_angle': 0,
            'speed': 0,
            'is_firing': False,
        }) 
        logging.debug("Sending request to stop turret ")
        raise e 
    except BrokenPipeError as e:
        logging.error("Socket pipe broken. Retrying in 5 seconds...")
        sock = None
        time.sleep(5)
        pass 
    except ConnectionResetError as e:
        logging.error("Socket connection lost. Retrying in 5 seconds...")
        sock = None
        time.sleep(5)
        pass
    except ConnectionRefusedError as e:
        logging.error("Socket connection refused. Retrying in 5 seconds...")
        sock = None
        time.sleep(5)
        pass
    except Exception as e:
        logging.error("An unknown error occurred: " + str(e) + ". Retrying in 5 seconds...") 
        traceback.print_exc()
        sock = None
        time.sleep(5)
        pass
    finally:
        if start_time and  args.benchmark:
            logging.debug("Frame processed in " + str(time.time() - start_time) + " seconds")
        pass
    
