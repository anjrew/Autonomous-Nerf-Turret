import subprocess
import os
import logging
from argparse import ArgumentParser
import sys
import subprocess
import threading
import time
import subprocess
from select_option import select_option

components_directory = os.path.dirname(os.path.abspath(__file__)) + '/..'
sys.path.append(components_directory)

# from nerf_turret_utils.logging_utils import setup_logger
from nerf_turret_utils.args_utils import map_log_level 
 
parser = ArgumentParser(description="Runs multiple services to make the the shooter work")
parser.add_argument("--log-level", "-ll" , help="Set the logging level by integer value.", default=logging.INFO, type=map_log_level)
parser.add_argument("--delay", "-d" , help="Delay in seconds between starting each successive script.", default=1, type=int)
parser.add_argument("--show-camera", "-c" , help="Show the camera output of what the turret sees.", action='store_true')
args = parser.parse_args()

logging.basicConfig(level=args.log_level)
# setup_logger('run_turret', args.log_level)

logging.debug("Starting run_turret.py wih args: " + str(args))

def read_output(process, process_name):
    while True:
        line = process.stdout.readline()
        if line:
            print(f'{process_name}: {line.decode().rstrip()}')

def main():
    """
    Run multiple Python scripts in parallel using separate threads.
    """

    serial_script = 'serial_driver/serial_driver.py'
    # ai_controller_script = 'ai_controller/ai_controller.py --search'
    controller_script = 'ai_controller/ai_controller.py'
    
    camera_vision_script = 'camera_vision/camera_vision.py'

    run_options = [
        'Aim only for face',
        'Aim only for people',
        'Aim at people but try to hit face',
        'Aim specifically at James Harper and always to hit face',
        'Use gaming controller'
    ]

    script_option_idx = select_option(run_options)
    
    logging.info(f"Running mode: {run_options[script_option_idx]}")

    if script_option_idx == 0: # aim for face
        camera_vision_script += ' --detect-objects False' 
        controller_script += ' --target-type face' 

    if script_option_idx == 1: # aim for people
        camera_vision_script += ' --detect-faces False' 
        controller_script += ' --target-type person' 

    if script_option_idx == 3: #aim for James Harper
        camera_vision_script += ' --detect-faces True --id-targets' 
        controller_script += ' --target-type face --target_ids james_harper' 
        
    if script_option_idx == 4: # use controller
        camera_vision_script += ' --detect-objects False  --detect-faces False -t' # disable all object detection for better performance 
        controller_script = 'game_controller/game_controller.py'


    camera_option_idx = select_option(['Run without camera view ', 'Show camera view', 'Show camera view and Record' ])
    
    if not args.show_camera and not camera_option_idx:
        camera_vision_script += ' --headless'   
    
    if camera_option_idx == 2:
        camera_vision_script += ' --record'

    script_paths = [
        serial_script,
        controller_script,
        camera_vision_script
    ]
    
    processes = []
    try:
            
        for script in script_paths:
            command = f'python {components_directory}/{script} --log-level {args.log_level}'
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
            process_name = f'{script.split("/")[0]}'
            t = threading.Thread(target=read_output, args=(process, process_name))
            t.daemon = True
            t.start()
            processes.append((process, t))

        while True:
            # Main process is also running indefinitely, press Ctrl+C to stop.
            time.sleep(1)
                

                
                
    
    except Exception as e:
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
  