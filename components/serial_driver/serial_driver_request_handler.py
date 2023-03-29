import logging
from http.server import BaseHTTPRequestHandler
from serial_driver_utils import encode
from serial import Serial
import time
import json


last_request_time = time.time()
class SerialDriverRequestHandler(BaseHTTPRequestHandler):
    
    def __init__(self, *args, **kwargs):
        keys_used = ['serial_inst', 'slowest_speed', 'fasted_speed', 'test', 'throttle_interval']
        self.properties = {}
        for key in keys_used:
            if key not in kwargs:
                raise Exception(f"Missing required key: {key}")
            else:
                self.properties[key] = kwargs[key]
                del kwargs[key]        
  
        BaseHTTPRequestHandler.__init__(self, *args, **kwargs)

        
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
        
        # If the test flag is set, then just return a 200 response without doing anything
        if self.properties.get('test') == True:
            logging.debug("Test flag is set, returning 200 response and not sending data to serial")
            self.send_response(200)
            self.end_headers()
            return
        
        global last_request_time
        throttle_interval = self.properties.get('throttle_interval', 0)
        print('last_request_time', last_request_time)
        print('throttle_interval', throttle_interval)
        current_time = time.time()
        print('current_time', current_time)
        time_since_last_request = current_time - last_request_time
        print('time_since_last_request', time_since_last_request)
        should_throttle_request = time_since_last_request < throttle_interval
        if should_throttle_request:
            logging.debug("Too many requests, returning 429 response")
            self.send_response(429)
            self.end_headers()
            self.wfile.write(b'Too many requests. Please try again later.')
            return
        
        print('Assining time here')
        start_time = last_request_time = time.time()
        # Get the content type and content length of the request
        content_length = int(self.headers.get('content-length', 0))
        # Read the request data
        data = self.rfile.read(content_length)
        
        # Parse the JSON data
        json_data = json.loads(data)
        logging.debug("Got Data: " + json.dumps(json_data))
        
        speed_in = json_data.get('speed', 0)
        
        slowest_speed = self.properties.get('slowest_speed')
        fasted_speed = self.properties.get('fasted_speed')
        serial_inst: Serial = self.properties.get('serial_inst')# type: ignore
        if speed_in and (speed_in < slowest_speed or speed_in > self.properties.get('fasted_speed')):
                # Send a response
                self.send_response(400)
                self.end_headers()
                # Send the bad request data
                self.wfile.write(f"""
                Received a speed that was outside the min({slowest_speed}) max({fasted_speed}) bounds: {speed_in}
                """.encode())
                return
            
       
        
        logging.debug("Sending before encoding: " + str([round(json_data.get("azimuth_angle", 0)), json_data.get("is_clockwise", False), round(speed_in), json_data['is_firing']]))
        encoded_message = encode(round(json_data.get("azimuth_angle", 0)), json_data.get("is_clockwise", False), round(speed_in), json_data['is_firing'])
        logging.debug("Encoded Message HEX: " + str(encoded_message) + "  BINARY: " + str(bin(encoded_message[0])) + " " + str(bin(encoded_message[1])))
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


        
        
