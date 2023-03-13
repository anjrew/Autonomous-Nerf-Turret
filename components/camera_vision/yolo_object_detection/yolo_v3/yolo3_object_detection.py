# import required packages
from typing import List
import cv2
import argparse
import numpy as np


class YoloObjectDetection:
    
    
    def __init__(self, classes_path: str, weights_path: str, config_path: str, scale = 0.00392):
        self.classes_path = classes_path
        with open(classes_path, 'r') as f:
            self.classes = [line.strip() for line in f.readlines()]
            
        self.COLORS = np.random.uniform(0, 255, size=(len(self.classes), 3))
        # read pre-trained model and config file
        self.net = cv2.dnn.readNet(weights_path, config_path)
        self.scale = scale        


    def process_image(self, image:np.ndarray) -> tuple:

        width = image.shape[1]
        height = image.shape[0]

        # create input blob 
        blob = cv2.dnn.blobFromImage(image, self.scale, (416,416), (0,0,0), True, crop=False)

        # set input blob for the network
        self.net.setInput(blob)
        
        print('\n Processing')
        print(self.net)
        output_layers = self.get_output_layers(self.net)
        print('Got output layers')
        outs = self.net.forward(output_layers)
        print('\n OUts')
        print(outs)
        class_ids = []
        confidences = []
        boxes = []
        conf_threshold = 0.5
        nms_threshold = 0.4


        for out in outs:
            for detection in out:
                scores = detection[5:]
                class_id = np.argmax(scores)
                confidence = scores[class_id]
                if confidence > 0.5:
                    center_x = int(detection[0] * width)
                    center_y = int(detection[1] * height)
                    w = int(detection[2] * width)
                    h = int(detection[3] * height)
                    x = center_x - w / 2
                    y = center_y - h / 2
                    class_ids.append(class_id)
                    confidences.append(float(confidence))
                    boxes.append([x, y, w, h])


        indices = cv2.dnn.NMSBoxes(boxes, confidences, conf_threshold, nms_threshold)
        print('\n indices')
        print(indices)
        return indices, boxes, class_ids, confidences
                
    
    # function to get the output layer names 
    # in the architecture
    def get_output_layers(self, net):
        
        layer_names = net.getLayerNames()
        print("Got layer names")
        print(layer_names)
        
        unconnected_out_layers = net.getUnconnectedOutLayers()
        print('got unconnected out layers', unconnected_out_layers)
        output_layers = []
        for i in unconnected_out_layers:
            print("Processign I", i)
            
            layer_index = i[0] - 1
            print('Layer_name index', layer_index)
            layer = layer_names[layer_index ]
            print('Found layer', layer)
            output_layers.append(layer)
        print("Got layers")
        return output_layers

    # function to draw bounding box on the detected object with class name
    def draw_bounding_box(self, img, class_id, confidence, x, y, x_plus_w, y_plus_h):

        label = str(self.classes[class_id])

        color = self.COLORS[class_id]

        cv2.rectangle(img, (x,y), (x_plus_w,y_plus_h), color, 2)

        cv2.putText(img, label, (x-10,y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        
        
    def draw_prediction(self, img, class_id, confidence, x, y, x_plus_w, y_plus_h):

        label = str(self.classes[class_id]) + str(confidence)
 
        color = self.COLORS[class_id]

        cv2.rectangle(img, (x,y), (x_plus_w,y_plus_h), color, 2)

        cv2.putText(img, label, (x-10,y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        
        return img
        

    def draw_all_predictions(self, indices: list, boxes: list, class_ids: list, confidences: list):
        for i in indices:
            try:
                box = boxes[i]
            except:
                i = i[0]
                box = boxes[i]
            
            x = box[0] # Left
            y = box[1] # Top
            w = box[2] # Width
            h = box[3] # Height
            self.draw_prediction(image, class_ids[i], confidences[i], round(x), round(y), round(x+w), round(y+h))
        
        
    
if __name__ == "__main__":
    # handle command line arguments
    ap = argparse.ArgumentParser()
    ap.add_argument('-i', '--image-path', required=True,
                    help = 'path to input image')
    ap.add_argument('-c', '--config-path', required=True,  default="yolov3.cfg",
                    help = 'path to yolo config file')
    ap.add_argument('-w', '--weights-path', required=True, default="yolov3.weights",
                    help = 'path to yolo pre-trained weights')
    ap.add_argument('-cl', '--classes-path', required=True, default="yolov3_classes.txt",
                    help = 'path to text file containing class names')
    args = ap.parse_args()
    print('Args', args)
    yolo_od = YoloObjectDetection(args.classes_path, args.weights_path, args.config_path)

    # read input image
    image = cv2.imread(args.image_path)
    
    indices, boxes, class_ids, confidences = yolo_od.process_image(image)
    
    img_predicted = yolo_od.draw_all_predictions( indices, boxes, class_ids, confidences)
    
    cv2.imshow("object detection", image)
    cv2.waitKey()
        
    cv2.destroyAllWindows()