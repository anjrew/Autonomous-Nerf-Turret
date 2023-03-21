# Vision

This code includes computer vision algorithms for object detection and tracking. 

## Info
  - A [video](https://www.youtube.com/watch?v=5yPeKQzCPdI&list=PLVlbw1IZ2gnswgwYW9jXkEz43f3j7qs25&index=77) of how to use the face recognition library 
  - A guide on setting up the [YOLO object detection](https://docs.ultralytics.com/tasks/detect/) 
  - Speed optimization for inference with script parameters:
    - Skip 10 frames
    - Use 4x compression


## Image processing times

These experiments were made on 2018 Macbook pro and processing as a video feed:

| MODEL           |   Task    | Preprocessing  |  Inference       | Post processing   | Detect total time  | Loop total time  | Showing camera |
|-----------------|-----------|----------------|------------------|-------------------|--------------------| -----------------| -------------- |
| yolov8n-seg.pt  | Detection | +/- 1ms mean   | +/- 220ms mean   | +/- 1ms mean      | +/- 222ms mean     | +/- 222ms mean   |       [x]      |
| yolov8n-seg.pt  | Detection | unknown        | unknown          | unknown           | unknown            | +/- 230ms mean   |       [x]      |
| yolov8n.pt      | Detection | +/- 1ms mean   | +/- 168s mean    | +/- 1ms mean      | +/- 170ms mean     | +/- 170ms mean   |       [x]      |

The findings indicate the most of the image processing time is in inference and the pre and post processing time is negligible.
Segmentation takes 30% more time to process than bounding box detection.