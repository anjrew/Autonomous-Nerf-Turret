# Python 3 server example
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Optional
import argparse
import serial.tools.list_ports
from serial.tools.list_ports_common import ListPortInfo
import json


parser = argparse.ArgumentParser()
parser.add_argument("--set-port-man", action="store_true",dest="is_port_man", help="Set the port manually instead of using the default port through the command line prompt.")
args = parser.parse_args()

webServer:Optional[HTTPServer] = None
serialInst:Optional[serial.Serial] = None

SLOWEST_HALF_STEP_MICROSECONDS = 17000
FASTEST_HALF_STEP_MICROSECONDS = 400

SLOWEST_SPEED = 0
FASTEST_SPEED = 10

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
    return original_value




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
            if int(val) >= len(portsList):
                print("Invalid Port Selected")
            serialInst.port = portsList[int(val or  0)]
    else:
        for port in ports:
            if "Arduino" in (port.manufacturer or ""):
                serialInst.port = port.device

    if not serialInst.port:
        raise Exception("No Arduino Found")

    serialInst.baudrate = 9600
    

    serialInst.open()
    print("Connected to Serial Port: ", serialInst.port)

    # ============================== SERVER ======================================

    hostName = "localhost"
    serverPort = 5565

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
        
        
        def do_POST(self):
            # Get the content type and content length of the request
            content_length = int(self.headers.get('content-length', 0))
            
            # Read the request data
            data = self.rfile.read(content_length)
            
            # Parse the JSON data
            json_data = json.loads(data)
            if "isClockwise" in json_data:
                
                serialInst.write(json.dumps({
                    "isClockwise": json_data["isClockwise"]
                }).encode())
            
            if "speed" in json_data:
                
                speed_in = json_data["speed"]
                
                if speed_in < SLOWEST_SPEED or speed_in > FASTEST_SPEED:
                    # Send a response
                    self.send_response(400)
                    self.end_headers()
                    # Send the bad request data
                    self.wfile.write(f"""
                    Received a speed that was outside the min({SLOWEST_SPEED}) max({FASTEST_SPEED}) bounds: {speed_in}
                    """.encode())
                    return
                else:
                    serialInst.write(json.dumps({
                        "stepUs": map_range(json_data["speed"])
                    }).encode())
            
            
            # Send a response
            self.send_response(200)
            self.end_headers()
            
            serialInst.write(json.dumps(json_data).encode())

    if __name__ == "__main__":        
        webServer = HTTPServer((hostName, serverPort), MyServer)
        print("Server started http://%s:%s" % (hostName, serverPort))

        webServer.serve_forever()
      

except Exception as e:
    print("An exception was thrown:" , e)
    if serialInst: serialInst.close()
    if webServer: webServer.server_close()
    print("Server stopped and Serial Port closed")
