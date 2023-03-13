# import required packages
from typing import List
import cv2
import argparse
import numpy as np


class YoloObjectDetection:
    
    
    def __init__(self, classes_path: str):
        self.classes_path = classes_path
        with open(classes_path, 'r') as f:
            self.classes = [line.strip() for line in f.readlines()]


def process_image(image:np.ndarray):

    width = image.shape[1]
    height = image.shape[0]
    scale = 0.00392

    # read class names from text file
    classes = None
    with open(args.classes, 'r') as f:
        classes = [line.strip() for line in f.readlines()]

    # generate different colors for different classes 
    COLORS = np.random.uniform(0, 255, size=(len(classes), 3))

    # read pre-trained model and config file
    net = cv2.dnn.readNet(args.weights, args.config)

    # create input blob 
    blob = cv2.dnn.blobFromImage(image, scale, (416,416), (0,0,0), True, crop=False)

    # set input blob for the network
    net.setInput(blob)
    
    
    
if __name__ == "__main__":
    # handle command line arguments
    ap = argparse.ArgumentParser()
    ap.add_argument('-i', '--image', required=True,
                    help = 'path to input image')
    ap.add_argument('-c', '--config', required=True,
                    help = 'path to yolo config file')
    ap.add_argument('-w', '--weights', required=True,
                    help = 'path to yolo pre-trained weights')
    ap.add_argument('-cl', '--classes', required=True,
                    help = 'path to text file containing class names')
    args = ap.parse_args()

    yolo_od = YoloObjectDetection(args.classes)

    # read input image
    image = cv2.imread(args.image)