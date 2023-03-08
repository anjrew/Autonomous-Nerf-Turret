# Python 3 server example
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Optional
import argparse
import serial.tools.list_ports
import json
import logging



parser = argparse.ArgumentParser()
parser.add_argument("--set-port-man", action="store_true",dest="is_port_man", help="Set the serial port manually instead of using the default port through the command line prompt.")
parser.add_argument("--port", help="Set the http server port.", default=5565)
parser.add_argument("--baud", help="Set the Baud Rate of the serial communication.", default=9600)
parser.add_argument("--host", help="Set the http server hostname.", default="localhost")
parser.add_argument("--log-level", help="Set the logging level by integer value.", default=logging.DEBUG, type=int)
parser.add_argument("--delay", "-d",help="Delay to rate the data is sent to the Arduino in seconds", default=0, type=int)

args = parser.parse_args()

logging.basicConfig(level=args.log_level)


webServer:Optional[HTTPServer] = None
serialInst:Optional[serial.Serial] = None

SLOWEST_HALF_STEP_MICROSECONDS = 17000
FASTEST_HALF_STEP_MICROSECONDS = 1000

SLOWEST_SPEED = 0
FASTEST_SPEED = 10

def limit_value(value, minimum=-90, maximum=90):
    """Limits the value to the min and max values"""
    if value < minimum:
        return minimum
    elif value > maximum:
        return maximum
    else:
        return value

def map_range(value=0, min_value=SLOWEST_HALF_STEP_MICROSECONDS, max_value=FASTEST_HALF_STEP_MICROSECONDS, new_min_value=SLOWEST_SPEED, new_max_value=FASTEST_SPEED):
    """Converts a value from on range to another

    Args:
        value (int, optional): Value to convert to the base range. Defaults to 0.
        min_value (int, optional): The slowest range of the stepper motor step. Defaults to SLOWEST_HALF_STEP_MICROSECONDS.
        max_value (int, optional): The fastest range of the stepper motor step. Defaults to FASTEST_HALF_STEP_MICROSECONDS.
        new_min_value (int, optional): The min value to be input here that is human comprehendible. Defaults to 0.
        new_max_value (int, optional): The max value to be input here that is human comprehendible. Defaults to 10.

    Returns:
        int: The value of the half step time in micro seconds to be sent to the stepper motor controller
    """

    new_range = new_max_value - new_min_value    

    original_range = max_value - min_value

    scaling_factor = original_range / new_range

    original_value = ((value - new_min_value) * scaling_factor) + min_value
    
    return round(original_value)

def encode(azimuth: int, is_clockwise: bool = True, speed: int = 0, is_firing: bool = False) -> bytes:
    """
    Encodes a motor command as two bytes.

    Parameters:
        azimuth (int): The azimuth of the motor, from 0 to 180.
        is_clockwise (bool): Whether the motor should turn clockwise (True) or counterclockwise (False).
            Default is True.
        speed (int): The speed of the motor, from 0 (off) to 10 (maximum speed).
            Default is 0.
        is_firing (bool): Whether the motor should be fired (True) or not (False).
            Default is False.

    Returns:
        bytes: Two bytes representing the encoded motor command.

    Example:
        >>> encode(90, True, 5)
        b'\x5f\x08'
    """
    azimuth_degrees = limit_value(azimuth, -90, 90) + 90  # Convert the input angle to a range of 0-180 degrees
    azimuth_byte = round((azimuth_degrees / 180.0) * 255.0)  # Scale the azimuth value to fit in a byte (0-255)
    encoded_value = 0
    if is_clockwise:
        encoded_value |= (1 << 7)  # Set the 8th bit to 1 for clockwise
        is_clockwise = bool(encoded_value & 0x80)
        
        
    encoded_value |= (speed & 0x0F)  # Mask the lower 4 bits for speed (0-10)
    
    if is_firing:
        encoded_value |= (1 << 2)  # Set the 3rd bit to 1 for is_firing
    return bytes([encoded_value, azimuth_byte])


try:
    # =========================== SERIAL ===========================================

    ports = serial.tools.list_ports.comports()
    serialInst = serial.Serial()

    portsList = []

    if args.is_port_man:
        
        print("\nSerial Port options: ")
        for i, onePort in enumerate(ports):
            print(f"{i}: ",onePort.name, " - ", onePort.manufacturer or "Unknown Manufacturer")
            portsList.append(onePort.device)
            
        val = None
        while val == None or int(val) >= len(portsList):
            val = input("Select Port: ")
            if int(val) >= len(portsList) or int(val) < 0:
                print("Invalid Port Selected")
            else:
                serialInst.port = portsList[int(val or  0)]
    else:
        for port in ports:
            if "Arduino" in (port.manufacturer or ""):
                serialInst.port = port.device

    if not serialInst.port:
        raise Exception("No Arduino Found")

    serialInst.baudrate = args.baud
    serialInst.open()
    print("Connected to Serial Port:", serialInst.port, "at", serialInst.baudrate, "baud rate.")    

    
    # ============================== SERVER ======================================
    
    class MyServer(BaseHTTPRequestHandler):
        
        def do_GET(self):
            # Send a response
            self.send_response(200)
            self.end_headers()
            
            # Send the response data
            self.wfile.write(b"""
                             Send a POST request to this endpoint with JSON data with the key 'speed' and a value between speed min 0 and max 10.
                             The json can also have a key of 'isClockwise' with a value of true or false for the direction of the motor.
                             """)
        
        # { 'isClockwise': True }
        def do_POST(self):
            # Get the content type and content length of the request
            content_length = int(self.headers.get('content-length', 0))
            # Read the request data
            data = self.rfile.read(content_length)
            
            # Parse the JSON data
            json_data = json.loads(data)
            logging.debug("Got Data: " + json.dumps(json_data))
            
            speed_in = json_data.get('speed', 0)
            
            if speed_in and (speed_in < SLOWEST_SPEED or speed_in > FASTEST_SPEED):
                    # Send a response
                    self.send_response(400)
                    self.end_headers()
                    # Send the bad request data
                    self.wfile.write(f"""
                    Received a speed that was outside the min({SLOWEST_SPEED}) max({FASTEST_SPEED}) bounds: {speed_in}
                    """.encode())
                    return

            encoded_message = encode(json_data.get("azimuth_angle", 90), json_data.get("is_clockwise", False), round(speed_in),json_data['is_firing'])
            serialInst.write(encoded_message)#.to_bytes(1, "big"))
            
            # # Send a response
            self.send_response(200)
            self.end_headers()
            

    if __name__ == "__main__":

        webServer = HTTPServer((args.host, args.port), MyServer)
        print("Server started http://%s:%s" % (args.host, args.port))

        webServer.serve_forever()
      

except Exception as e:
    print("An exception was thrown:" , e)
    if serialInst: serialInst.close()
    if webServer: webServer.server_close()
    print("Server stopped and Serial Port closed")
