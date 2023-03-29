import os
import sys
from typing import Any, Dict, List, Tuple
directory_path = os.path.dirname(os.path.abspath(__file__))

sys.path.append(directory_path + '/..')
sys.path.append(directory_path + '/../..')
sys.path.append(directory_path)

import cv2.dnn #type: ignore
import numpy as np
from ultralytics.yolo.utils import ROOT, yaml_load
from ultralytics.yolo.utils.checks import check_yaml
import logging

print(sys.path)
print(directory_path)
from object_detection import ObjectDetector


class ONNXObjectDetector(ObjectDetector):
    """Class to perform object detection using a YOLOv8n model."""

    
    def __init__(self, model_name: str = "yolov8n.onnx") -> None:
        """
        Initializes the object detector with a YOLOv8n model and class names.
        
        Args:
            model_name: Name of the ONNX model file to use.
        """
        self.model: cv2.dnn.Net = cv2.dnn.readNetFromONNX(f'{directory_path}/{model_name}')
        self.class_names = yaml_load(check_yaml('coco128.yaml'))['names'] # type: ignore
        logging.debug("Detecting from : " + str(self.class_names))
        self.colors = np.random.uniform(0, 255, size=(len(self.class_names), 3))
        self.class_name_id = { v:k for k, v in self.class_names.items() } # type: ignore

    
    def get_color_for_class_name(self, class_name: str) -> Tuple[int, int, int]:
        """
        Gets the color for a particular class by name.
        
        Args:
            class_name: The name of the class to get the color for.
        
        Returns:
            A tuple representing the RGB color value for the class.
        """                    
        return tuple(self.colors[self.class_name_id[class_name]])
    
    
    def draw_bounding_box(self, img: np.ndarray, class_id: int, confidence: float, x: int, y: int, x_plus_w: int, y_plus_h: int) -> None:
        """
        Draws a bounding box with label on an image for a detected object.
        
        Args:
            img: The image to draw on.
            class_id: The ID of the class of the detected object.
            confidence: The confidence score of the detection.
            x: The x-coordinate of the top-left corner of the bounding box.
            y: The y-coordinate of the top-left corner of the bounding box.
            x_plus_w: The x-coordinate of the bottom-right corner of the bounding box.
            y_plus_h: The y-coordinate of the bottom-right corner of the bounding box.
        """
        label = f'{self.class_names[class_id]} ({confidence:.2f})'
        color = self.colors[class_id]
        cv2.rectangle(img, (x, y), (x_plus_w, y_plus_h), color, 2)
        cv2.putText(img, label, (x - 10, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)


    def detect(self, original_image: np.ndarray, confidence: float = 0.7) -> List[Dict[str, Any]]:
        """
        Performs object detection on an image.
        
        Args:
            original_image: The image to perform detection on.
        
        Returns:
            A list of dictionaries representing the detected objects. Each dictionary has the following keys:
            - class_name: The name of the class of the detected object.
            - confidence: The confidence score of the detection.
            - box: A list of four values representing the coordinates of the bounding box.
        """
        [height, width, _] = original_image.shape
        length = max((height, width))
        image = np.zeros((length, length, 3), np.uint8)
        image[0:height, 0:width] = original_image
        # scale = length / 640
        blob = cv2.dnn.blobFromImage(image, scalefactor=1 / 255, size=(640, 640))
        self.model.setInput(blob)
        outputs = self.model.forward()

        outputs = np.array([cv2.transpose(outputs[0])])
        rows = outputs.shape[1]

        boxes = []
        scores = []
        class_ids = []

        for i in range(rows):
            classes_scores = outputs[0][i][4:]
            (minScore, maxScore, minClassLoc, (x, maxClassIndex)) = cv2.minMaxLoc(classes_scores)
            if maxScore >= 0.25:
                box = [
                    outputs[0][i][0] - (0.5 * outputs[0][i][2]), outputs[0][i][1] - (0.5 * outputs[0][i][3]),
                    outputs[0][i][2], outputs[0][i][3]]
                boxes.append(box)
                scores.append(maxScore)
                class_ids.append(maxClassIndex)

        result_boxes = cv2.dnn.NMSBoxes(boxes, scores, 0.25, 0.45, 0.5)

        detections = []
        for i in range(len(result_boxes)):
            index = result_boxes[i]
            detector_confidence = scores[index]
            if detector_confidence >= confidence:
                box = boxes[index]
                detection = {
                    'class_name': self.class_names[class_ids[index]],
                    'confidence': detector_confidence,
                    'box': [int(box[0]), int(box[1]), int(box[2]), int(box[3])] ,
                }
                detections.append(detection)

        return detections



if __name__ == '__main__':
    
    image: np.ndarray = cv2.imread(str(ROOT / 'assets/bus.jpg'))
    [height, width, _] = image.shape
    length = max((height, width))
    scale = length / 640
    
    detector = ONNXObjectDetector() 
    
    for detection in detector.detect(image):
        box = detection['box']
        detector.draw_bounding_box(
            image, 
            detector.class_name_id[detection['class_name']], 
            detection['confidence'], 
            round(box[0] * scale), 
            round(box[1] * scale),
            round((box[0] + box[2]) * scale), 
            round((box[1] + box[3]) * scale)
        )
    
    cv2.imshow('image', image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()