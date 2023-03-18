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

# setup_logger('run_turret', args.log_level)
logging.basicConfig(level=args.log_level, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

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
    for script in script_paths:
        logging.info("Running: " + script)
    
    script_paths = [f'python {components_directory}/{script_path} --log-level {args.log_level}' for script_path in script_paths]

    try:
        bash_command = " & ".join(script_paths)
        subprocess.run(bash_command, shell=True, check=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        terminate_processes(e)


def terminate_processes(e):
    print("\nTerminating the scripts...", e)
    subprocess.run("kill $(ps aux | grep '[p]ython' | grep Autonomous-Nerf-Turret | awk '{print $2}')", shell=True, check=True, capture_output=True)
    raise e

if __name__ == '__main__':
    
    try:
        main()
    except Exception as e:
        terminate_processes(e)
       
    print("Exiting...")
  