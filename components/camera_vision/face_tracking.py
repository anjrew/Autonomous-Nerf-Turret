import cv2
import face_recognition
from argparse import ArgumentParser
import math

parser = ArgumentParser(description="Track faces with bounding boxes")

parser.add_argument('--camera', '-c', type=int, default=0, help="Choose the camera for tracking" )

parser.add_argument('--crosshair_size', '-ch', type=int, default=10, help="The size of the crosshair" )

parser.add_argument('--center_threshold', '-t', type=int, default=5, 
                    help="""
                    The threshold of how accurate the gun will try to get the target in the center of the crosshair in pixels.
                    """ )

parser.add_argument('--vert_offset', '-v', type=int, default=5, 
                    help="""
                    The vertical offset the gun will aim for from the center of the crosshair in pixels so gravity is taken into account.
                    """ )

parser.add_argument('--target_padding', '-p', type=int, default=10,
                    help="""
                    The amount of padding around the target bounding box in pixels that the gun will ignore before shooting
                    """  
)

args = parser.parse_args()

# Set this value to change the Camera ID
CAMERA_ID = args.camera
CROSS_HAIR_SIZE = args.crosshair_size
CENTER_THRESHOLD = args.center_threshold
VERT_OFFSET = args.vert_offset

cap = cv2.VideoCapture(CAMERA_ID)
scaling_factor = 0.5
process_this_frame = True
face_locations = []

while True:
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
        
        font_size = 445
        
        cv2.putText(frame, f"{lock_text} {movement_vector} {distance:.2f}", (left + 6, bottom - 6), font, box_width/font_size, (255, 255, 255), 1)
        
        # Draw a red horizontal line through the center
        cv2.line(frame, (center_x - CROSS_HAIR_SIZE, center_y), (center_x + CROSS_HAIR_SIZE, center_y), target_highlight_color, target_highlight_size)

        # Draw a red vertical line through the center
        cv2.line(frame, (center_x, center_y - CROSS_HAIR_SIZE), (center_x, center_y + CROSS_HAIR_SIZE), target_highlight_color, target_highlight_size)
        
    cv2.imshow('Face Detector', frame)

    c = cv2.waitKey(1)
    ## S 'key'
    if c == 27:
        break

cap.release()
cv2.destroyAllWindows()