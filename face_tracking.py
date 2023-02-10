import cv2
import numpy as np
import face_recognition



cap = cv2.VideoCapture(0)
scaling_factor = 0.5
process_this_frame = True
face_locations = []

while True:
    ret, frame = cap.read()
    
    if process_this_frame:
    
        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
   
        face_locations = face_recognition.face_locations(small_frame)

    process_this_frame = not process_this_frame
    
    for top, right, bottom, left in face_locations:
        # Scale back up face locations since the frame we detected in was scaled to 1/4 size
        top *= 4
        right *= 4
        bottom *= 4
        left *= 4

        # Draw a box around the face
        cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)

        # Draw a label with a name below the face
        cv2.rectangle(frame, (left, bottom - 35), (right, bottom), (0, 0, 255), cv2.FILLED)
        font = cv2.FONT_HERSHEY_DUPLEX
        cv2.putText(frame, "Human", (left + 6, bottom - 6), font, 1.0, (255, 255, 255), 1)
        
    
    cv2.imshow('Face Detector', frame)

    c = cv2.waitKey(1)
    ## S 'key'
    if c == 27:
        break

cap.release()
cv2.destroyAllWindows()