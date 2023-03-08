import time
import cv2
import face_recognition
from argparse import ArgumentParser
import math
import logging
import socket
import json

parser = ArgumentParser(description="Track faces with bounding boxes")

parser.add_argument('--camera', '-c', type=int, default=0, help="Choose the camera for tracking" )

parser.add_argument('--crosshair_size', '-ch', type=int, default=10, help="The size of the crosshair" )

parser.add_argument("--port", help="Set the web socket server port to send messages to.", default=6565, type=int)
parser.add_argument("--host", help="Set the web socket server hostname to send messages to.", default="localhost")

parser.add_argument("--log-level", help="Set the logging level by integer value.", default=logging.DEBUG, type=int)
parser.add_argument("--delay", help="Delay to limit the data flow into the websocket server.", default=0.1, type=int)
parser.add_argument("--headless", help="Wether to run the service in headless mode.", action='store_true', default=False)


args = parser.parse_args()

logging.basicConfig(level=args.log_level)

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
sock = None
face_locations = []

def try_to_connect_to_server():
    logging.info(f"Connecting to host{HOST, PORT}")
    try:
        global sock
        # Create a new socket and connect to the server
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((HOST, PORT))
        logging.info(f"Successfully Connected to socket @ {HOST, PORT}")
    except:
        # time.sleep(5)
        sock = None
        logging.error("Failed on trying to connect to socket. Attempting to try again")
        # try_to_connect_to_server()
        pass


while True:
    time.sleep(args.delay)
    if not sock:
        try_to_connect_to_server()
        
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
            target_highlight_color = (0, 0, 255) if is_on_target else (0, 255, 0)
            
            if not HEADLESS:
                # Draw a box around the face
                cv2.rectangle(frame, (left, top), (right, bottom), target_highlight_color, 2)
            
            box_center_x = (left + right) / 2
            box_center_y = (top + bottom) / 2
            box_width = right - left
            
            movement_vector = [box_center_x - center_x, box_center_y - center_y]
            
            distance = math.sqrt(movement_vector[0]**2 + movement_vector[1]**2)
            
            
            lock_text = "Lock" if is_on_target else f""
            
            targets.append({ "vec_delta": movement_vector, "locked": is_on_target, "box": [left, top, right, bottom]})
            
            if not HEADLESS:
                font_size = 445
                # Draw a label with a name below the face
                cv2.rectangle(frame, (left, bottom - 35), (right, bottom), target_highlight_color, cv2.FILLED)
                font = cv2.FONT_HERSHEY_DUPLEX
                
                cv2.putText(frame, f"{lock_text} {movement_vector} {distance:.2f}", (left + 6, bottom - 6), font, box_width/font_size, (255, 255, 255), 1)
                
                # Draw a red horizontal line through the center
                cv2.line(frame, (center_x - CROSS_HAIR_SIZE, center_y), (center_x + CROSS_HAIR_SIZE, center_y), target_highlight_color, target_highlight_size)
                # Draw a red vertical line through the center
                cv2.line(frame, (center_x, center_y - CROSS_HAIR_SIZE), (center_x, center_y + CROSS_HAIR_SIZE), target_highlight_color, target_highlight_size)
        
        # print("len(targets)", len(targets))
        if len(targets) > 0:
            data = {
                "targets": targets,
                "heading_vect": [center_x, center_y],
                "view_dimensions": [width, height],
            }
            json_data = json.dumps(data).encode('utf-8') # Encode the JSON object as a byte string
            if sock:
                print('Sending data to server', json_data)
                sock.sendall(json_data) # Send the byte string to the server
                
        else:
            if sock:
                sock.sendall(json.dumps({"targets": []}).encode('utf-8'))
            
        
        cv2.imshow('Face Detector', frame)

        c = cv2.waitKey(1)
        ## S 'key'
        if c == 27:
            break
    except KeyboardInterrupt as e:
        raise e 
    except BrokenPipeError as e:
        logging.error("Socket connection lost. Retrying in 5 seconds...")
        sock = None
        pass 
    except ConnectionResetError as e:
        print("Socket connection lost. Retrying in 5 seconds...")
        sock = None
        # try_to_connect_to_server()
        pass

        
cap.release()
        
        
            

        
cv2.destroyAllWindows()