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
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + '/..')

from nerf_turret_utils.logging_utils import map_log_level
from nerf_turret_utils.image_utils import get_frame_box_dimensions_delta
from nerf_turret_utils.number_utils import map_range
from ai_controller_utils import assert_in_int_range, slow_start_fast_end_smoothing, get_priority_target_index, get_elevation_speed, get_elevation_clockwise
from pid_controller import PIDController
from tuning_ui import TuningState, start_tuning_ui


parser = argparse.ArgumentParser("AI Controller for the Nerf Turret")
parser.add_argument("--ws-port", help="Set the web socket server port to recieve messages from.", default=6565, type=int)
parser.add_argument("--ws-host", help="Set the web socket server hostname to recieve messages from.", default="localhost")
parser.add_argument("--port", help="Set the web server server port to send commands too.", default=5565, type=int)
parser.add_argument("--host", help="Set the web server server hostname. to send commands too", default="localhost")
parser.add_argument("--log-level", "-ll" , help="Set the logging level by integer value or string representation.", default=logging.WARNING, type=map_log_level)
parser.add_argument("--azimuth-dp", help="Set how many decimal places the azimuth is taken too.", default=2, type=int)
parser.add_argument("--elevation-dp", help="Set how many decimal places the elevation is taken too.", default=0, type=int)
parser.add_argument("--delay", "-d", help="Delay to limit the data flow into the websocket server.", default=0, type=int)
parser.add_argument("--test", "-t", help="For testing it will not send requests to the driver.", action="store_true")
parser.add_argument("--x-speed", "-xs", help="Set the limit for the the azimuth speed", default=30, type=int)
parser.add_argument("--x-smoothing", "-smx", help="The amount of smoothing factor for speed to optimal position on the azimuth angle", default=1, type=int)
parser.add_argument("--max-azimuth-angle", "-ma", help="The maximum angle that the turret will try to turn in one step on the azimuth plane", default=55, type=int)
parser.add_argument("--y-speed", "-ys", help="Set the factor to multiply the elevation speed", default=2, type=int)
parser.add_argument("--y-smoothing", "-smy", help="The amount of smoothing factor for speed to optimal position on the elevation angle", default=1, type=int)
parser.add_argument("--max-elevation-speed", "-mes", 
                    help="The maximum speed at which the elevation of the gun angle can change as an integrer value between [1-10]", 
                    default=10, 
                    type=lambda x: assert_in_int_range(int(x), 1, 10), ) # type: ignore

parser.add_argument("--benchmark", "-b",help="Wether to measure the script performance and output in the logs.", action='store_true', default=False)


parser.add_argument('--targets', nargs='+', type=lambda x: str(x.lower().replace(" ", "_")), 
                    help='List of target ids to track. This will only be valid if a target type of "person" is selected', default=[])

parser.add_argument('--search',  action='store_true', help='If this flag is set the gun will try to find targets if there are none currently in sight', default=False)

parser.add_argument("--target-padding", "-p",help="""
                    Set the padding for when the gun will try and shoot relative to the edge of the target in %.
                    The amount of padding around the target bounding box in pixels that the gun will ignore before shooting
                    """, default=10, type=int)

parser.add_argument('--accuracy-threshold-x', '-atx', type=int, default=1, 
                    help="""
                    The threshold of how accurate the gun will try to get the target in the center of the crosshair in pixels horizontally.
                    """ )

parser.add_argument('--accuracy-threshold-y', '-aty', type=int, default=30, 
                    help="""
                    The threshold of how accurate the gun will try to get the target in the center of the crosshair in pixels vertically.
                    """ )

parser.add_argument('--target-type', '-ty', type=lambda x: str(x.lower()), default='person', 
                    help="""
                    The type of object to shoot at. This can be anything available in yolov8 objects but it will default to shoot people, preferably in the face'.
                    """ )

parser.add_argument('--no-pid', action='store_true',
                    help='Fall back to the legacy heuristic aiming instead of the PID controllers.')
parser.add_argument('--ui-port', type=int, default=8081,
                    help='Port for the PID tuning web UI. Set to 0 to disable the UI.')
parser.add_argument('--az-kp', type=float, default=0.10, help='Azimuth PID proportional gain.')
parser.add_argument('--az-ki', type=float, default=0.02, help='Azimuth PID integral gain.')
parser.add_argument('--az-kd', type=float, default=0.05, help='Azimuth PID derivative gain.')
parser.add_argument('--el-kp', type=float, default=0.02, help='Elevation PID proportional gain.')
parser.add_argument('--el-ki', type=float, default=0.005, help='Elevation PID integral gain.')
parser.add_argument('--el-kd', type=float, default=0.01, help='Elevation PID derivative gain.')



# TODO: Implement this feature
# parser.add_argument('--vert-offset', '-v', type=int, default=5, 
#                     help="""
#                     The percentage of vertical offset the gun will aim for from the center of the crosshair in negative correlation to the size of the target box so gravity is taken into account. 
#                     This means that the smaller the target the further it must be form the gun and therefore the higher the gun will aim.
#                     """ )


args = parser.parse_args()



if args.target_type != 'face' and len(args.targets) > 0 :
    raise argparse.ArgumentTypeError(
        f'You can only track specific targets if the target type is set to \'face\', but it is set to \'{args.target_type}\'')


logging.basicConfig(level=args.log_level)

logging.debug(f"\nArgs: {args}\n")

TARGET_PADDING_PERCENTAGE = args.target_padding/100

# Live-tunable PID gains (sliders in the tuning UI apply per frame) and the
# per-axis controllers. Output limits mirror the legacy clamps.
tuning_state = TuningState({
    'az': {'kp': args.az_kp, 'ki': args.az_ki, 'kd': args.az_kd},
    'el': {'kp': args.el_kp, 'ki': args.el_ki, 'kd': args.el_kd},
})
azimuth_pid = PIDController(
    kp=args.az_kp, ki=args.az_ki, kd=args.az_kd,
    output_limits=(-args.max_azimuth_angle, args.max_azimuth_angle),
)
el_pid = PIDController(
    kp=args.el_kp, ki=args.el_ki, kd=args.el_kd,
    output_limits=(0, args.max_elevation_speed * args.y_speed / 2),
)
if args.ui_port:
    ui_server = start_tuning_ui(tuning_state, args.ui_port)
    logging.info(f'PID tuning UI on http://0.0.0.0:{args.ui_port}')
last_frame_time = time.monotonic()
WS_HOST = args.ws_host  # IP address of the server
WS_PORT = args.ws_port  # Port number to listen on


url = f"http://{args.host}:{args.port}"

logging.info(f'{"Mocking" if args.test else "" } Forwarding controller values to host at {url}')

if args.targets:
    logging.info(f'Tracking targets with ids: {args.targets}')

# Cache the controller state to prevent sending the same values over and over again
cached_controller_state ={
    'azimuth_angle': 0, # The angle of the gun in the horizontal plane adjustment
    'is_clockwise': False,
    'speed': 0,
    'is_firing': False,
} 

already_sent_no_targets=False # Flag to prevent sending the same message over and over again
connection = None
sock = None

search = {
    'clockwise': True,
    'heading': 0,
}
    
def try_to_bind_to_socket():
    global sock, connection
    """Try to bind to the socket and accept the connection"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    global connection
    logging.info(f"Binding to host {WS_HOST, WS_PORT}")
    sock.bind((WS_HOST, WS_PORT))
    sock.listen()
    connection, addr = sock.accept()
    logging.info(f'Connected by {addr}')


start_time=None




while True:
    time.sleep(args.delay)
    if args.benchmark:
        start_time = time.time()
    try:
        if not connection:
            try_to_bind_to_socket()
        
        else:
    
            data = connection.recv(1024)  # Receive data from the client
            if not data:
                continue
            
            json_data = None
            try:
                json_data = json.loads(data.decode('utf-8'))
            except json.JSONDecodeError as e:
                logging.error(f"Error decoding JSON: {e}")
                continue
            
            # Check if there are any targets in the frame
            if len(json_data['targets']) > 0:
                logging.debug('Data obtained:' + json.dumps(data.decode('utf-8')))
                already_sent_no_targets=False 
                center_x, center_y =  json_data['heading_vect']
                target_index = get_priority_target_index(json_data['targets'], args.target_type, args.targets)
                
                if target_index is None:
                    logging.debug(f'No valid target found from type {args.target_type} with ids {args.targets}')
                    azimuth_pid.reset()
                    el_pid.reset()
                    # If no valid target was found, then just move onto the next frame
                    continue
                
                target = json_data['targets'][target_index] # Extract the first target from the targets list
                
                logging.debug('Targeting:' + json.dumps(target))

                left, top, right, bottom = target['box']
                
                # calculate box coordinates
                box_center_x = (left + right) / 2
                box_center_y = (top + bottom) / 2
                box_width = right - left
                box_height = bottom - top
                
                view_width = json_data['view_dimensions'][0]
                view_height = json_data['view_dimensions'][1]

                # Get movement vector to align gun with center of target
                movement_vector = get_frame_box_dimensions_delta(left, top, right, bottom, view_width, view_height)
                
                # Add padding as a percentage of the original dimensions
                padding_width = box_width * TARGET_PADDING_PERCENTAGE
                padding_height = box_height * TARGET_PADDING_PERCENTAGE

                # Calculate box coordinates
                padded_left = left + padding_width
                padded_right = right - padding_width
                padded_top = top + padding_height
                padded_bottom = bottom - padding_height
                    
                is_on_target = False  
                if padded_top <= center_y <= padded_bottom and padded_left <= center_x <= padded_right:
                    is_on_target=True
                
                current_distance_from_the_middle = movement_vector[0]
                max_distance_from_the_middle_left = -(view_width / 2)
                max_distance_from_the_middle_right = view_width / 2
            
                now = time.monotonic()
                dt = min(max(now - last_frame_time, 1e-3), 0.5)
                globals()['last_frame_time'] = now

                if not args.no_pid:
                    gains = tuning_state.gains()
                    azimuth_pid.kp, azimuth_pid.ki, azimuth_pid.kd = (
                        gains['az']['kp'], gains['az']['ki'], gains['az']['kd'])
                    el_pid.kp, el_pid.ki, el_pid.kd = (
                        gains['el']['kp'], gains['el']['ki'], gains['el']['kd'])

                    # Horizontal error: pixels the target centre sits right of
                    # the crosshair (same error the legacy path used).
                    azimuth_error = (
                        current_distance_from_the_middle - args.accuracy_threshold_x
                    )
                    azimuth_formatted = round(
                        azimuth_pid.update(azimuth_error, azimuth_error, dt),
                        args.azimuth_dp,
                    )

                    # Vertical error in magnitude domain, like the legacy
                    # elevation heuristic; direction comes from the stepper.
                    elevation_error = abs(movement_vector[1]) - args.accuracy_threshold_y
                    elevation_speed = el_pid.update(
                        max(elevation_error, 0.0), abs(movement_vector[1]), dt
                    )

                    tuning_state.telemetry({
                        'azimuth': {'error': round(azimuth_error, 1),
                                    'output': azimuth_formatted},
                        'elevation': {'error': round(elevation_error, 1),
                                      'output': round(elevation_speed, 2)},
                        'dt_ms': round(dt * 1000, 1),
                        'is_firing': is_on_target,
                        'targets': len(json_data['targets']),
                    })
                else:
                    predicted_azimuth_angle = map_range(
                        current_distance_from_the_middle - args.accuracy_threshold_x,
                        max_distance_from_the_middle_left,
                        max_distance_from_the_middle_right,
                        -args.max_azimuth_angle,
                        args.max_azimuth_angle
                    )
                    azimuth_speed_adjusted = min(predicted_azimuth_angle, args.x_speed)
                    smoothed_speed_adjusted_azimuth = slow_start_fast_end_smoothing(azimuth_speed_adjusted, float(args.x_smoothing) + 1.0, 90)
                    azimuth_formatted = round(smoothed_speed_adjusted_azimuth, args.azimuth_dp)
                    elevation_speed = get_elevation_speed(args, view_height, movement_vector, target['box'])

                controller_state = cached_controller_state = {
                    'azimuth_angle': azimuth_formatted,
                    'is_clockwise': get_elevation_clockwise(movement_vector),
                    'speed': int(elevation_speed) if not args.no_pid else get_elevation_speed(args, view_height, movement_vector, target['box']),
                    'is_firing': is_on_target,
                }
                
                logging.debug("Sending controller state: " + json.dumps(controller_state))
                
                if not args.test:
                    try:
                        requests.post(url, json=controller_state)       
                    except:
                        logging.error("Failed to send controller state to server.")

            else:
                if args.search:
                   
                    requests.post(url, json={
                        **cached_controller_state,
                        'azimuth_angle': 1 if search["clockwise"] else -1,
                        'speed': 0,
                        'is_firing': False,
                    }) 
                      
                    if search['heading'] > 180:
                        search['heading'] = 0
                        search["clockwise"] = not search["clockwise"]
                    else:
                        search['heading'] += 1                  
                        
                    
                elif not already_sent_no_targets and not args.test:
                    ## No targets detected, so stop the gun but hold its current position
                    requests.post(url, json={
                        **cached_controller_state,
                        'speed': 0,
                        'is_firing': False,
                    })      
                    already_sent_no_targets=True 
    
    except KeyboardInterrupt as e:
        requests.post(url, json={
            'azimuth_angle': 0,
            'speed': 0,
            'is_firing': False,
        }) 
        logging.debug("Sending request to stop turret ")
        raise e 
    except (BrokenPipeError, ConnectionResetError, ConnectionRefusedError) as e:
        logging.error(f'Socket connection lost ({type(e).__name__}). Retrying in 5 seconds...')
        # Reset BOTH handles: leaving the stale `connection` set made the loop
        # retry the dead socket forever instead of rebinding.
        connection = None
        if sock is not None:
            sock.close()
            sock = None
        azimuth_pid.reset()
        el_pid.reset()
        time.sleep(5)
    except Exception as e:
        logging.error("An unknown error occurred: " + str(e) + ". Retrying in 5 seconds...") 
        traceback.print_exc()
        connection = None
        if sock is not None:
            sock.close()
            sock = None
        time.sleep(5)
    finally:
        if start_time and  args.benchmark:
            logging.debug("Frame processed in " + str(time.time() - start_time) + " seconds")
        pass
    
