import multiprocessing
import subprocess
import os
import logging
import time
from argparse import ArgumentParser
import sys

# TODO: This entire script is a mess. It needs to be cleaned up and made more robust and is not actually working right now.
components_directory = os.path.dirname(os.path.abspath(__file__)) + '/..'
sys.path.append(components_directory)

from nerf_turret_utils.args_utils import map_log_level 

parser = ArgumentParser(description="Runs multiple services to make the the shooter work")
parser.add_argument("--log-level", "-ll" , help="Set the logging level by integer value.", default=logging.INFO, type=map_log_level)
parser.add_argument("--delay", "-d" , help="Delay in seconds between starting each successive script.", default=1, type=int)
args = parser.parse_args()


logging.basicConfig(level=args.log_level)


def run_script(script_path):
    print('Running script: ', script_path)
    # subprocess.run(['python', script_path])
    subprocess.run([script_path])

if __name__ == '__main__':
    script_paths = [
        'serial_driver/serial_driver.py', 
        'ai_controller/ai_controller.py', 
        'camera_vision/face_tracking.py'
    ]

    processes = []
    for script_path in script_paths:
        full_path = f'python {components_directory}/{script_path}'
        print('full_path: ', full_path)
        process = multiprocessing.Process(target=run_script, args=(script_path))
        process.start()
        # processes.append(process)
        # time.sleep(args.delay)

    # for process in processes:
    #     process.join()