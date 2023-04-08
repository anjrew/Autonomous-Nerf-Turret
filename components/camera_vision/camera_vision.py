# Standard library imports
import socket
import time
import os
import sys
from datetime import datetime
from typing import List, Optional, cast

directory = os.path.dirname(os.path.abspath(__file__))
sys.path.append(directory + '/..')

# Third-party imports
import cv2
import face_recognition
import json
import logging
import numpy as np

# Local/application-specific imports
from argparse import ArgumentParser
from nerf_turret_utils.args_utils import map_log_level, str2bool
from models import CameraVisionDetection, CameraVisionTarget
from camera_vision_utils import get_face_location_details, get_target_id, find_faces_in_frame, draw_face_box, draw_cross_hair
from yolo_object_detection.object_detection import YoloObjectDetector
from yolo_object_detection.object_detection import ObjectDetector
from yolo_object_detection.utils import draw_object_mask, draw_object_box
from yolo_object_detection.opencv_onnx_python import ONNXObjectDetector


parser = ArgumentParser(description="Track faces with bounding boxes")

parser.add_argument('--camera', '-c', type=int, default=0, help="Choose the camera for tracking" )

parser.add_argument('--record', '-r', action='store_true', default=False, help="Weather to record the video output" )
parser.add_argument('-fps', type=int, default=30, help="The amount of frames per second when recording video" )

parser.add_argument('--crosshair_size', '-ch', type=int, default=10, help="The size of the crosshair" )

parser.add_argument("--port", help="Set the web socket server port to send messages to.", default=6565, type=int)
parser.add_argument("--host", help="Set the web socket server hostname to send messages to.", default="localhost")
parser.add_argument("--test", "-t", help="Test without trying to emit data.", action='store_true', default=False)

parser.add_argument("--detector", "-d" , help="The detector to use with inference.", default='yolo', type=str)

parser.add_argument("--log-level", "-ll" , help="Set the logging level by integer value.", default=logging.INFO, type=map_log_level)

parser.add_argument("--delay", help="Delay in seconds set in the loop to limit the speed of which detections are sent to the controller.", default=0, type=float)

parser.add_argument("--headless", help="Whether to run the service in headless mode.", action='store_true', default=False)

parser.add_argument("--id-targets", "-it", help="Whether to id targets that are stored in the './data/targets' folder.", action='store_true', default=False)


parser.add_argument("--benchmark", "-b", help="Wether to measure the script performance and output in the logs.", action='store_true', default=False)

parser.add_argument("--image-compression", "-ic", 
                        help="The amount to compress the image. Eg give a value of 2 and the image for inference will have half the pixels", type=int, default=4)

parser.add_argument("--skip-frames", "-sk", help="Skip x amount of frames to process to increase performance", type=int, default=500)


parser.add_argument("--detect-faces", "-df", 
                        help="Weather or not to detect faces", type=str2bool, default=True)

parser.add_argument("--detect-objects", "-do", 
                        help="Weather or not to detect general objects", type=str2bool, default=True)

parser.add_argument("--object-confidence", "-oc", 
                        help="Ho confidence the camera vision should be", type=float, default=0.7)

parser.add_argument("--box-targets", "-bt",
                        help="What objects to draw boxes around", nargs='+', type=str, default=['person', 'face'])

args = parser.parse_args()


logging.basicConfig(level=args.log_level)

logging.debug(f"\nArgs: {args}\n")

# Set the random seed so the target box colors are consistent
np.random.seed(42)

session_id = datetime.now().strftime('%H%M%S%Y%m%d') # type: ignore

target_images = []
target_names = [ ]


if args.id_targets:
    """Load the target images and use them to build the target names"""
    script_path = os.path.abspath(sys.argv[0])
    script_dir = os.path.dirname(script_path)
    targets_dir = f"{script_dir}/data/targets"
    
    for file in os.listdir(targets_dir):
             
        target_names.append(file.split('.')[0])
        target_images.append(
            face_recognition.face_encodings(
                cv2.cvtColor(
                    cv2.imread(
                        f"{targets_dir}/{file}"
                    ),
                    cv2.COLOR_BGR2RGB
                )
            )[0]
        )
        
    logging.info(f" Labeling targets {target_names}")
            
image_compression = args.image_compression

object_detector: Optional[ObjectDetector]        
if args.detect_objects:
    object_detector = ONNXObjectDetector() if args.detector == 'onnx' else YoloObjectDetector() 
                       
## Setup ready to send data to subscribers
HOST = args.host  # IP address of the server
PORT = args.port  # Port number to listen on


# Set this value to change the Camera ID
CAMERA_ID = args.camera
CROSS_HAIR_SIZE = args.crosshair_size
HEADLESS=args.headless

if HEADLESS:
    cv2.CAP_DSHOW = False
    

IS_RECORD_MODE = args.record
"""Weather to record the video output"""

fourcc = cv2.VideoWriter_fourcc(*'mp4v') if IS_RECORD_MODE else None # MP4 codec
video_writer: Optional[cv2.VideoWriter] = None

cap = cv2.VideoCapture(CAMERA_ID)



def try_to_create_socket():
    global upd_socket_client_connection
    logging.info(f"Connecting to udp socket host @ {HOST, PORT}")
    try:
        # Create a new socket and connect to the server
        upd_socket_client_connection = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        logging.info(f"Successfully Connected to socket @ {HOST, PORT}")
    except Exception as e:
        time.sleep(1)
        upd_socket_client_connection = None
        logging.error("Failed on trying to connect to socket. Attempting to try again")
        print(e)
        pass


def run_session() -> None:
    global video_writer
    upd_socket_client_connection = None
    face_locations = []

    skip_frames =  args.skip_frames + 1
    frame_count = 0
    cached_detection: Optional[CameraVisionDetection] = None
    
    start_time=time.time()
    targets = [] # List of targets in the frame to keep out here for skipped frame processing
    
    while True:
        time.sleep(args.delay)
        if start_time and args.benchmark:
            print(f'Performance benchmark on 1 loop:{ round(time.time() - start_time, 3) * 1000 }ms', )
            start_time = time.time()

        if not upd_socket_client_connection and not args.test:
            try_to_create_socket()
            
        try:
            frame_count += 1
            skip_frame = frame_count % skip_frames == 0
            logging.debug(f"Skipping frame: {skip_frame}")
            
            _, frame = cap.read()
            if frame is None:
                logging.error("No frame detected. Waiting 1 second and trying again")
                time.sleep(1)
                continue
            
            # Get the image height and width
            frame_height, frame_width, _ = frame.shape 
            
            compressed_image = cv2.resize(frame, (0, 0), fx=1/image_compression, fy=1/image_compression) #type: ignore

            if not skip_frame:
                targets:List[CameraVisionTarget] = []
                if args.detect_faces:
                    face_locations = find_faces_in_frame(compressed_image)

            
            # Loop through each face in this frame of video that were detected
            for face_location in face_locations:
                # Scale back up face locations since the frame we detected in was scaled to 1/4 size
                target: CameraVisionTarget = get_face_location_details(image_compression, face_location)
                
                if args.id_targets:
                    target["id"]  = get_target_id(frame, target["box"], target_names, target_images)
                    
                targets.append(target)
                
            if 'object_detector' in globals() and not skip_frame: 
                results =  object_detector.detect(compressed_image, args.object_confidence) #type: ignore
                for result in results:

                    target: CameraVisionTarget = { "id": None, "mask": None, "box": (np.array(result["box"]) * image_compression).tolist(), "type": result["class_name"],}
                    targets.append(target)
                    
            if not HEADLESS: ## Draw targets
                is_on_target = False
                    
                for target in targets:
                    logging.debug("Target: " + str(target))
                    
                    if len(args.box_targets or []) == 0 or target['type'] not in args.box_targets:
                        continue # skip this target if it's not in the list of targets to draw boxes around
                    
                    left, top, right, bottom = target["box"]
                    center_x = frame_width // 2
                    center_y = frame_height // 2
                    
                    
                    if top <= center_y <= bottom and left <= center_x <= right:
                        is_on_target=True 
                        
                    if target['type'] == 'face':
                        frame = draw_face_box(frame, target, is_on_target)
                        
                    elif object_detector: # type: ignore
                        
                        class_color = cast(ObjectDetector, object_detector).get_color_for_class_name(target['type'])

                        if 'mask' in target and target['mask'] is not None:
                            frame = draw_object_mask(frame, class_color, np.array(target['mask']))
                        
                        if 'box' in target:
                            frame = draw_object_box(frame, left, top, right, bottom, target['type'], class_color)
                        
                    # Always draw the cross hai.rindex() if not headless        
                frame =  draw_cross_hair(frame, CROSS_HAIR_SIZE, is_on_target)

                
            if not HEADLESS:
                logging.debug(f"Drawing frame")
                cv2.imshow('Face Detector', frame)

            detection_data: CameraVisionDetection = {
                    "targets": targets,
                    "view_dimensions": (frame_width, frame_height),
                } if len(targets) > 0 else {"targets": [], 'view_dimensions': (frame_width, frame_height)}
            
            if detection_data == cached_detection:
                logging.debug("No new action, skipping request")
            else:
                cached_detection = detection_data   
                json_data = json.dumps(detection_data).encode('utf-8') # Encode the JSON object as a byte string
                
                logging.debug(f'{ "Mock: "if args.test else ""}Sending data({len(json_data)}) to the AI controller:' + json.dumps(detection_data))
                if upd_socket_client_connection and not args.test:
                    upd_socket_client_connection.sendto(json_data, (HOST, PORT)) # Send the byte string to the server
                    
            if IS_RECORD_MODE:
                if video_writer is None:
                    video_folder=f'{directory}/../../artifacts/videos'
                    if not os.path.exists(video_folder):
                        os.makedirs(video_folder)
                    video_writer = cv2.VideoWriter(f'{video_folder}/{session_id}.mp4', fourcc, args.fps, (frame_width, frame_height))
                # Write the processed frame to the output video file
                cast(cv2.VideoWriter,video_writer).write(frame)
                
                
            # This must be hit in order to render the frame
            c = cv2.waitKey(1)
            ## S 'key'
            if c == 27:
                break
            
        except KeyboardInterrupt as e:
            raise e
        except AttributeError as e:
            logging.error(f"Wrong property accessed. See logs below.Retrying in 5 seconds...{e}")     
            print(e)
            time.sleep(5)
            pass
        except BrokenPipeError as e:
            logging.error("Socket pipe broken. Retrying in 5 seconds...")
            time.sleep(5)
            upd_socket_client_connection = None
            pass 
        except ConnectionResetError as e:
            logging.error("Socket connection lost. Retrying in 5 seconds...")
            time.sleep(5)
            upd_socket_client_connection = None
            pass
    
    
# Run session logging any errors and cleaning up resources safely after session has finished 
try:
    run_session()
except Exception as e:
    logging.error(str(e))
finally:
    cap.release()
    cv2.destroyAllWindows()
    cast(cv2.VideoWriter,video_writer).release()    

      
