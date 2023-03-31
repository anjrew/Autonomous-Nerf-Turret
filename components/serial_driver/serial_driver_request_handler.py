import logging
from http.server import BaseHTTPRequestHandler
from typing import Optional, Tuple
from serial_driver_utils import encode, map_controller_action_to_turret_action
from serial import Serial

import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)) + '/..')
from nerf_turret_utils.controller_action import ControllerAction
from nerf_turret_utils.turret_controller import TurretAction
import time
import json


last_request_time = time.time()
class SerialDriverRequestHandler(BaseHTTPRequestHandler):
    
    last_action:Optional[TurretAction] = None
    
    def __init__(self, 
        serial_inst: Serial,
        azimuth_speed_range: Tuple[int, int],
        elevation_speed_range: Tuple[int, int],
        test: bool,
        throttle_interval: int,
        base_args: Tuple,  # Add this line
        base_kwargs: dict
        ):
        self.serial_inst = serial_inst
        self.azimuth_speed_range = azimuth_speed_range
        self.elevation_speed_range = elevation_speed_range
        self.test = test
        self.throttle_interval = throttle_interval
         
  
        super().__init__(*base_args, **base_kwargs)

        
    def do_GET(self):
        # Send a response
        self.send_response(200)
        self.end_headers()
        
        # Send the response data
        self.wfile.write(b"""
                            Send a POST request to this endpoint with JSON data with the key 'speed' and a value between speed min 0 and max 10.
                            The json can also have a key of 'isClockwise' with a value of true or false for the direction of the motor.
                            """)
    

    def do_POST(self):
        
        # Get the content type and content length of the request
        content_length = int(self.headers.get('content-length', 0))
        # Read the request data
        data = self.rfile.read(content_length)
        
        # Parse the JSON data
        raw_data = json.loads(data)
        controller_action = ControllerAction(**raw_data)
        logging.debug("Got Data: " + json.dumps(controller_action.__dict__))
        if controller_action == self.last_action:
            logging.debug("Same as last action, returning 200 response")
            self.send_response(200)
            self.end_headers()
            return
        
               
        global last_request_time
        throttle_interval = self.throttle_interval
        current_time = time.time()
        time_since_last_request = current_time - last_request_time
        should_throttle_request = time_since_last_request < throttle_interval
        if should_throttle_request:
            logging.debug("Too many requests, returning 429 response")
            self.send_response(429)
            self.end_headers()
            self.wfile.write(b'Too many requests. Please try again later.')
            return
        
        start_time = last_request_time = time.time()
                
        serial_inst: Serial = self.serial_inst# type: ignore
            
        turret_action:TurretAction = map_controller_action_to_turret_action(action=controller_action, azimuth_speed_range=self.azimuth_speed_range ,elevation_speed_range=self.elevation_speed_range)   
        
        assert self.azimuth_speed_range[0] <= turret_action['azimuth_angle'] <= self.azimuth_speed_range[1], "Azimuth angle should be within the range of the azimuth speed range"
        assert self.elevation_speed_range[0] <= turret_action['speed'] <= self.elevation_speed_range[1], "Speed should be within the range of the azimuth speed range"
        assert turret_action['speed'] >= 0, "Speed should be greater than or equal to 0"
        
        logging.debug("Sending before encoding: " + str(turret_action))
        encoded_message = encode(round(turret_action.get("azimuth_angle", 0)), turret_action.get("is_clockwise", False), turret_action['speed'], turret_action['is_firing'])
        logging.debug("Encoded Message HEX: " + str(encoded_message) + "  BINARY: " + str(bin(encoded_message[0])) + " " + str(bin(encoded_message[1])))
        # If the test flag is set, then just return a 200 response without doing anything
        if self.test == True:
            logging.debug("Test flag is set, returning 200 response and not sending data to serial")
            self.send_response(200)
            self.end_headers()
            return
        
        try:

            serial_inst.write(encoded_message)
            # # Send a response
            self.send_response(200)
            self.end_headers()
            
        except Exception as e:
            logging.error("An exception was thrown:" + str(e) + " " + str(type(e)))
            if serial_inst: serial_inst.close()
            logging.error("SerialDriverServer stopped and Serial Port closed")
            self.send_response(500)
            self.end_headers()
        finally: 
            # Record the time taken to process the frame
            logging.debug("Frame processed in " + str(time.time() - start_time) + " seconds")


        
        
