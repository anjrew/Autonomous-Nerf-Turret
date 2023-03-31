# Vision

This code includes computer vision algorithms for object detection and tracking. 

## Info
  - A [video](https://www.youtube.com/watch?v=5yPeKQzCPdI&list=PLVlbw1IZ2gnswgwYW9jXkEz43f3j7qs25&index=77) of how to use the face recognition library 
  - A guide on setting up the [YOLO object detection](https://docs.ultralytics.com/tasks/detect/) 
  - Speed optimization for inference with script parameters:
    - Skip 10 frames
    - Use 4x compression


## Object processing times

These experiments were made on 2018 Macbook pro and processing as a video feed:

| MODEL           |   Task    | Preprocessing  |  Inference       | Post processing   | Detect total time  | Loop total time  | Showing camera | Machine        |
|-----------------|-----------|----------------|------------------|-------------------|--------------------| -----------------| -------------- | ---------------|
| yolov8n-seg.pt  | Detection | +/- 1ms mean   | +/- 220ms mean   | +/- 1ms mean      | +/- 222ms mean     | +/- 222ms mean   |       [x]      |       Mac      |
| yolov8n-seg.pt  | Detection | unknown        | unknown          | unknown           | unknown            | +/- 230ms mean   |       [x]      |       Mac      |
| yolov8n.pt      | Detection | +/- 1ms mean   | +/- 168s mean    | +/- 1ms mean      | +/- 170ms mean     | +/- 170ms mean   |       [x]      |       Mac      |

The findings indicate the most of the image processing time is in inference and the pre and post processing time is negligible.
Segmentation takes 30% more time to process than bounding box detection.

## Face detection processing times

The time of face detection seems to depend on the amount of delay in the loop. 

The minimum face detection time with a large delay in the loop was 0.1s.
If the loop delay was less than 0.1 seconds then the face detection time would go up as high as 0.3s when no delay was given.

Set the delay to zero to ensure maximum performance