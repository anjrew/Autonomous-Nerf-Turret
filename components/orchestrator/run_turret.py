import subprocess
import os
import logging
from argparse import ArgumentParser
import sys
import asyncio
import sys
import subprocess
import threading
from select_option import select_option

components_directory = os.path.dirname(os.path.abspath(__file__)) + '/..'
sys.path.append(components_directory)

from nerf_turret_utils.args_utils import map_log_level 

parser = ArgumentParser(description="Runs multiple services to make the the shooter work")
parser.add_argument("--log-level", "-ll" , help="Set the logging level by integer value.", default=logging.INFO, type=map_log_level)
parser.add_argument("--delay", "-d" , help="Delay in seconds between starting each successive script.", default=1, type=int)
parser.add_argument("--show-camera", "-c" , help="Show the camera output of what the turret sees.", action='store_true')
args = parser.parse_args()


logging.basicConfig(level=args.log_level)

processes = []

def run_script(script_path: str) -> None:
    """
    Run a Python script in a separate process and print its output to the console.

    :param script_path: The path to the Python script to run.
    """
    process = subprocess.Popen([sys.executable, script_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    processes.append(process)

    while True:
        output = process.stdout.readline() #type: ignore
        if output:
            print(f"{script_path} output: {output.decode().strip()}")
        if process.poll() is not None:
            break


async def main():
    """
    Run multiple Python scripts in parallel using separate threads.
    """
    
    serial_script = 'serial_driver/serial_driver.py'
    ai_controller_script = 'ai_controller/ai_controller.py'
    camera_vision_script = 'camera_vision/camera_vision.py'
    
    run_options = [
        'Aim only for face',
        'Aim only for people',
        'Aim at people but try to hit face',
        'Aim specifically at James Harper and always to hit face'
    ]
    
    script_option = select_option(run_options)
    
    if script_option == 0:
        camera_vision_script += ' --detect-objects False' 
        ai_controller_script += ' --target-type face' 
    
    if script_option == 1:
        camera_vision_script += ' --detect-faces False' 
        ai_controller_script += ' --target-type person' 
        
    if script_option == 3: #aim for James Harper
        camera_vision_script += ' --detect-faces True --id-targets' 
        ai_controller_script += ' --target-type face --targets james_harper' 
    
    if not args.show_camera:
        camera_vision_script += ' --headless'   
    
    threads = []
    script_paths = [
        serial_script,
        ai_controller_script,
        camera_vision_script 
    ]
    # script_paths = [f'{components_directory}/{script_path}' for script_path in script_paths]
    script_paths = [f'python {components_directory}/{script_path}' for script_path in script_paths]

    bash_command = " & ".join(script_paths)
    subprocess.run(bash_command, shell=True)
    # print('Running scripts:')
    # for script_path in script_paths:
        
    #     print(script_path)
    #     thread = threading.Thread(target=run_script, args=(script_path,))
    #     thread.start()
    #     threads.append(thread)

    try:
        for thread in threads:
            thread.join()
            
    except KeyboardInterrupt:
        print("\nTerminating the scripts...")

        # Terminate all running threads
        for thread in threads:
            if thread.is_alive():
                try:
                    thread.terminate()
                except AttributeError:
                    # Python 3.7 and below do not have the terminate() method
                    pass


if __name__ == '__main__':
    
    asyncio.run(main())

    
  