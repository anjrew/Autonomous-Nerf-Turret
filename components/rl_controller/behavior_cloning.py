from argparse import Namespace
import argparse
import os
import sys
import time
import types
from typing import Callable, Optional, Sequence, Tuple, TypedDict
import logging
# Standard library imports
import json
import logging
import socket
import threading
import requests
import numpy as np


sys.path.append(os.path.dirname(os.path.abspath(__file__)) + '/..')


from rl_controller.turret_env import TurretEnv, TurretObservationSpace
from nerf_turret_utils.thread_executor import ThreadExecutor
from nerf_turret_utils.turret_controller import TurretAction
from nerf_turret_utils.args_utils import map_log_level
from camera_vision.models import CameraVisionDetection, CameraVisionTarget
import gym
import numpy as np
from stable_baselines3 import PPO
from stable_baselines3.common.evaluation import evaluate_policy

from imitation.algorithms import bc
from imitation.data import rollout

from ai_controller.ai_controller_model import AiController


from imitation.data import types


parser = argparse.ArgumentParser("Reinforcement Learning Controller")
parser.add_argument("--log-level", "-ll" , help="Set the logging level by integer value or string representation.", default=logging.WARNING, type=map_log_level)

parser.add_argument("--udp-port", help="Set the web socket server port to recieve messages from.", default=6565, type=int)
parser.add_argument("--udp-host", help="Set the web socket server hostname to recieve messages from.", default="localhost")

parser.add_argument("--web-port", help="Set the web server server port to send commands too.", default=5565, type=int)
parser.add_argument("--web-host", help="Set the web server server hostname. to send commands too", default="localhost")

parser.add_argument("--test", "-t", help="For testing it will not send requests to the driver.", action="store_true")

parser.add_argument("--time-steps", "-ts", help="The amount of training timesteps per learning episode.",  type=int, default=1000)
parser.add_argument("--model-save-frequency", "-msf", help="The amount of training timesteps.", type=int, default=30)

parser.add_argument("--delay", "-d", help="Delay to limit the data flow into the websocket server.", default=0.1, type=float)

parser.add_argument("--benchmark", "-b",help="Wether to measure the script performance and output in the logs.", action='store_true', default=False)

parser.add_argument("--step-limit", "-sl",help="How many steps of experience to collect from the expert.", default=10_000, type=int)

args = parser.parse_args()

logging.basicConfig(level=args.log_level)
logging.debug(f"\nArgs: {args}\n")
url = f"http://{args.web_host}:{args.web_port}"
logging.info(f'{"Mocking" if args.test else "" } Forwarding controller values to host at {url}')


class TargetAndFrame(TypedDict):
    target: CameraVisionTarget
    view_dimensions: Tuple[int,int]


NO_TARGET_STATE: TargetAndFrame = {
    'view_dimensions': (0,0),
    'target':{
         'box': (0,0,0,0),
         'id': None,
         'mask': None,
         'type':'person'
    }
}  

current_state:TargetAndFrame = NO_TARGET_STATE


def get_current_state()-> TurretObservationSpace:
    global current_state
    logging.debug('Processing current state: ' + str(current_state['target']['box']) + ' view dimensions: ' + str(current_state['view_dimensions']) + ' to the environment.')
    return {
        "box": current_state['target']['box'],
        "view_dimensions": current_state['view_dimensions']
    }


def set_current_state(x: TargetAndFrame)-> None:
    global current_state
    current_state = x


def try_to_bind_to_socket() -> socket.socket:
    """Try to bind to the socket and accept the connection"""
    
    UDP_HOST = args.udp_host  # IP address of the server
    UDP_PORT = args.udp_port  # Port number to listen on
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_address = (UDP_HOST, UDP_PORT)
    logging.info(f"Binding to host {server_address}")
    sock.bind(server_address)

    logging.info(f'Connected by {server_address}')
    return sock


def listen_for_targets(
    controller: AiController, 
    first_target_found_emitter: Callable, 
    set_current_state: Callable[[TargetAndFrame], None],
    stop_event: threading.Event
) -> None:
    """Listen for targets and store them in a global variable ready for the controller to use."""
    sock: Optional[socket.socket] = None
    
    first_found =  False
    while not stop_event.is_set():
        time.sleep(args.delay)
        if args.benchmark:
            global start_time
            logging.debug('Benchmarking loop: ' + str(time.time() - start_time) + ' seconds')
            start_time = time.time()
        if not sock:
            try:
                sock = try_to_bind_to_socket()
            except Exception as e:
                logging.error(f"Error binding to socket: {e}")
                continue
        else:
                 
            # Receive data from a client
            data, _ = sock.recvfrom(1024) # type: ignore
            if not data:
                continue
            
            detection_data:Optional[CameraVisionDetection] = None
            try:
                detection_data = json.loads(data.decode('utf-8'))
            except json.JSONDecodeError as e:
                logging.error(f"Error decoding JSON: {e}")
                continue
            
            if detection_data and len(detection_data['targets']) > 0:
                target_index = controller.get_priority_target_index(detection_data['targets'])
                
                if target_index is None:
                    logging.debug(f'No valid target found')
                    # If no valid target was found, then just move onto the next frame
                    continue
                
                target: CameraVisionTarget = detection_data['targets'][target_index] # Extract the first target from the targets list
                
                set_current_state({
                    'target': target,  
                    'view_dimensions': detection_data['view_dimensions']
                })
                if not first_found:
                    first_found = True
                    first_target_found_emitter()
            else:
                set_current_state(NO_TARGET_STATE)


def create_expert() -> AiController:
    """Create the expert which will train the policy."""
    args =  Namespace(
        target_padding=10, 
        search=True,
        target_type='person', 
        targets=[], 
        accuracy_threshold_x=1, 
        accuracy_threshold_y=20,
        x_smoothing=1, 
        max_azimuth_angle=10, 
        azimuth_dp=1,
        x_speed_max=10, 
        max_elevation_speed=10,
        elevation_dp=0,
        y_speed=1,
    )
    logging.debug(f"Expert created with args: {args}")
    return AiController(args.__dict__)


def sample_expert_transitions(expert: AiController, env: TurretEnv, step_limit: int) -> types.Transitions:   
    """Sample expert transitions using the expert policy to gain experience."""
    
    # step_limit = 10_000
    

    logging.info(f"Sampling expert transitions.")

    obs: np.ndarray = np.array([env.NO_TARGET_STATE])
    acts: np.ndarray = np.empty((0,4))
    infos: np.ndarray = np.empty((0,1))
    terminal: bool = False
    rews: np.ndarray = np.empty((0,))
    
    for i in range(step_limit):
        logging.info(f'Sampling expert transitions {i}')
        
        mapped_action = np.array([0,0,0,0])
        
        has_target = current_state['target']['box'][:4] != env.NO_TARGET_STATE[:4]
        logging.debug(f"Expert has target: {has_target}")     
        
        if has_target:
            action = expert.get_action_for_target(current_state['target'], current_state['view_dimensions'])
            logging.debug(f"Expert output action. {str(action)} for target {str(current_state)}")     
            mapped_action = env.map_action_object_to_vector(action)
             
        result = env.step(mapped_action)
        observation, reward, done, info  = result
        
        obs =  np.vstack((obs, observation))
        acts =  np.vstack((acts, mapped_action))
        rews = np.append(rews, reward)
        infos = np.vstack((infos, info))
        terminal = done
        
    episode = types.TrajectoryWithRew(
        obs=obs,
        acts=acts,
        infos=infos,
        terminal=terminal,
        rews=rews,
    )
    roll_outs: Sequence[types.TrajectoryWithRew] = [episode]
    
    return rollout.flatten_trajectories(roll_outs)
    
    
def eval_func(env, bc_trainer, is_after = False):
    logging.info("Evaluating policy")
    reward, _ = evaluate_policy(
        bc_trainer.policy,  # type: ignore[arg-type]
        env,
        n_eval_episodes=3,
        render=True,
    )
    print(f"Reward { 'after' if is_after else 'before'} training: {reward}")


def create_env() -> gym.Env:   
    """Create the turret environment"""      
    def dispatch_action(action: TurretAction) -> None:
        logging.debug('Dispatching action: ' + str(action))
        if not args.test: 
            try:
                requests.post(url, json=action)
            except requests.exceptions.ConnectionError as e:
                logging.error(f"ConnectionError sending request to serial driver at {url}: {e}")
            except Exception as e:
                logging.error(f"Unknown Error sending request to serial driver at {url}: {e}")
    
    env = TurretEnv(get_current_state, dispatch_action)
    # Wrap the environment with the Monitor class
    # env = Monitor(env, filename="monitor_log.csv")
    return env


expert: AiController = create_expert()

environment = create_env()

stop_event = threading.Event()

# Create threads for both functions
experience_episode_gathering = ThreadExecutor[types.Transitions](target=sample_expert_transitions, args=(expert, environment, args.step_limit))
server_thread = threading.Thread(
    target=listen_for_targets, 
    args=(expert , lambda: experience_episode_gathering.start(), lambda x: set_current_state(x), stop_event)
)

server_thread.start()

while not experience_episode_gathering.is_alive():
    logging.info('Waiting for experience gathering thread to start')
    time.sleep(1)

logging.info('First target found, waiting for experience gathering thread to finish')
experience_episode_gathering.join()
logging.info('Finished collecting experience')
# Set the stop event to stop the thread
stop_event.set()

rng = np.random.default_rng(0)

bc_trainer = bc.BC(
    observation_space=environment.observation_space,
    action_space=environment.action_space,
    demonstrations=experience_episode_gathering.result, # type: ignore
    rng=rng,
)

# Stop the environment running
environment.done = True # type: ignore

logging.info("Training a policy using Behavior Cloning")

eval_func(environment, bc_trainer, False)

bc_trainer.train(n_epochs=1)

eval_func(environment, bc_trainer , True)


# def run_model_training_process():
#     TIME_STEPS = args.time_steps
    
#     # Train the agent
#     for i in range(args.model_save_frequency):
#         model.learn(total_timesteps=TIME_STEPS, reset_num_timesteps=False, progress_bar=True, tb_log_name=f"run_{run_id}-{i}")
#         model.save(f"{model_directory}/{TIME_STEPS*i}")
        




