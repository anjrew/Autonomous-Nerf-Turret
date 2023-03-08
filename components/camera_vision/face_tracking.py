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

parser.add_argument("--port", help="Set the mqtt server port.", default=6565, type=int)
parser.add_argument("--host", help="Set the mqtt server hostname.", default="localhost")
parser.add_argument("--log-level", help="Set the logging level by integer value.", default=logging.DEBUG, type=int)

args = parser.parse_args()

logging.basicConfig(level=args.log_level)

## Setup ready to send data to subscribers
HOST = args.host  # IP address of the server
PORT = args.port  # Port number to listen on


# Set this value to change the Camera ID
CAMERA_ID = args.camera
CROSS_HAIR_SIZE = args.crosshair_size


cap = cv2.VideoCapture(CAMERA_ID)
scaling_factor = 0.5
process_this_frame = True
face_locations = []
sock = None

def try_to_connect_to_server():
    logging.info(f"Connecting to host{HOST, PORT}")
    try:
        global sock
        # Create a new socket and connect to the server
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((HOST, PORT))
    except:
        time.sleep(5)
        logging.error("Connecting socket failed. Attempting to try again")
        try_to_connect_to_server()
        pass


while True:
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
            
            # Draw a box around the face
            cv2.rectangle(frame, (left, top), (right, bottom), target_highlight_color, 2)
            
            box_center_x = (left + right) / 2
            box_center_y = (top + bottom) / 2
            box_width = right - left
            
            movement_vector = [box_center_x - center_x, box_center_y - center_y]
            
            distance = math.sqrt(movement_vector[0]**2 + movement_vector[1]**2)
            
            # Draw a label with a name below the face
            cv2.rectangle(frame, (left, bottom - 35), (right, bottom), target_highlight_color, cv2.FILLED)
            font = cv2.FONT_HERSHEY_DUPLEX
            
            lock_text = "Lock" if is_on_target else f""
            
            targets.append({ "vec_delta": movement_vector, "locked": is_on_target, "box": [left, top, right, bottom]})
            
            font_size = 445
            
            cv2.putText(frame, f"{lock_text} {movement_vector} {distance:.2f}", (left + 6, bottom - 6), font, box_width/font_size, (255, 255, 255), 1)
            
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
            if sock:
                try:
                    sock.sendall(json_data) # Send the byte string to the server
                except Exception as e:
                    logging.error(f"Error sending data to server: {e}")
                    try_to_connect_to_server()
                    pass
            else:
                logging.error("No socket detected")
                try_to_connect_to_server()
            
        
        cv2.imshow('Face Detector', frame)

        c = cv2.waitKey(1)
        ## S 'key'
        if c == 27:
            break
    
    except:
        print("Socket connection lost. Retrying in 5 seconds...")
        time.sleep(5)
        sock = None
        try_to_connect_to_server()
        
cap.release()
        
        
            

        
cv2.destroyAllWindows()