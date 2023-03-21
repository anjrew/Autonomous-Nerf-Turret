import os
import sys
from typing import Tuple
directory_path = os.path.dirname(os.path.abspath(__file__))
sys.path.append(directory_path + '/..')
from object_detection import ObjectDetector
import cv2.dnn #type: ignore
import numpy as np
from ultralytics.yolo.utils import ROOT, yaml_load
from ultralytics.yolo.utils.checks import check_yaml
import logging


class ONNXObjectDetector(ObjectDetector):
    
    
    def __init__(self, model_name: str = "yolov8n.onnx") -> None:
        self.model: cv2.dnn.Net = cv2.dnn.readNetFromONNX(f'{directory_path}/{model_name}')
        self.class_names = yaml_load(check_yaml('coco128.yaml'))['names']
        logging.debug("Detecting from : " + str(self.class_names))
        self.colors = np.random.uniform(0, 255, size=(len(self.class_names), 3))
        self.class_name_id = { v:k for k, v in self.class_names.items() } # type: ignore

    
    def get_color_for_class_name(self, class_name: str) -> Tuple[int, int, int]:
        """Gets the color for a particular class by name"""                
        return self.colors[self.class_name_id[class_name]]
    
    def draw_bounding_box(self, img, class_id, confidence, x, y, x_plus_w, y_plus_h):
        label = f'{self.class_names[class_id]} ({confidence:.2f})'
        color = self.colors[class_id]
        cv2.rectangle(img, (x, y), (x_plus_w, y_plus_h), color, 2)
        cv2.putText(img, label, (x - 10, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

    def detect(self, original_image: np.ndarray) -> list:
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
            box = boxes[index]
            detection = {
                'class_name': self.class_names[class_ids[index]],
                'confidence': scores[index],
                'box': box,
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