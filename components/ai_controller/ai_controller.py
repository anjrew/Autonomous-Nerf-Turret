import argparse
import logging
import math
import socket
import threading
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

parser.add_argument('--search', action=argparse.BooleanOptionalAction, default=True, help='Sweep to find targets when none are in sight (default on; --no-search disables).')
parser.add_argument('--search-range', type=float, default=60.0,
                    help='Search sweep amplitude in degrees from centre (0-90).')
parser.add_argument('--search-ease', type=float, default=1.0,
                    help='Ease-in/out at each end of the sweep: 0 = constant speed with instant reversal, 1 = sinusoidal, higher = stronger dwell at the ends.')
parser.add_argument('--search-period', type=float, default=10.0,
                    help='Seconds for one full back-and-forth sweep cycle in search mode.')
parser.add_argument('--search-resume-delay', type=float, default=2.0,
                    help='Seconds to hold position after losing a target before resuming the search sweep.')

parser.add_argument("--target-padding", "-p",help="""
                    Set the padding for when the gun will try and shoot relative to the edge of the target in %%.
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
parser.add_argument('--no-fire', action='store_true',
                    help='Aim and track targets but never fire the gun.')
parser.add_argument('--target-offset-x', type=float, default=0.0,
                    help='Horizontal aim offset in pixels. Positive aims right of the target centre; compensates for gun/camera misalignment.')
parser.add_argument('--target-offset-y', type=float, default=0.0,
                    help='Vertical aim offset in pixels. Positive aims below the target centre; compensates for gun/camera misalignment.')
parser.add_argument('--max-azimuth-delta', type=float, default=5.0,
                    help='Maximum azimuth degrees sent per frame. The Arduino integrates deltas, so large values rail the servo.')
parser.add_argument('--invert-azimuth', action=argparse.BooleanOptionalAction, default=True,
                    help='Negate azimuth deltas so positive commands pan the camera toward increasing screen x (servo mounting dependent).')
parser.add_argument('--ui-port', type=int, default=8081,
                    help='Port for the PID tuning web UI. Set to 0 to disable the UI.')
parser.add_argument('--video-url', default='http://localhost:8082/video.mjpg',
                    help='MJPEG stream URL embedded in the tuning UI live view.')
parser.add_argument('--camera-settings-url', default='http://localhost:8082',
                    help='Base URL of the camera_vision settings API proxied by the tuning UI.')
parser.add_argument('--az-kp', type=float, default=0.00517, help='Azimuth PID proportional gain.')
parser.add_argument('--az-ki', type=float, default=0.0, help='Azimuth PID integral gain.')
parser.add_argument('--az-kd', type=float, default=0.0003, help='Azimuth PID derivative gain.')
parser.add_argument('--el-kp', type=float, default=0.00244, help='Elevation PID proportional gain.')
parser.add_argument('--el-ki', type=float, default=0.001, help='Elevation PID integral gain.')
parser.add_argument('--el-kd', type=float, default=0.0, help='Elevation PID derivative gain.')



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

# Live-tunable PID gains (sliders in the tuning UI apply per frame), runtime
# mode params (target type / tracked ids), and the per-axis controllers.
tuning_state = TuningState({
    'az': {'kp': args.az_kp, 'ki': args.az_ki, 'kd': args.az_kd},
    'el': {'kp': args.el_kp, 'ki': args.el_ki, 'kd': args.el_kd},
}, initial_params={
    'target_type': args.target_type,
    'targets': list(args.targets),
    'target_offset_x': args.target_offset_x,
    'target_offset_y': args.target_offset_y,
    'search_enabled': args.search,
    'search_range': args.search_range,
    'search_ease': args.search_ease,
    'search_period': args.search_period,
    'search_resume_delay': args.search_resume_delay,
    'control_mode': 'auto',
    'manual_azimuth': 0.0,
    'manual_speed': 0.0,
    'manual_clockwise': False,
    'manual_fire': False,
    'accuracy_threshold_x': args.accuracy_threshold_x,
    'accuracy_threshold_y': args.accuracy_threshold_y,
})


def joystick_input_thread():
    """Poll a connected gamepad and drive the manual controls from it."""
    try:
        # SDL video init aborts off the main thread on macOS; joystick needs no video.
        os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
        import pygame
        pygame.joystick.init()
    except Exception as e:
        logging.warning(f'Joystick support unavailable: {e}')
        return
    logging.info('Watching for a joystick...')
    deadzone = 0.12
    stick = None
    while True:
        try:
            if pygame.joystick.get_count() == 0:
                if stick is not None:
                    logging.warning('Joystick disconnected')
                    stick = None
                time.sleep(1.0)
                continue
            if stick is None:
                stick = pygame.joystick.Joystick(0)
                stick.init()
                logging.info(f'Joystick connected: {stick.get_name()}')
            pygame.event.pump()
            azimuth_axis = stick.get_axis(0)
            elevation_axis = stick.get_axis(1)
            fire = stick.get_button(0) if stick.get_numbuttons() > 0 else False
            updates = {
                'manual_speed': round(min(10.0, abs(elevation_axis) * 10.0), 1),
                'manual_clockwise': bool(elevation_axis > 0.0),
                'manual_fire': bool(fire) and not args.no_fire,
            }
            if abs(azimuth_axis) > deadzone:
                updates['manual_azimuth'] = round(azimuth_axis * 90.0, 1)
            if abs(azimuth_axis) > deadzone or abs(elevation_axis) > deadzone or fire:
                updates['control_mode'] = 'manual'
            tuning_state.set_params(updates)
            time.sleep(0.03)
        except Exception as e:
            logging.error(f'Joystick thread error: {e}')
            stick = None
            time.sleep(1)


def keyboard_input_thread():
    """Arrow keys adjust the manual controls; space fires; M toggles manual."""
    try:
        import keyboard
    except Exception as e:
        logging.warning(f'Keyboard control unavailable: {e}')
        return

    def pressed(key_name: str) -> bool:
        try:
            return keyboard.is_pressed(key_name)
        except Exception:
            return False # Some keys (e.g. letters) are unmapped on macOS

    m_latch = False
    fire_latch = False
    while True:
        time.sleep(0.05)
        try:
            azimuth_delta = 0.0
            if pressed('left'):
                azimuth_delta -= 3
            if pressed('right'):
                azimuth_delta += 3
            speed_delta = 0
            if pressed('up'):
                speed_delta = 1
            if pressed('down'):
                speed_delta = -1
            fire = pressed('space')
            m_now = pressed('m')
            updates = {}
            if m_now and not m_latch:
                mode_now = tuning_state.params().get('control_mode', 'auto')
                updates['control_mode'] = 'auto' if mode_now == 'manual' else 'manual'
            m_latch = m_now
            if azimuth_delta or speed_delta or fire:
                updates['control_mode'] = 'manual'
                current = tuning_state.params()
                updates['manual_azimuth'] = max(-90.0, min(90.0,
                    current.get('manual_azimuth', 0.0) + azimuth_delta))
                updates['manual_speed'] = max(0.0, min(10.0,
                    current.get('manual_speed', 0.0) + speed_delta))
            if fire and not args.no_fire:
                updates['manual_fire'] = True
            elif fire_latch:
                updates['manual_fire'] = False
            fire_latch = fire
            if updates:
                tuning_state.set_params(updates)
        except Exception as e:
            logging.warning(f'Keyboard thread error: {e}')
            time.sleep(1)


threading.Thread(target=joystick_input_thread, daemon=True).start()
threading.Thread(target=keyboard_input_thread, daemon=True).start()
azimuth_pid = PIDController(
    kp=args.az_kp, ki=args.az_ki, kd=args.az_kd,
    output_limits=(-args.max_azimuth_angle, args.max_azimuth_angle),
)
el_pid = PIDController(
    kp=args.el_kp, ki=args.el_ki, kd=args.el_kd,
    output_limits=(0, args.max_elevation_speed * args.y_speed / 2),
)
if args.ui_port:
    ui_server = start_tuning_ui(tuning_state, args.ui_port, args.video_url,
                                args.camera_settings_url)
    logging.info(f'PID tuning UI on http://0.0.0.0:{args.ui_port}')
last_frame_time = time.monotonic()
WS_HOST = args.ws_host  # IP address of the server
WS_PORT = args.ws_port  # Port number to listen on


url = f"http://{args.host}:{args.port}"

def send_command(payload: dict) -> bool:
    """Post a command to the serial driver with a hard timeout.

    A stale pooled keep-alive connection (e.g. after the driver restarted)
    can otherwise hang the control loop forever on the response wait, so
    failures swap in a fresh session and the next frame starts clean.
    """
    global session
    try:
        if args.invert_azimuth:
            payload = {**payload, 'azimuth_angle': -payload.get('azimuth_angle', 0)}
        session.post(url, json=payload, timeout=0.05)
        return True
    except Exception:
        session = requests.Session()
        return False

# One keep-alive session for the per-frame command POSTs: re-creating the
# TCP connection every frame costs ~0.3 ms on localhost (more over Wi-Fi).
session = requests.Session()

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
recv_buffer = b'' # Newline-delimited frames from the camera can arrive coalesced

search_phase = 0.0 # Radians along the back-and-forth sweep cycle
search_pending = 0.0 # Fractional degree remainder (the protocol takes whole degrees)
last_search_time = time.monotonic()
was_searching = False # True while search is engaged, so a resume starts smoothly
search_resume_deadline = None # Monotonic time when the sweep may resume after losing a target
manual_azimuth_sent = 0.0 # Last azimuth target sent to the Arduino (which integrates deltas)
az_pending = 0.0 # Fractional carry so sub-degree PID corrections still integrate
el_pending = 0.0 # Same carry for the elevation speed ordinal
    
def try_to_bind_to_socket():
    global sock, connection
    """Try to bind to the socket and accept the connection"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    global connection
    logging.info(f"Binding to host {WS_HOST, WS_PORT}")
    sock.bind((WS_HOST, WS_PORT))
    sock.listen()
    connection, addr = sock.accept()
    connection.settimeout(0.25) # Tick the loop even when the camera sends nothing (manual control)
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
    
            try:
                data = connection.recv(1024)  # Receive data from the client
            except TimeoutError:
                data = None
            if data == b'':
                # Clean EOF: the camera reconnected elsewhere, so rebind.
                logging.warning('Camera socket closed; rebinding...')
                connection = None
                if sock is not None:
                    sock.close()
                    sock = None
                recv_buffer = b''
                continue
            if data:
                recv_buffer += data

            mode_params = tuning_state.params()

            if mode_params.get('control_mode', 'auto') == 'manual':
                # The Arduino integrates relative deltas, so send the change
                # since the last target rather than the target itself.
                target_azimuth = mode_params.get('manual_azimuth', 0.0)
                delta = int(round(target_azimuth - manual_azimuth_sent))
                manual_azimuth_sent = target_azimuth
                command = {
                    'azimuth_angle': delta,
                    'is_clockwise': bool(mode_params.get('manual_clockwise', False)),
                    'speed': int(round(mode_params.get('manual_speed', 0.0))),
                    'is_firing': bool(mode_params.get('manual_fire', False)) and not args.no_fire,
                }
                tuning_state.telemetry({'manual': {**command, 'target_azimuth': target_azimuth}})
                if not args.test and not send_command(command):
                    logging.error("Failed to send manual command to server.")
                recv_buffer = b'' # Stale camera frames are useless after manual control
                continue

            if not recv_buffer or b'\n' not in recv_buffer:
                continue # No complete camera frame yet

            # Camera frames are newline-delimited and can arrive coalesced;
            # process only the newest complete frame.
            newest_frame, _, recv_buffer = recv_buffer.rpartition(b'\n')

            json_data = None
            try:
                json_data = json.loads(newest_frame.strip().decode('utf-8'))
            except json.JSONDecodeError as e:
                logging.error(f"Error decoding JSON: {e}")
            if json_data is None:
                continue

            # Check if there are any targets in the frame
            target_index = None
            if len(json_data['targets']) > 0:
                logging.debug('Data obtained:' + json.dumps(json_data))
                center_x, center_y =  json_data['heading_vect']
                mode_params = tuning_state.params()
                target_type = mode_params.get('target_type', args.target_type)
                target_ids = mode_params.get('targets', list(args.targets))
                target_index = get_priority_target_index(json_data['targets'], target_type, target_ids)

                if target_index is None:
                    # Objects were seen but none match the current target type,
                    # so treat this like having no target at all (search/hold).
                    logging.debug(f'No valid target found from type {target_type} with ids {target_ids}')

            if target_index is not None:
                was_searching = False
                already_sent_no_targets=False
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
                if 'center' in target:
                    # Segmentation mode: aim at the mask centroid, which is
                    # steadier than the bounding-box centre.
                    cx, cy = target['center']
                    movement_vector = (view_width // 2 - cx, view_height // 2 - cy)
                else:
                    movement_vector = get_frame_box_dimensions_delta(left, top, right, bottom, view_width, view_height)
                
                # Add padding as a percentage of the original dimensions
                padding_width = box_width * TARGET_PADDING_PERCENTAGE
                padding_height = box_height * TARGET_PADDING_PERCENTAGE

                # Calculate box coordinates
                padded_left = left + padding_width
                padded_right = right - padding_width
                padded_top = top + padding_height
                padded_bottom = bottom - padding_height
                    
                aim_x = center_x + mode_params.get('target_offset_x', 0.0)
                aim_y = center_y + mode_params.get('target_offset_y', 0.0)

                is_on_target = False
                if padded_top <= aim_y <= padded_bottom and padded_left <= aim_x <= padded_right:
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

                    # Horizontal error: pixels between the target centre and
                    # the offset aim point (same error the legacy path used).
                    azimuth_error = (
                        current_distance_from_the_middle
                        - mode_params.get('target_offset_x', 0.0)
                        - mode_params.get('accuracy_threshold_x', args.accuracy_threshold_x)
                    )
                    azimuth_formatted = round(
                        azimuth_pid.update(azimuth_error, azimuth_error, dt),
                        args.azimuth_dp,
                    )
                    azimuth_formatted = max(-args.max_azimuth_delta, min(args.max_azimuth_delta, azimuth_formatted))
                    az_pending += azimuth_formatted
                    az_step = int(az_pending)
                    az_pending -= az_step

                    # Vertical error in magnitude domain, like the legacy
                    # elevation heuristic; direction comes from the stepper.
                    elevation_error = (
                        abs(movement_vector[1])
                        - mode_params.get('target_offset_y', 0.0)
                        - mode_params.get('accuracy_threshold_y', args.accuracy_threshold_y)
                    )
                    elevation_speed = el_pid.update(
                        max(elevation_error, 0.0), abs(movement_vector[1]), dt
                    )
                    el_pending += elevation_speed
                    el_step = min(10, max(0, int(el_pending)))
                    el_pending -= el_step

                    tuning_state.telemetry({
                        'azimuth': {'error': round(azimuth_error, 1),
                                    'output': azimuth_formatted},
                        'elevation': {'error': round(elevation_error, 1),
                                      'output': round(elevation_speed, 2)},
                        'dt_ms': round(dt * 1000, 1),
                        'is_firing': is_on_target and not args.no_fire,
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
                    azimuth_formatted = max(-args.max_azimuth_delta, min(args.max_azimuth_delta, azimuth_formatted))
                    elevation_speed = get_elevation_speed(args, view_height, movement_vector, target['box'])

                controller_state = cached_controller_state = {
                    'azimuth_angle': az_step,
                    'is_clockwise': get_elevation_clockwise(movement_vector),
                    'speed': el_step if not args.no_pid else get_elevation_speed(args, view_height, movement_vector, target['box']),
                    'is_firing': is_on_target and not args.no_fire,
                }
                
                logging.debug("Sending controller state: " + json.dumps(controller_state))
                
                if not args.test:
                    try:
                        send_command(controller_state)
                    except:
                        logging.error("Failed to send controller state to server.")

            if target_index is None:
                azimuth_pid.reset()
                el_pid.reset()
                mode_params = tuning_state.params()
                if mode_params.get('search_enabled', args.search):
                    # The Arduino integrates relative azimuth deltas, so sweep
                    # by sending the per-frame velocity of a sinusoidal
                    # position profile: naturally zero velocity at each end
                    # (ease-in/out); search_ease sharpens (>1) or flattens
                    # (<1) that shaping.
                    now_search = time.monotonic()
                    resume_delay = max(0.0, mode_params.get('search_resume_delay', args.search_resume_delay))
                    if not was_searching and search_resume_deadline is None:
                        search_resume_deadline = now_search + resume_delay
                    if search_resume_deadline is not None and now_search < search_resume_deadline:
                        # Target just lost: hold position before resuming the sweep.
                        last_search_time = now_search
                        tuning_state.telemetry({'search': {'active': False,
                                                           'resume_in': round(search_resume_deadline - now_search, 1)}})
                    else:
                        if not was_searching:
                            # Fresh engagement: start the sweep smoothly instead of
                            # leaping with a stale timing delta.
                            last_search_time = now_search
                            search_pending = 0.0
                            search_dt = 0.0
                        was_searching = True
                        search_resume_deadline = None
                        search_dt = min(max(now_search - last_search_time, 0.0), 0.5)
                        last_search_time = now_search
                        period = max(1.0, mode_params.get('search_period', args.search_period))
                        search_phase = (search_phase + 2 * math.pi * search_dt / period) % (2 * math.pi)
                        amplitude = max(0.0, min(90.0, mode_params.get('search_range', args.search_range)))
                        ease = max(0.0, mode_params.get('search_ease', args.search_ease))
                        wave = math.cos(search_phase)
                        delta = (
                            amplitude * (2 * math.pi / period)
                            * math.copysign(abs(wave) ** ease, wave)
                            * search_dt
                        )
                        # The protocol only carries whole degrees; accumulate the
                        # fractional remainder so slow phases still integrate out
                        # to the full sweep range instead of stalling near zero.
                        search_pending += delta
                        step = int(round(search_pending))
                        search_pending -= step
                        tuning_state.telemetry({
                            'search': {'active': True,
                                       'delta': round(delta, 2),
                                       'step': step,
                                       'phase_deg': round(math.degrees(search_phase), 1)},
                        })
                        if not args.test and not send_command({
                            **cached_controller_state,
                            'azimuth_angle': step,
                            'speed': 0,
                            'is_firing': False,
                        }):
                            logging.error("Failed to send search command to server.")

                elif not already_sent_no_targets and not args.test:
                    ## No targets detected, so stop the gun but hold its current position
                    send_command({
                        **cached_controller_state,
                        'speed': 0,
                        'is_firing': False,
                    })
                    already_sent_no_targets=True

    except KeyboardInterrupt as e:
        send_command({
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
    
