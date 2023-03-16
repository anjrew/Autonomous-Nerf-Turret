import multiprocessing
import subprocess
import os
import logging
from argparse import ArgumentParser
import sys
import keyboard


# TODO: This entire script is a mess. It needs to be cleaned up and made more robust and is not actually working right now.
components_directory = os.path.dirname(os.path.abspath(__file__)) + '/..'
sys.path.append(components_directory)

from nerf_turret_utils.args_utils import map_log_level 

parser = ArgumentParser(description="Runs multiple services to make the the shooter work")
parser.add_argument("--log-level", "-ll" , help="Set the logging level by integer value.", default=logging.INFO, type=map_log_level)
parser.add_argument("--delay", "-d" , help="Delay in seconds between starting each successive script.", default=1, type=int)
args = parser.parse_args()


logging.basicConfig(level=args.log_level)


# def run_script(script_path):
#     print('Running script: ', script_path)
#     # subprocess.run(['python', script_path])
#     subprocess.run([script_path])

def run_script(script_path):
    subprocess.Popen([sys.executable, script_path])


if __name__ == '__main__':
    script_paths = [
        'serial_driver/serial_driver.py', 
        'ai_controller/ai_controller.py', 
        'camera_vision/face_tracking.py'
    ]

    
    processes = []

    for script_path in script_paths:
        script_path = f'{components_directory}/{script_path}'
        if not os.path.exists(script_path):
            raise FileNotFoundError(f"Script not found: {script_path}")

        process = multiprocessing.Process(target=run_script, args=(script_path,))
        processes.append(process)

    # # Start all processes
    # for process in processes:
    #     process.start()

    # # Wait for all processes to finish
    # for process in processes:
    #     process.join()
    print("Press 'q' to terminate the subprocesses...")

    # Wait for the 'q' key press
    keyboard.wait('q')

    # Terminate the subprocesses
    for process in processes:
        process.terminate()  # Use process.kill() if you want to forcefully kill the process

    # Wait for all processes to finish
    for process in processes:
        process.wait()

    print("Subprocesses terminated.")