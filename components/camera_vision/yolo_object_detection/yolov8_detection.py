from ultralytics import YOLO

# Load a model
model = YOLO("yolov8n.pt")  # load an official model
# model = YOLO("yolov8n-seg.pt")  # load an official model
# model = YOLO("yolov8n-cls.pt")  # load an official model
# results = model("https://ultralytics.com/images/bus.jpg")

results = model.predict("https://ultralytics.com/images/bus.jpg", save=True, save_txt=True, conf=0.8)

# print('\nresults type', type(results)   )
# print('\nresult type', type(results[0])   )
# print('\nresults[0]', results[0]   )
# print('\nresults', results   )
print('Result amount', len(results))
print('Result props', )
keys = [key for key in dir(results[0]) if not key.startswith('_')]
print(keys)

print('\nBoxes type ', type(results[0].boxes))
print('\nBoxes props ', [key for key in dir(results[0].boxes) if not key.startswith('_')])
print('\nBoxes 0 ', results[0].boxes[0])
print('\nBoxes found ', results[0].boxes)


# print('\nMasks type ', type(results[0].masks))
# print('\nMasks 0 ', results[0].masks[0])
# print('\nMasks found ', results[0].masks)

# print('\nProbs found type ', type(results[0].probs))
# print('\nProbs 0 ', results[0].probs[0])
# print('\nProbs found ', results[0].probs)


for result in results:
    boxes = result.boxes  # Boxes object for bbox outputs
    cls = result.boxes.cls
    print('Class', cls)
    print('boxes', result.boxes[0])
    masks = result.masks  # Masks object for segmenation masks outputs
    probs = result.probs  # Class probabilities for classification outputs