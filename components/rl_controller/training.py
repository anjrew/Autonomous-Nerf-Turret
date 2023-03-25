import argparse
import logging
import socket
import json
from typing import Tuple
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



parser = argparse.ArgumentParser("Reinforcement Learning Controller")
parser.add_argument("--udp-port", help="Set the web socket server port to recieve messages from.", default=6565, type=int)
parser.add_argument("--udp-host", help="Set the web socket server hostname to recieve messages from.", default="localhost")
parser.add_argument("--web-port", help="Set the web server server port to send commands too.", default=5565, type=int)
parser.add_argument("--web-host", help="Set the web server server hostname. to send commands too", default="localhost")
parser.add_argument("--test", "-t", help="For testing it will not send requests to the driver.", action="store_true")

args = parser.parse_args()


url = f"http://{args.web_host}:{args.web_port}"

logging.info(f'{"Mocking" if args.test else "" } Forwarding controller values to host at {url}')


current_state: Tuple[int, int, int, int, int, int] = (0,0,0,0,0,0)
get_current_state = lambda: current_state
dispatch_action = lambda action: print(f"Dispatching Action: {action}")
# Define the environment
env = TurretEnv(get_current_state, dispatch_action)

check_env(env, warn=True)

run_id = datetime.now().strftime('%H%M%S%Y%m%d') # type: ignore

# Define the PPO model
model = PPO('MlpPolicy', env, verbose=1, tensorboard_log=f"./turret_tensorboard/{run_id}")

# Train the model
model.learn(total_timesteps=10000)

obs = env.reset()
n_steps = 10
for _ in range(n_steps):
    # Random action
    action = env.action_space.sample()
    obs, reward, done, info = env.step(action)
    if done:
        obs = env.reset()