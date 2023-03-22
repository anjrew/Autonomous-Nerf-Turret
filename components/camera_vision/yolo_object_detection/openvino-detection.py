import cv2
import numpy as np
import sys
import os
import numpy as np
from typing import List, Tuple, Dict, Any


from openvino.inference_engine import IECore # type: ignore
directory_path = os.path.dirname(os.path.abspath(__file__))
sys.path.append(directory_path + '/../..')


def yolo_post_processing(outputs: Dict[str, np.ndarray],
                         anchors: List[Tuple[float, float]],
                         num_classes: int,
                         input_shape: Tuple[int, int],
                         conf_threshold: float = 0.7,
                         iou_threshold: float = 0.4) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:

    boxes = []
    confidences = []
    class_ids = []
    
    for output in outputs.values():
        # Reshape the output
        output = output.reshape((output.shape[0], -1, num_classes + 5))
        
        # Calculate the absolute coordinates, confidence scores, and class probabilities
        grid_size = int(np.sqrt(output.shape[1]))
        cell_size = input_shape[0] / grid_size
        anchors = np.array(anchors).reshape(-1, 2)
        
        tx, ty, tw, th = np.split(output[..., :4], 4, axis=-1)
        cx, cy = np.meshgrid(np.arange(grid_size), np.arange(grid_size))
        bx = (sigmoid(tx) + cx) * cell_size
        by = (sigmoid(ty) + cy) * cell_size
        bw = np.exp(tw) * anchors[:, 0:1] * cell_size
        bh = np.exp(th) * anchors[:, 1:2] * cell_size
        
        box_confidence = sigmoid(output[..., 4:5])
        box_class_probs = sigmoid(output[..., 5:])
        
        # Filter out boxes with low confidence scores
        box_scores = box_confidence * box_class_probs
        box_classes = np.argmax(box_scores, axis=-1)
        box_class_scores = np.max(box_scores, axis=-1)
        pos = np.where(box_class_scores >= conf_threshold)
        
        # Extract the boxes, confidences, and class_ids
        boxes.append(np.column_stack((bx[pos], by[pos], bw[pos], bh[pos])))
        confidences.append(box_class_scores[pos])
        class_ids.append(box_classes[pos])
    
    # Concatenate results from all output layers
    boxes = np.concatenate(boxes)
    confidences = np.concatenate(confidences)
    class_ids = np.concatenate(class_ids)
    
    # Perform non-maximum suppression
    indices = cv2.dnn.NMSBoxes(boxes.tolist(), confidences.tolist(), conf_threshold, iou_threshold)
    boxes = boxes[indices.ravel()]
    confidences = confidences[indices.ravel()]
    class_ids = class_ids[indices.ravel()]
    
    return boxes, confidences, class_ids

def sigmoid(x):
    return 1 / (1 + np.exp(-x))


# Load the model
model_xml = f"{directory_path}/yolov8n_openvino_model/yolov8n.xml"
model_bin = f"{directory_path}/yolov8n_openvino_model/yolov8n.bin"

ie = IECore()
net = ie.read_network(model=model_xml, weights=model_bin)
exec_net = ie.load_network(network=net, device_name="CPU")

# Prepare input
input_layer = next(iter(net.input_info))
input_shape = (net.input_info[input_layer].tensor_desc.dims[3], net.input_info[input_layer].tensor_desc.dims[2])

output_layer = next(iter(net.outputs))
output_layer_names = list(net.outputs.keys())
print("Model labels: ", output_layer_names)

image = cv2.imread(f"{directory_path}/bus.jpg")
image = cv2.resize(image, input_shape)
image = image.transpose((2, 0, 1))  # Change data layout from HWC to CHW
image = np.expand_dims(image, axis=0)

# Run inference
res = exec_net.infer(inputs={input_layer: image})

# Process results
output = res[output_layer]
print("Output: ", output)
print("Found ", len(output), "results")
 # print("Results here", results)


for result in output:
    print("Result length", result.shape )
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

from ultralytics.yolo.utils import ROOT, yaml_load
from ultralytics.yolo.utils.checks import check_yaml

CLASSES = yaml_load(check_yaml('coco128.yaml'))['names']

colors = np.random.uniform(0, 255, size=(len(CLASSES), 3))
    
post_processed = yolo_post_processing(res, anchors, len(CLASSES), input_shape, conf_threshold=0.7)

