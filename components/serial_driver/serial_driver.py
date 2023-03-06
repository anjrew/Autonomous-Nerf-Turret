# Python 3 server example
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Optional
import serial.tools.list_ports
import json

webServer:Optional[HTTPServer] = None
serialInst:Optional[serial.Serial] = None

try:
    # =========================== SERIAL ===========================================

    ports = serial.tools.list_ports.comports()
    serialInst = serial.Serial()

    portsList = []

    print("\nSerial Port options: ")
    for i, onePort in enumerate(ports):
        print(f"{i}: ",onePort.name, " - ", onePort.manufacturer or "Unknown Manufacturer")
        portsList.append(onePort.device)

    val = None

    while val == None or int(val) >= len(portsList):
        val = input("Select Port: ")
        if int(val) >= len(portsList):
            print("Invalid Port Selected")

    serialInst.baudrate = 9600
    serialInst.port = portsList[int(val)]

    serialInst.open()
    print("Connected to Serial Port: ", serialInst.port)

    # ============================== SERVER ======================================

    hostName = "localhost"
    serverPort = 5565

    class MyServer(BaseHTTPRequestHandler):
        
        def do_POST(self):
            # Get the content type and content length of the request
            content_type = self.headers.get('content-type')
            content_length = int(self.headers.get('content-length', 0))
            
            # Read the request data
            data = self.rfile.read(content_length)
            
            # Parse the JSON data
            json_data = json.loads(data)
            
            # Print the request data
            print(f'Request data: {json_data}')
            
            # Send a response
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            serialInst.write(json.dumps(json_data).encode())

    if __name__ == "__main__":        
        webServer = HTTPServer((hostName, serverPort), MyServer)
        print("Server started http://%s:%s" % (hostName, serverPort))

        webServer.serve_forever()
      

except Exception as e:
    print(e)
    if serialInst: serialInst.close()
    if webServer: webServer.server_close()
    print("Server stopped and Serial Port closed")
