# Python 3 server example
from http.server import HTTPServer
from typing import Optional
import argparse
import serial.tools.list_ports
import serial
import logging

from serial_driver_server import SerialDriverServer
from serial_driver_utils import map_log_level
    

parser = argparse.ArgumentParser()
parser.add_argument("--set-port-man", action="store_true",dest="is_port_man", help="Set the serial port manually instead of using the default port through the command line prompt.")
parser.add_argument("--port", help="Set the http server port.", default=5565)
parser.add_argument("--baud", help="Set the Baud Rate of the serial communication.", default=9600)
parser.add_argument("--host", help="Set the http server hostname.", default="localhost")
parser.add_argument("--log-level", "-ll" ,help="Set the logging level by integer value.", default=logging.WARNING, type=map_log_level)
parser.add_argument("--delay", "-d",help="Delay to rate the data is sent to the Arduino in seconds", default=0, type=int)

args = parser.parse_args()

logging.basicConfig(level=args.log_level)


webServer:Optional[HTTPServer] = None
serialInst:Optional[serial.Serial] = None

## For the elevation stepper motor speed ordinal values
SLOWEST_EL_SPEED = 0
FASTEST_EL_SPEED = 10


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
    
    if __name__ == "__main__":

        webServer = HTTPServer(
            (args.host, args.port),
            lambda *args, **kwargs: SerialDriverServer(
                serial_inst=serialInst, 
                slowest_speed=SLOWEST_EL_SPEED, 
                fasted_speed=FASTEST_EL_SPEED, 
                *args, **kwargs
                ))
        
        print("Server started http://%s:%s" % (args.host, args.port))

        webServer.serve_forever()
      

except Exception as e:
    logging.error("An exception was thrown:" + str(e))
    if serialInst: serialInst.close()
    if webServer: webServer.server_close()
    logging.error("Server stopped and Serial Port closed")
    raise e
