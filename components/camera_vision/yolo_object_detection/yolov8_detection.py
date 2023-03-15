import time
from typing import List, Union
import numpy as np
from ultralytics import YOLO, yolo
from ultralytics.yolo.engine.results import Results as YoloResults, Masks, Boxes
from yolo_utils import map_log_level
import logging
import argparse


class ObjectDetector:
    """Detect objects of multiple types Using YOLOv8
    """
    
    def __init__(self, model_name: str = "yolov8n-seg.pt") -> None:
        self.model = YOLO(model_name)  # load an official model
        self.class_names = self.model.names or {}
        logging.debug("Detecting from : " + str(self.class_names))
        self.colors = np.random.uniform(0, 255, size=(len(self.class_names), 3))
        self._class_name_id = { v:k for k, v in self.class_names.items() }
        
        
    def get_color_for_class_name(self, class_name: str) -> np.ndarray:
        """Gets the color for a particular class by name"""                
        return detector.colors[self._class_name_id[class_name]]


    # def perform_yolov8_segmentation(uri: str) -> List[YoloResults]:
    def perform_yolov8_segmentation(self, source: Union[str, int, np.ndarray], confidence: float, save=False, save_txt=False) -> List[dict]:

        # return model.predict(uri, save=True, save_txt=True, conf=0.8)
        results: List[dict] = []

        detections = self.model.predict(source, save=save, save_txt=save_txt, conf=confidence)
        
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
                        'mask': detection.masks[i].numpy(),
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
    parser.add_argument("--image-compression", "-ic", 
                        help="The amount to compress the image. Eg give a value o2 2 and the image for inference will have half the pixels", type=int, default=1)

    
    args = parser.parse_args()
    
    
    detector = ObjectDetector()
    
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
                
                results = detector.perform_yolov8_segmentation(process_frame, args.confidence)
                
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

                # mask = np.array(result['mask'], dtype=np.int8)
                mask = np.array(cv2.resize(result['mask'], frame.shape[1], frame.shape[0]), dtype=np.int8)
                # Draw a mask
                if len(mask.shape) == 2:
                    mask = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
                
                
                frame = cv2.bitwise_and(frame ,mask)
                    
                
                # Draw a bounding box
                cv2.rectangle(frame, (int(left), int(top)), (int(right), int(bottom)), target_highlight_color, 2)
                
                # Draw a label with a name below the face
                cv2.rectangle(frame, (left, top - 55), (right, top), target_highlight_color, cv2.FILLED)
                
                font_size = 445
                font = cv2.FONT_HERSHEY_DUPLEX
                box_text = f'{id} {confidence:.2f}'
                cv2.putText(frame, box_text, (left + 6, top - 6), font, box_width/font_size, (255, 255, 255) if False else (10, 10, 10), 1)
                
            
            cv2.imshow('YOLO Detector', frame)
            c = cv2.waitKey(1)
            ## S 'key'
            if c == 27:
                break
            
    else:
    
        results = detector.perform_yolov8_segmentation("https://ultralytics.com/images/bus.jpg", args.confidence)
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