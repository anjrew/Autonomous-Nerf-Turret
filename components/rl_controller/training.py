import argparse
import logging
import socket
import json
from typing import Optional, Tuple
import requests
import time
import traceback
import os
import sys
from stable_baselines3 import PPO
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + '/..')
from stable_baselines3.common.env_checker import check_env
from turret_env import TurretEnv
import argparse
from datetime import datetime
from utils import get_priority_target_index


parser = argparse.ArgumentParser("Reinforcement Learning Controller")
parser.add_argument("--udp-port", help="Set the web socket server port to recieve messages from.", default=6565, type=int)
parser.add_argument("--udp-host", help="Set the web socket server hostname to recieve messages from.", default="localhost")
# parser.add_argument("--web-port", help="Set the web server server port to send commands too.", default=5565, type=int)
# parser.add_argument("--web-host", help="Set the web server server hostname. to send commands too", default="localhost")
# parser.add_argument("--test", "-t", help="For testing it will not send requests to the driver.", action="store_true")

args = parser.parse_args()
logging.basicConfig(level=args.log_level)

logging.debug(f"\nArgs: {args}\n")
# url = f"http://{args.web_host}:{args.web_port}"
# logging.info(f'{"Mocking" if args.test else "" } Forwarding controller values to host at {url}')



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
    
    
current_state: Tuple[int, int, int, int, int, int] = (0,0,0,0,0,0)
get_current_state = lambda: current_state
dispatch_action = lambda action: print(f"Dispatching Action: {action}")
# Define the environment
env = TurretEnv(get_current_state, dispatch_action)

check_env(env, warn=True)

run_id = datetime.now().strftime('%H%M%S%Y%m%d') # type: ignore

# Define the PPO model
model = PPO('MlpPolicy', env, verbose=1, tensorboard_log=f"./turret_tensorboard/{run_id}")


while True:
    time.sleep(args.delay)
    if args.benchmark:
        start_time = time.time()
    if not sock:
        try_to_bind_to_socket()
    
    else:
        # Receive data from a client
        data, addr = sock.recvfrom(1024) # type: ignore
        if not data:
            continue
        
        json_data = None
        try:
            json_data = json.loads(data.decode('utf-8'))
        except json.JSONDecodeError as e:
            logging.error(f"Error decoding JSON: {e}")
            continue
        
        if len(json_data['targets']) > 0:
            logging.debug('Data obtained:' + json.dumps(data.decode('utf-8')))
            already_sent_no_targets=False 
            center_x, center_y =  json_data['heading_vect']
            target_index = get_priority_target_index(json_data['targets'], args.target_type, args.targets)
            
            if target_index is None:
                logging.debug(f'No valid target found from type {args.target_type} with ids {args.targets}')
                # If no valid target was found, then just move onto the next frame
                continue
            
            target = json_data['targets'][target_index] # Extract the first target from the targets list
            current_state = (center_x, center_y, target['x'], target['y'], target['width'], target['height'])

# Train the model
model.learn(total_timesteps=10000)

# obs = env.reset()
# n_steps = 10
# for _ in range(n_steps):
#     # Random action
#     action = env.action_space.sample()
#     obs, reward, done, info = env.step(action)
#     if done:
#         obs = env.reset()