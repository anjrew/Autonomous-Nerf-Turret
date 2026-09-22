# Standard library imports
import socket
import time
import os
import sys
from typing import List, Optional


sys.path.append(os.path.dirname(os.path.abspath(__file__)) + '/..')

# Third-party imports
import cv2
import face_recognition
import json
import logging
import numpy as np

# Local/application-specific imports
from argparse import ArgumentParser
from nerf_turret_utils.args_utils import map_log_level, str2bool
from camera_vision_utils import get_face_location_details, get_target_id, find_faces_in_frame, draw_face_box, draw_cross_hair
from yolo_object_detection.object_detection import YoloObjectDetector
from yolo_object_detection.object_detection import ObjectDetector
from yolo_object_detection.utils import draw_object_mask, draw_object_box
from yolo_object_detection.opencv_onnx_python import ONNXObjectDetector
from stream_server import start_stream_server, update as update_stream, TurretSettings


parser = ArgumentParser(description="Track faces with bounding boxes")

parser.add_argument('--camera', '-c', type=int, default=0, help="Choose the camera for tracking" )

parser.add_argument('--crosshair_size', '-ch', type=int, default=10, help="The size of the crosshair" )

parser.add_argument("--port", help="Set the web socket server port to send messages to.", default=6565, type=int)
parser.add_argument("--host", help="Set the web socket server hostname to send messages to.", default="localhost")

parser.add_argument("--detector", "-d" , help="The detector to use with inference.", default='yolo', type=str)

parser.add_argument("--log-level", "-ll" , help="Set the logging level by integer value.", default=logging.INFO, type=map_log_level)
parser.add_argument("--delay", help="Delay to limit the data flow into the websocket server.", default=0, type=int)
parser.add_argument("--headless", help="Deprecated: same as --view none.", action='store_true', default=False)
parser.add_argument("--view", choices=['web', 'window', 'none'], default='web',
                    help="Where to show the feed: web (MJPEG stream in the tuning UI, default), window (native OpenCV window), or none.")
parser.add_argument("--stream-port", help="Port for the MJPEG web stream of the annotated feed. 0 disables the stream.", type=int, default=8082)
parser.add_argument("--id-targets", "-it", help="Whether to id targets that are stored in the './data/targets' folder.", action='store_true', default=False)
parser.add_argument("--test", "-t", help="Test without trying to emit data.", action='store_true', default=False)
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

parser.add_argument("--imgsz", type=int, default=640,
                    help="Inference input size. 640 = most accurate; lower values trade recall for speed. Live-tunable.")

args = parser.parse_args()

logging.basicConfig(level=args.log_level)

settings = TurretSettings({
    'imgsz': args.imgsz,
    'image_compression': args.image_compression,
    'detect_every': args.skip_frames + 1,
    'object_confidence': args.object_confidence,
    'detect_faces': args.detect_faces,
    'detect_objects': args.detect_objects,
    'id_targets': args.id_targets,
    'loop_delay': args.delay,
})

VIEW = 'none' if args.headless else args.view

logging.debug(f"\nArgs: {args}\n")


target_images = []
target_names = [ ]
targets_loaded = False

script_dir = os.path.dirname(os.path.abspath(sys.argv[0]))


def ensure_targets_loaded():
    """Load known-target encodings once, the first time face ID targeting is used"""
    global target_images, target_names, targets_loaded
    if targets_loaded:
        return
    targets_dir = f"{script_dir}/data/targets"
    os.makedirs(targets_dir, exist_ok=True)
    names, images = [], []
    for file in os.listdir(targets_dir):
        if not file.lower().endswith(('.jpg', '.jpeg', '.png')):
            continue
        names.append(file.rsplit('.', 1)[0])
        images.append(
            face_recognition.face_encodings(
                cv2.cvtColor(
                    cv2.imread(
                        f"{targets_dir}/{file}"
                    ),
                    cv2.COLOR_BGR2RGB
                )
            )[0]
        )
    target_names = names
    target_images = images
    targets_loaded = True
    if target_names:
        logging.info(f" Labeling targets {target_names}")
    else:
        logging.warning(
            f"No target photos in {targets_dir}; face ID targeting will match nobody "
            "until photos named <person>.jpg are added there."
        )


def get_target_names(refresh: bool = False) -> list:
    global targets_loaded
    if refresh:
        targets_loaded = False
    ensure_targets_loaded()
    return list(target_names)


if settings.get('id_targets'):
    ensure_targets_loaded()

if VIEW == 'web' and args.stream_port:
    start_stream_server(args.stream_port, settings, get_target_names)
    logging.info(f"MJPEG stream on http://0.0.0.0:{args.stream_port}/video.mjpg")


object_detector: Optional[ObjectDetector] = None


def ensure_object_detector():
    global object_detector
    if object_detector is None:
        object_detector = ONNXObjectDetector() if args.detector == 'onnx' else YoloObjectDetector(
            imgsz=settings.get('imgsz', 640))
    return object_detector


if settings.get('detect_objects'):
    ensure_object_detector()
                       
## Setup ready to send data to subscribers
HOST = args.host  # IP address of the server
PORT = args.port  # Port number to listen on


# Set this value to change the Camera ID
CAMERA_ID = args.camera
CROSS_HAIR_SIZE = args.crosshair_size

cap = cv2.VideoCapture(CAMERA_ID)

if not cap.isOpened():
    logging.error(
        f"Camera {CAMERA_ID} failed to open. On macOS this usually means camera access "
        "is denied: System Settings > Privacy & Security > Camera, enable it for your "
        "terminal app, then re-run."
    )
    sys.exit(1)

scaling_factor = 0.5
web_socket_client_connection = None
face_locations = []

skip_frames =  args.skip_frames + 1
frame_count = 0



def try_to_create_socket():
    global web_socket_client_connection
    logging.info(f"Connecting to web socket host @ {HOST, PORT}")
    try:
        # Create a new socket and connect to the server
        web_socket_client_connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        web_socket_client_connection.connect((HOST, PORT))
        logging.info(f"Successfully Connected to socket @ {HOST, PORT}")
    except Exception as e:
        time.sleep(1)
        web_socket_client_connection = None
        logging.error("Failed on trying to connect to socket. Attempting to try again")
        print(e)
        
        pass


start_time=time.time()
targets = [] # List of targets in the frame to keep out here for skipped frame processing

while True:
    time.sleep(settings.get('loop_delay', args.delay))
    if args.benchmark:
        print(f'Performance benchmark on 1 loop:{ round(time.time() - start_time, 3) * 1000 }ms', )
        start_time = time.time()

    if not web_socket_client_connection and not args.test:
        try_to_create_socket()
        
    try:
        image_compression = settings.get('image_compression', args.image_compression)
        frame_count += 1
        skip_frame = frame_count % settings.get('detect_every', skip_frames) == 0
        logging.debug(f"Skipping frame: {skip_frame}")
        
        ret, frame = cap.read()
        
        if not ret or frame is None:
            logging.error(f"Failed to read frame from camera {CAMERA_ID}. Retrying in 5 seconds...")
            time.sleep(5)
            continue
                
        # Get the image height and width
        frame_height, frame_width, _ = frame.shape   
        
        compressed_image = cv2.resize(frame, (0, 0), fx=1/image_compression, fy=1/image_compression) #type: ignore

        if not skip_frame:
            targets = []
            if settings.get('detect_faces', args.detect_faces):
                face_locations = find_faces_in_frame(compressed_image)
        elif not settings.get('detect_faces', args.detect_faces):
            face_locations = []

        
        # Loop through each face in this frame of video that were detected
        for face_location in face_locations:
            # Scale back up face locations since the frame we detected in was scaled to 1/4 size
            target = get_face_location_details(image_compression, face_location)
            
            if settings.get('id_targets', args.id_targets):
                ensure_targets_loaded()
                if target_names:
                    target["id"]  = get_target_id(frame, target["box"], target_names, target_images)
                
            targets.append(target)
            
        if settings.get('detect_objects', args.detect_objects) and not skip_frame:
            if object_detector is None:
                ensure_object_detector()
            else:
                object_detector.imgsz = settings.get('imgsz', 640)
            results =  object_detector.detect(compressed_image, settings.get('object_confidence', args.object_confidence)) #type: ignore
            for result in results:

                # target = { "box": result["box"], "type": result["class_name"], "mask": result["mask"].tolist()}
                target = { "box": (np.array(result["box"]) * image_compression).tolist(), "type": result["class_name"],}
                targets.append(target)
                
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
                
                class_color = object_detector.get_color_for_class_name(target['type'])

                if 'mask' in target:
                    frame = draw_object_mask(frame, class_color, np.array(target['mask']))
                
                if 'box' in target:
                    frame = draw_object_box(frame, left, top, right, bottom, target['type'], class_color)
                
            # Always draw the cross hai.rindex() if not headless        
        frame =  draw_cross_hair(frame, CROSS_HAIR_SIZE, is_on_target)

 
        
        if len(targets) > 0:
            center_x = frame_width // 2
            center_y = frame_height // 2
            data = {
                "targets": targets,
                "heading_vect": [center_x, center_y],
                "view_dimensions": [frame_width, frame_height],
            }
            json_data = json.dumps(data).encode('utf-8') # Encode the JSON object as a byte string
            
            # logging.debug(f'{ "Mock: "if args.test else ""}Sending data({len(json_data)}) to the AI controller:' + json.dumps(data))
            logging.debug(f'{ "Mock: "if args.test else ""}Sending data({len(json_data)}) to the AI controller:' + json.dumps(data))
            if web_socket_client_connection and not args.test:
                web_socket_client_connection.sendall(json_data) # Send the byte string to the server
                
        else:
            if web_socket_client_connection and not args.test:
                web_socket_client_connection.sendall(json.dumps({"targets": []}).encode('utf-8'))
            
        if VIEW == 'web' and args.stream_port:
            ok, jpeg = cv2.imencode('.jpg', frame)
            if ok:
                update_stream(jpeg.tobytes())

        if VIEW == 'window':
            cv2.imshow('Face Detector', frame)

            c = cv2.waitKey(1)
            ## S 'key'
            if c == 27:
                break
        
        
    except KeyboardInterrupt as e:
        raise e
    except AttributeError as e:
        logging.error("Wrong property accessed. See logs below. Retrying in 5 seconds...")
        print(e)
        time.sleep(5)
        pass
    except BrokenPipeError as e:
        logging.error("Socket pipe broken. Retrying in 5 seconds...")
        time.sleep(5)
        web_socket_client_connection = None
        pass 
    except ConnectionResetError as e:
        logging.error("Socket connection lost. Retrying in 5 seconds...")
        time.sleep(5)
        web_socket_client_connection = None
        pass
    except Exception as e:
        logging.error(f"Unhandled error in camera loop ({type(e).__name__}: {e}). Retrying in 1 second...")
        time.sleep(1)
        pass
    finally:
        # Record the time taken to process the frame
        if start_time and args.benchmark:
            logging.debug("Frame processed in " + str(time.time() - start_time) + " seconds")
        pass
        
cap.release()

        
cv2.destroyAllWindows()