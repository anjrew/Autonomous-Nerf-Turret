from ultralytics import YOLO
import argparse
from argparse import ArgumentParser
import logging

parser = ArgumentParser(description="Tracks multiple objects with bounding boxes, segmentation and classification")

parser.add_argument("--model-name", "-mn", help="The model name to use for detection", type=str, default="yolov8n-seg.pt")
parser.add_argument("--format", "-f", help="The format to make the model", type=str, default="openvino")

args = parser.parse_args()
    

# Load a model
model = YOLO(args.model_name)  # load an official model

# Export the model
model.export(format=args.format)