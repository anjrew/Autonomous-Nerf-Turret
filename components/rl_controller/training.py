# Standard library imports
import argparse
import json
import logging
import os
import socket
import sys
import threading
import time
from datetime import datetime
from typing import Callable, Optional
import requests

# Third-party imports
from stable_baselines3 import PPO
from stable_baselines3.common.env_checker import check_env

# Local application imports
file_directory = os.path.dirname(os.path.abspath(__file__))
sys.path.append(file_directory + '/..')
from camera_vision.models import CameraVisionDetections, CameraVisionTarget
from nerf_turret_utils.turret_controller import TurretAction
from turret_env import TurretEnv
from models import TurretObservationSpace
from nerf_turret_utils.logging_utils import map_log_level
from utils import get_priority_target_index


parser = argparse.ArgumentParser("Reinforcement Learning Controller")
parser.add_argument("--log-level", "-ll" , help="Set the logging level by integer value or string representation.", default=logging.WARNING, type=map_log_level)

parser.add_argument("--udp-port", help="Set the web socket server port to recieve messages from.", default=6565, type=int)
parser.add_argument("--udp-host", help="Set the web socket server hostname to recieve messages from.", default="localhost")

parser.add_argument("--web-port", help="Set the web server server port to send commands too.", default=5565, type=int)
parser.add_argument("--web-host", help="Set the web server server hostname. to send commands too", default="localhost")

parser.add_argument("--test", "-t", help="For testing it will not send requests to the driver.", action="store_true")

parser.add_argument("--time-steps", "-ts", help="The amount of training timesteps per learning episode.",  type=int, default=1000)
parser.add_argument("--model-save-frequency", "-msf", help="The amount of training timesteps.", type=int, default=30)

parser.add_argument("--delay", "-d", help="Delay to limit the data flow into the websocket server.", default=0.3, type=float)
parser.add_argument("--benchmark", "-b",help="Wether to measure the script performance and output in the logs.", action='store_true', default=False)
parser.add_argument('--target-type', '-ty', type=lambda x: str(x.lower()), default='person', 
                    help="""
                    The type of object to shoot at. This can be anything available in yolov8 objects but it will default to shoot people, preferably in the face'.
                    """ )

parser.add_argument('--targets', nargs='+', type=lambda x: str(x.lower().replace(" ", "_")), 
                    help='List of target ids to track. This will only be valid if a target type of "person" is selected', default=[])
# parser.add_argument("--web-port", help="Set the web server server port to send commands too.", default=5565, type=int)
# parser.add_argument("--web-host", help="Set the web server server hostname. to send commands too", default="localhost")
# parser.add_argument("--test", "-t", help="For testing it will not send requests to the driver.", action="store_true")

args = parser.parse_args()
logging.basicConfig(level=args.log_level)

logging.debug(f"\nArgs: {args}\n")
url = f"http://{args.web_host}:{args.web_port}"
logging.info(f'{"Mocking" if args.test else "" } Forwarding controller values to host at {url}')

sock: Optional[socket.socket] = None

UDP_HOST = args.udp_host  # IP address of the server
UDP_PORT = args.udp_port  # Port number to listen on

sock: Optional[socket.socket] = None

def try_to_bind_to_socket():
    """Try to bind to the socket and accept the connection"""
    global sock
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_address = (UDP_HOST, UDP_PORT)
    logging.info(f"Binding to host {server_address}")
    sock.bind(server_address)

    logging.info(f'Connected by {server_address}')


NO_TARGET_STATE: TurretObservationSpace = {
    'box': (0,0,0,0),
    "view_dimensions": (0,0),
}
        
current_state = NO_TARGET_STATE

get_current_state = lambda: current_state


def dispatch_action(action: TurretAction) -> None:
    if not args.test: 
        try:
            requests.post(url, json=action)
        except requests.exceptions.ConnectionError as e:
            logging.error(f"Error sending request to {url}: {e}")
     
# Define the environment
env = TurretEnv(get_current_state, dispatch_action)

check_env(env, warn=True)

run_id = datetime.now().strftime('%H%M%S%Y%m%d') # type: ignore

start_time =0

# Define the PPO model
model = PPO('MlpPolicy', env, verbose=2, tensorboard_log=f"{file_directory}/turret_tensorboard/{run_id}")
# Define where the model will be saved
model_directory=f'{file_directory}/turret_models/{run_id}'
if not os.path.exists(model_directory):
    os.makedirs(model_directory)

def run_model_training_process():
    TIME_STEPS = args.time_steps
    
    # Train the agent
    for i in range(args.model_save_frequency):
        model.learn(total_timesteps=TIME_STEPS, reset_num_timesteps=False, progress_bar=True, tb_log_name=f"run_{run_id}-{i}")
        model.save(f"{model_directory}/{TIME_STEPS*i}")


def listen_for_targets(first_target_found_emitter: Callable):
    first_found =  False
    while True:
        time.sleep(args.delay)
        if args.benchmark:
            global start_time
            logging.debug('Benchmarking loop: ' + str(time.time() - start_time) + ' seconds')
            start_time = time.time()
        if not sock:
            try_to_bind_to_socket()
        
        else:
                 
            # Receive data from a client
            data, addr = sock.recvfrom(1024) # type: ignore
            if not data:
                continue
            
            json_data:Optional[CameraVisionDetections] = None
            try:
                json_data = json.loads(data.decode('utf-8'))
            except json.JSONDecodeError as e:
                logging.error(f"Error decoding JSON: {e}")
                continue
            
            if json_data and len(json_data['targets']) > 0:
                target_index = get_priority_target_index(json_data['targets'], args.target_type, args.targets)
                
                if target_index is None:
                    logging.debug(f'No valid target found from type {args.target_type} with ids {args.targets}')
                    # If no valid target was found, then just move onto the next frame
                    continue
                
                target: CameraVisionTarget = json_data['targets'][target_index] # Extract the first target from the targets list
                
                global current_state
                
                current_state = {
                    'box': target['box'],  
                    'view_dimensions': json_data['view_dimensions']
                }
                if not first_found:
                    first_found = True
                    first_target_found_emitter()
            else:
                current_state = NO_TARGET_STATE


# Create threads for both functions
model_training_thread = threading.Thread(target=run_model_training_process)
server_thread = threading.Thread(target=listen_for_targets, args=(lambda: model_training_thread.start(),))

server_thread.start()
