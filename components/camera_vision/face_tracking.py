# Standard library imports
import argparse
import os
import socket
import sys
import time

# Third-party imports
import cv2
import face_recognition
import json
import logging
import math

# Local/application-specific imports
from argparse import ArgumentParser
from face_tracking_utils import map_log_level


parser = ArgumentParser(description="Track faces with bounding boxes")

parser.add_argument('--camera', '-c', type=int, default=0, help="Choose the camera for tracking" )

parser.add_argument('--crosshair_size', '-ch', type=int, default=10, help="The size of the crosshair" )

parser.add_argument("--port", help="Set the web socket server port to send messages to.", default=6565, type=int)
parser.add_argument("--host", help="Set the web socket server hostname to send messages to.", default="localhost")

parser.add_argument("--log-level", "-ll" , help="Set the logging level by integer value.", default=logging.INFO, type=map_log_level)
parser.add_argument("--delay", help="Delay to limit the data flow into the websocket server.", default=0, type=int)
parser.add_argument("--headless", help="Whether to run the service in headless mode.", action='store_true', default=False)
parser.add_argument("--id-targets", "-it",help="Whether to only shoot targets that are stored in the './data/targets' folder.", action='store_true', default=False)
parser.add_argument("--test", "-t",help="Test without trying to emit data.", action='store_true', default=False)
parser.add_argument("--benchmark", "-b",help="Wether to measure the script performance and output in the logs.", action='store_true', default=False)


args = parser.parse_args()

logging.basicConfig(level=args.log_level)

target_images = []
target_names = [ ]

if args.id_targets:

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
            
          
        
## Setup ready to send data to subscribers
HOST = args.host  # IP address of the server
PORT = args.port  # Port number to listen on


# Set this value to change the Camera ID
CAMERA_ID = args.camera
CROSS_HAIR_SIZE = args.crosshair_size
HEADLESS=args.headless

if HEADLESS:
    cv2.CAP_DSHOW = False

cap = cv2.VideoCapture(CAMERA_ID)

scaling_factor = 0.5
process_this_frame = True
web_socket_client_connection = None
face_locations = []


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

start_time=None

while True:
    
    time.sleep(args.delay)
    if args.benchmark:
        start_time = time.time()

    if not web_socket_client_connection and not args.test:
        try_to_create_socket()
        
    try:
        targets = [] # List of targets in the frame
        
        ret, frame = cap.read()
        
        # Get the image height and width
        height, width, _ = frame.shape
        
        # Calculate the center coordinates
        center_x = width // 2
        center_y = height // 2
            
        if process_this_frame:
            
            small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25) #type: ignore
    
            face_locations = face_recognition.face_locations(small_frame)

        process_this_frame = not process_this_frame
        
        for top, right, bottom, left in face_locations:
            # Scale back up face locations since the frame we detected in was scaled to 1/4 size
            top *= 4
            right *= 4
            bottom *= 4
            left *= 4
    
            is_on_target = False  
            if top <= center_y <= bottom and left <= center_x <= right:
                is_on_target=True
            
            target_highlight_size = 5 if is_on_target else 1
            target_highlight_color = (0, 0, 255) if is_on_target else (0, 100, 0)
            
            if not HEADLESS:
                
                # Draw a box around the face
                cv2.rectangle(frame, (left, top), (right, bottom), target_highlight_color, 2)
                
            box_center_x = (left + right) / 2
            box_center_y = (top + bottom) / 2
            box_width = right - left
            
            movement_vector = [box_center_x - center_x, box_center_y - center_y]
            
            distance = math.sqrt(movement_vector[0]**2 + movement_vector[1]**2)
            
            lock_text = "Lock" if is_on_target else f""
             
            target = { "vec_delta": movement_vector, "locked": is_on_target, "box": [left, top, right, bottom]}
            
            if args.id_targets:
                t_width = right-left
                t_height = bottom-top
                sub_image = frame[top:top+t_height, left:left+t_width]
                img = cv2.cvtColor(   
                        sub_image,
                        cv2.COLOR_BGR2RGB
                    )
                img_encoding = face_recognition.face_encodings(
                    img
                )
                
                if len(img_encoding) >  0:
                    matched_results = face_recognition.compare_faces(target_images, img_encoding[0])
                    if True in matched_results:
                        # Do something with the index of the matching face
                        result = matched_results.index(True)
                        
                        target["id"] = target_names[result]
                    else:
                        logging.debug("Target not recognized")
                
                
            targets.append(target)
            
            if not HEADLESS:
                font_size = 445
                
                # Draw a label with a name below the face
                cv2.rectangle(frame, (left, bottom - 35), (right, bottom), target_highlight_color, cv2.FILLED)
                font = cv2.FONT_HERSHEY_DUPLEX
                box_text = target.get("id") if target.get("id") else f"{lock_text} {movement_vector} {distance:.2f}"
                cv2.putText(frame, box_text, (left + 6, bottom - 6), font, box_width/font_size, (255, 255, 255), 1)
                
                # Draw a red horizontal line through the center
                cv2.line(frame, (center_x - CROSS_HAIR_SIZE, center_y), (center_x + CROSS_HAIR_SIZE, center_y), target_highlight_color, target_highlight_size)
                
                # Draw a red vertical line through the center
                cv2.line(frame, (center_x, center_y - CROSS_HAIR_SIZE), (center_x, center_y + CROSS_HAIR_SIZE), target_highlight_color, target_highlight_size)
        
        if len(targets) > 0:
            data = {
                "targets": targets,
                "heading_vect": [center_x, center_y],
                "view_dimensions": [width, height],
            }
            json_data = json.dumps(data).encode('utf-8') # Encode the JSON object as a byte string
            
            
            logging.debug(f'{ "Mock: "if args.test else ""}Sending data to the AI controller:' + json.dumps(data))
            if web_socket_client_connection and not args.test:
                web_socket_client_connection.sendall(json_data) # Send the byte string to the server
                
        else:
            if web_socket_client_connection and not args.test:
                web_socket_client_connection.sendall(json.dumps({"targets": []}).encode('utf-8'))
            
        if not HEADLESS:
            cv2.imshow('Face Detector', frame)

        c = cv2.waitKey(1)
        ## S 'key'
        if c == 27:
            break
        
        
    except KeyboardInterrupt as e:
        raise e
    except AttributeError as e:
        logging.error("Camera failed. Retrying in 5 seconds...")
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
    finally:
        # Record the time taken to process the frame
        if start_time and args.benchmark:
            logging.debug("Frame processed in " + str(time.time() - start_time) + " seconds")
        pass
        
cap.release()
        
        
            

        
cv2.destroyAllWindows()