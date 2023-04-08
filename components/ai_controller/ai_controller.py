import argparse
import logging
import socket
import json
from threading import Lock, Thread
from typing import Optional
import requests
import time
import traceback
import os
import sys

from concurrent.futures import ThreadPoolExecutor


sys.path.append(os.path.dirname(os.path.abspath(__file__)) + '/..')

from camera_vision.models import CameraVisionDetection
from ai_controller_model import AiController
from nerf_turret_utils.controller_action import ControllerAction
from nerf_turret_utils.logging_utils import map_log_level


parser = argparse.ArgumentParser("AI Controller for the Nerf Turret")

# Networking
parser.add_argument("--udp-port", help="Set the web socket server port to recieve messages from.", default=6565, type=int)
parser.add_argument("--udp-host", help="Set the web socket server hostname to recieve messages from.", default="localhost")
parser.add_argument("--web-port", help="Set the web server server port to send commands too.", default=5565, type=int)
parser.add_argument("--web-host", help="Set the web server server hostname. to send commands too", default="localhost")

# Script arguments
parser.add_argument("--log-level", "-ll" , help="Set the logging level by integer value or string representation.", default=logging.WARNING, type=map_log_level)
parser.add_argument("--delay", "-d", help="Delay to limit the data flow into the websocket server.", default=0.15, type=int)
parser.add_argument("--test", "-t", help="For testing it will not send requests to the driver.", action="store_true")
parser.add_argument("--benchmark", "-b",help="Wether to measure the script performance and output in the logs.", action='store_true', default=False)

# AI Controller arguments
parser.add_argument('--search',  action='store_true', help='If this flag is set the gun will try to find targets if there are none currently in sight', default=False)

# Targets
parser.add_argument("--target-padding", "-p",help="""
                    Set the padding for when the gun will try and shoot relative to the edge of the target in %.
                    The amount of padding around the target bounding box in pixels that the gun will ignore before shooting
                    """, default=10, type=int)
parser.add_argument('--target-type', '-ty', type=lambda x: str(x.lower()), default='person', 
                    help="""
                    The type of object to shoot at. This can be anything available in yolov8 objects but it will default to shoot people, preferably in the face'.
                    """ )
parser.add_argument('--target_ids', nargs='+', type=lambda x: str(x.lower().replace(" ", "_")), 
                    help='List of target ids to track. This will only be valid if a target type of "person" is selected', default=[])


args = parser.parse_args()


if args.target_type != 'face' and len(args.target_ids) > 0 :
    raise argparse.ArgumentTypeError(
        f'You can only track specific targets if the target type is set to \'face\', but it is set to \'{args.target_type}\'')


logging.basicConfig(level=args.log_level)

logging.debug(f"\nArgs: {args}\n")


UDP_HOST = args.udp_host  # IP address of the server
UDP_PORT = args.udp_port  # Port number to listen on

url = f"http://{args.web_host}:{args.web_port}"

logging.info(f'{"Mocking" if args.test else "" } Forwarding controller values to host at {url}')

if args.target_ids:
    logging.info(f'Tracking targets with ids: {args.target_ids}')

# Cache the controller state to prevent sending the same values over and over again
cached_action= ControllerAction(
    x=0,
    y=0,
    is_firing = False  
)

controller = AiController(
    target_padding=args.target_padding,
    target_type=args.target_type,
    search=args.search,
    target_ids=args.target_ids
)

sock: Optional[socket.socket] = None
latest_request = None
lock = Lock()
stop_thread = False

def try_to_bind_to_socket():
    """Try to bind to the socket and accept the connection"""
    global sock
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # sock.settimeout(1)  # Set a timeout of 1 second
    server_address = (UDP_HOST, UDP_PORT)
    logging.info(f"Binding to host {server_address}")
    sock.bind(server_address)

    logging.info(f'Connected by {server_address}')


def handle_request(data, addr):
    print("Handling request")
    object_detections: Optional[CameraVisionDetection] = None
    try:
        object_detections = json.loads(data.decode('utf-8'))
        logging.debug(f"Received detections from Vision: {object_detections}")
        if not object_detections:
            raise ValueError('Object detection failed')
    except json.JSONDecodeError as e:
        logging.error(f"Error decoding JSON: {e}")
        return
    except ValueError as e:
        logging.error(e)
        return

    action = controller.get_action(object_detections)

    logging.debug(f"Action decision of controller: {action.__dict__}")
    global cached_action
    if action == cached_action:
        logging.debug("No new action, skipping request")
        return
    else:
        cached_action = action

    if not args.test:
        logging.debug(f"Sending action to serial driver {url}")
        # Only send requests on new action states
        requests.post(url, json=action.__dict__)     



start_time=None

with ThreadPoolExecutor(max_workers=5) as executor:
    while True:
        print("Listening for request")
        time.sleep(args.delay)
        if args.benchmark:
            start_time = time.time()
        try:
            if not sock:
                try_to_bind_to_socket()
            else:
                print("Getting request")
                # Receive data from a client
                data, addr = sock.recvfrom(1024)  # type: ignore
                print("Got request", data)
                # Submit the received request to the executor for handling
                executor.submit(handle_request, data, addr)

    
        except KeyboardInterrupt as e:
            stop_thread = True
            # On a keyboard interrupt
            requests.post(url, json={
                'x': 0,
                'y': 0,
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
            if start_time and args.benchmark:
                logging.debug("Frame processed in " + str(time.time() - start_time) + " seconds")
            pass
        
