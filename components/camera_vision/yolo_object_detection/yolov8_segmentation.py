from typing import List
import numpy as np
from ultralytics import YOLO, yolo
from ultralytics.yolo.engine.results import Results as YoloResults, Masks, Boxes


class YoloV8SegmentationBox:
    
    def __init__(self, box: List, mask: List, class_name: str):
        self.box = box
        self.mask = mask
        self.class_name = class_name



# Load a model
model = YOLO("yolov8n-seg.pt")  # load an official model
print('\nBoxes props ', [key for key in dir(model) if not key.startswith('_')])
class_names = model.names or []
print(class_names)
# def perform_yolov8_segmentation(uri: str) -> List[YoloResults]:
def perform_yolov8_segmentation(uri: str) -> List[dict]:

    # return model.predict(uri, save=True, save_txt=True, conf=0.8)
    results: List[dict] = []

    detections = model.predict(uri, save=True, save_txt=True, conf=0.8)
    
    
    for detection in detections:
        if hasattr(detection, 'boxes') and detection.boxes:
            print('detection: ', [key for key in dir(detection) if not key.startswith('_')])
            # print(len(detection.masks))
            boxes = detection.boxes
            box_classes = detection.boxes.cls
            # print('Box classes', box_classes)
            for i, box in enumerate(boxes): # type: ignore
                #   boxes (torch.Tensor) or (numpy.ndarray): A tensor or numpy array containing the detection boxes,
                #   with shape (num_boxes, 6). The last two columns should contain confidence and class values.
                
                print('box', box)
                cls = class_names[box_classes[i].item()]
                # print('\nbox', dir(box))
                # print('\mask', dir(detection.masks[i].numpy))
                # Get the bounding boxes
                # box = box.xyxy.numpy()

                box = box.data.tolist()[0]
                print('box', box)
                # Extract the height, width, top, bottom, left, and right values
                top = box[1]
                right = box[2]
                bottom = box[3]
                left = box[0]
                height = bottom - top
                width = right - left
                confidence = box[4]
                class_v = box[5]
                
                print('t', top, 'r', right, 'b', bottom, 'l', left, 'h', height, 'w', width, 'c', confidence, 'cl', class_v)

                results.append({
                    'box': box.numpy,
                    'mask': detection.masks[i].numpy,
                    'class_name':cls
                })
    return results

# # print('\nresults type', type(results)   )
# # print('\nresult type', type(results[0])   )
# # print('\nresults[0]', results[0]   )
# # print('\nresults', results   )
# print('Result amount', len(results))
# print('Result props', )
# keys = [key for key in dir(results[0]) if not key.startswith('_')]
# print(keys)

# print('\nBoxes type ', type(results[0].boxes))
# print('\nBoxes props ', [key for key in dir(results[0].boxes) if not key.startswith('_')])
# print('\nBoxes 0 ', results[0].boxes[0])
# print('\nBoxes found ', results[0].boxes)


# print('\nMasks type ', type(results[0].masks))
# print('\nMasks 0 ', results[0].masks[0])
# print('\nMasks found ', results[0].masks)

# print('\nProbs found type ', type(results[0].probs))
# print('\nProbs 0 ', results[0].probs[0])
# print('\nProbs found ', results[0].probs)



    
    
if __name__ == '__main__':
    
    
    results = perform_yolov8_segmentation("https://ultralytics.com/images/bus.jpg")
    # print("Results here", results)
    for result in results:
        print('\n', result)
    #     if hasattr(result, 'boxes') and result.boxes:
    #         boxes = result.boxes
    #         box_classes = result.boxes.cls
    #         print('Box classes', box_classes)
    #         for i, box in enumerate(boxes): # type: ignore
    #             print('box', box)
    #             cls = class_names[box_classes[i].item()]
    #             print('Seen Class', cls)
                # print('boxes', result.boxes[0])
                # masks = result.masks  # Masks object for segmentation masks outputs
                
                # print('segmentation', result.masks[0])
                # probs = result.probs  # Class probabilities for classification outputs