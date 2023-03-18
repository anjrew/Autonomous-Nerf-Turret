import subprocess
import os
import logging
from argparse import ArgumentParser
import sys
import sys
import subprocess
from select_option import select_option

components_directory = os.path.dirname(os.path.abspath(__file__)) + '/..'
sys.path.append(components_directory)

from nerf_turret_utils.logging_utils import setup_logger
from nerf_turret_utils.args_utils import map_log_level 
 
parser = ArgumentParser(description="Runs multiple services to make the the shooter work")
parser.add_argument("--log-level", "-ll" , help="Set the logging level by integer value.", default=logging.INFO, type=map_log_level)
parser.add_argument("--delay", "-d" , help="Delay in seconds between starting each successive script.", default=1, type=int)
parser.add_argument("--show-camera", "-c" , help="Show the camera output of what the turret sees.", action='store_true')
args = parser.parse_args()

setup_logger('run_turret', args.log_level)

def main():
    """
    Run multiple Python scripts in parallel using separate threads.
    """

    serial_script = 'serial_driver/serial_driver.py'
    # ai_controller_script = 'ai_controller/ai_controller.py --search'
    ai_controller_script = 'ai_controller/ai_controller.py'
    camera_vision_script = 'camera_vision/camera_vision.py'

    run_options = [
        'Aim only for face',
        'Aim only for people',
        'Aim at people but try to hit face',
        'Aim specifically at James Harper and always to hit face'
    ]

    script_option_idx = select_option(run_options)
    
    logging.info(f"Running mode: {run_options[script_option_idx]}")

    if script_option_idx == 0:
        camera_vision_script += ' --detect-objects False' 
        ai_controller_script += ' --target-type face' 

    if script_option_idx == 1:
        camera_vision_script += ' --detect-faces False' 
        ai_controller_script += ' --target-type person' 

    if script_option_idx == 3: #aim for James Harper
        camera_vision_script += ' --detect-faces True --id-targets' 
        ai_controller_script += ' --target-type face --targets james_harper' 

    if not args.show_camera:
        camera_vision_script += ' --headless'   

    script_paths = [
        serial_script,
        ai_controller_script,
        camera_vision_script 
    ]
    
    # script_paths = [ for script_path in script_paths]

    processes = []
    try:
        for script in script_paths:
            command = f'python {components_directory}/{script} --log-level {args.log_level}'
            logging.debug("Running command: " + command)
            process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            processes.append(process)

        for process in processes:
            stdout, stderr = process.communicate()
            if stdout:
                # We print all output because the log level will be set in the child processes
                print(stdout.decode("utf-8"))
            if stderr:
                raise subprocess.CalledProcessError(process.returncode, f"Process {process.pid} failed: {stderr.decode('utf-8')}")

    
    except subprocess.CalledProcessError as e:
        print(e)
        for process in processes:
            logging.warning(f"Terminating process with PID {process.pid}")
            try:
                process.terminate()
            except Exception as exc:
                print(f"Error terminating process with PID {process.pid}: {exc}")
        exit()
   
    

if __name__ == '__main__':
    
    try:
        main()
    except Exception as e:
        logging.error('Unknown Error')
        print(e)
       
    print("Exiting...")
  