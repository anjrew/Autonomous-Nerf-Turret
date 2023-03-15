import sys
import os
directory_path = os.path.dirname(os.path.abspath(__file__))
sys.path.append(directory_path + '/../..')

import time
from typing import List, Union
import numpy as np
from ultralytics import YOLO
from nerf_turret_utils.args_utils import map_log_level
import logging
import onnxruntime as ort





class ObjectDetector:
    """Detect objects of multiple types Using YOLOv8
    """
    
    def __init__(self, model_name: str ="yolov8n-seg.onnx") -> None:
        self.model = ort.InferenceSession(model_name)
        # Get the output names and shapes
        outputs = self.model.get_outputs()
        self.output_names = [output.name for output in outputs]
        class_names = { i:output.name for i, output in enumerate(outputs) }
        self.class_names = class_names or {}
        logging.debug("Detecting from : " + str(self.class_names))
        self.colors = np.random.uniform(0, 255, size=(len(self.class_names), 3))
        self._class_name_id = { v:k for k, v in self.class_names.items() }
        
        
    def get_color_for_class_name(self, class_name: str) -> np.ndarray:
        """Gets the color for a particular class by name"""                
        return detector.colors[self._class_name_id[class_name]]


    # def perform_yolov8_segmentation(uri: str) -> List[YoloResults]:
    def detect(self, source: Union[str, int, np.ndarray]) -> List[dict]:
        """
        Performs YOLOv8 segmentation on an image or video frame.

        Args:
            source: The source of the image or video frame to be segmented.
                Can be a file path (str), camera ID (int), or a NumPy array containing the image data.
            confidence: The minimum confidence level required for a detection to be included in the results.
            save: Whether to save the results to an image file (default=False).
            save_txt: Whether to save the results to a text file (default=False).

        Returns:
            A list of dictionaries containing the detection results.
                Each dictionary contains the following keys:
                - 'box': A list of four integers [left, top, right, bottom] representing the bounding box coordinates.
                - 'mask': A NumPy array containing the segmentation mask for the detected object.
                - 'class_name': A string representing the name of the detected object class.
                - 'confidence': A float representing the confidence level of the detection.
        """
        image = None
        if type(source) == str:
            image = cv2.imread(source) # type: ignore
        
        # Convert the image to a NumPy array
        image = np.array(image)

        # Reshape the array to match the input shape of the ONNX model
        # image = image.transpose((2, 0, 1))
        image = image.reshape(image.shape)

        results: List[dict] = []

        # Convert the array to a tensor and run the inference using the ONNX model
        ort_inputs = {self.model.get_inputs()[0].name: image}
        # print('ort_inputs', ort_inputs)
        detections = self.model.run(self.output_names, ort_inputs)
        
        for detection in detections:
            if hasattr(detection, 'boxes') and detection.boxes:
                boxes = detection.boxes
                for i, box in enumerate(boxes): # type: ignore
                    #   boxes (torch.Tensor) or (numpy.ndarray): A tensor or numpy array containing the detection boxes,
                    #   with shape (num_boxes, 6). The last two columns should contain confidence and class values.
                    box = box.data.tolist()[0]
                    # Extract the height, width, top, bottom, left, and right values
                    left = box[0]
                    top = box[1]
                    right = box[2]
                    bottom = box[3]
                    confidence = box[4]
                  
                    results.append({
                        'box': [ int(left), int(top), int(right), int(bottom) ],
                        'mask': detection.masks[i].numpy().data,
                        'class_name': self.class_names[int(box[5])],
                        'confidence': box[4]
                    })
                    
        return results


    
if __name__ == '__main__':
    
    from argparse import ArgumentParser
    import cv2


    parser = ArgumentParser(description="Tracks multiple objects with bounding boxes, segmentation and classification")

    parser.add_argument("--log-level", "-ll", help="Set the logging level by integer value. Default INFO", default=logging.INFO, type=map_log_level)
    parser.add_argument("--confidence", "-c", help="Set the confidence from low(0) to high (1) as a float for detection. Default 0.8", default=0.8, type=float)
    parser.add_argument("--camera", "-cam", help="Weather or not to use the camera for testing purposes", action='store_true', default=False)
    parser.add_argument("--skip-frames", "-sk", help="Skip x amount of frames to increase performance", type=int, default=0)
    parser.add_argument("--model-name", "-mn", help="The model name to use for detection", type=str, default="yolov8n-seg.onnx")
    parser.add_argument("--image-compression", "-ic", 
                        help="The amount to compress the image. Eg give a value o2 2 and the image for inference will have half the pixels", type=int, default=1)
    parser.add_argument("--draw-mask", "-dm", 
                        help="Whether a mask should be drawn ", type=bool, default=True)
    parser.add_argument("--draw-box", "-db", 
                        help="Whether a box should be drawn ", type=bool, default=True)
    parser.add_argument("--draw-crosshair", "-dc", 
                        help="Whether a crosshair should be drawn ", type=bool, default=True)

    
    args = parser.parse_args()
    
    
    detector = ObjectDetector(model_name=args.model_name)
    
    skip_frames =  args.skip_frames + 1
    frame_count = 0
    results = [] # The results are cached to be used in the next frame when skipping frames
    
    if args.camera:
        cap = cv2.VideoCapture(0)
        
        frame = None
        
        while True:
            frame_count += 1
            
            ret, frame = cap.read()
            if not ret:
                logging.warning("Could not connect to the camera. Trying again in 3 seconds...")
                # If could not connect to camera go to the next frame
                time.sleep(3)
                continue
            
            # Get the image height and width
            height, width, _ = frame.shape
            
            if frame_count % skip_frames == 0:
                
                process_frame = frame
                if args.image_compression > 1:
                    process_frame = cv2.resize(frame, (0, 0), fx=1/args.image_compression, fy=1/args.image_compression) #type: ignore
                
                results = detector.detect(process_frame)
                
            for result in results:
                
                left, top, right, bottom = result['box']
                top *= args.image_compression
                right *= args.image_compression
                bottom *= args.image_compression
                left *= args.image_compression
                box_height = bottom - top
                box_width = right - left
                
                id = result['class_name']
                confidence = result['confidence']
            
                target_highlight_color = detector.get_color_for_class_name(id)
                
                mask = result.get('mask', np.array([]))
                
                if args.draw_mask:
                    mask = cv2.resize(mask, (frame.shape[1], frame.shape[0]))
                    # Draw a mask
                    if len(mask.shape) == 2:

                        # Create a color mask using the segmented area
                        color_mask = np.zeros_like(frame)
                        color_mask[mask == 1] = target_highlight_color  # Set the color for the segmented area

                        # Blend the color mask with the original image
                        alpha = 0.5  # Adjust the alpha value for the blending
                        beta = 1 - alpha
                        frame = cv2.addWeighted(frame, alpha, color_mask, beta, 0)
                    
                    
                if args.draw_box:
                    
                    # Draw a bounding box
                    cv2.rectangle(frame, (int(left), int(top)), (int(right), int(bottom)), target_highlight_color, 2)
                    
                    # Draw a label with a name below the face
                    cv2.rectangle(frame, (left, top - 55), (right, top), target_highlight_color, cv2.FILLED)
                    
                    font_size = 445
                    font = cv2.FONT_HERSHEY_DUPLEX
                    box_text = f'{id} {confidence:.2f}'
                    cv2.putText(frame, box_text, (left + 6, top - 6), font, box_width/font_size, (255, 255, 255) if False else (10, 10, 10), 1)
                
                
                # Get the center position of the image
                center = (frame.shape[1]//2, frame.shape[0]//2)

                # Check if the center position is within the segmented masked area
                is_on_target = mask[center[1], center[0]] == 1
                
                if args.draw_crosshair:
                    # Draw a crosshair at the center of the image
                    center = (frame.shape[1]//2, frame.shape[0]//2)
                    length = 20
                    color = (0, 0, 255) if is_on_target else (0, 255, 0) # Set the color to red
                    thickness = 2
                    cv2.line(frame, (center[0]-length, center[1]), (center[0]+length, center[1]), color, thickness)
                    cv2.line(frame, (center[0], center[1]-length), (center[0], center[1]+length), color, thickness)

                
                
            cv2.imshow('YOLO Detector', frame)
            c = cv2.waitKey(1)
            ## S 'key'
            if c == 27:
                break
            
    else:
    
        results = detector.detect("https://ultralytics.com/images/bus.jpg")
        # print("Results here", results)
        for result in results:
            print('\n', result)
            
            if hasattr(result, 'boxes') and result.boxes: # type: ignore
                boxes = result.boxes # type: ignore
                box_classes = result.boxes.cls # type: ignore
                print('Box classes', box_classes)
                # for i, box in enumerate(boxes): # type: ignore
                #     print('box', box)
                #     cls = class_names[box_classes[i].item()]
                #     print('Seen Class', cls)
                #     print('boxes', result.boxes[0])
                #     masks = result.masks  # Masks object for segmentation masks outputs
                    
                    # print('segmentation', result.masks[0])
                    # probs = result.probs  # Class probabilities for classification outputs