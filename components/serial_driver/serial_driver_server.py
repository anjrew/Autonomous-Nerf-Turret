from http.server import HTTPServer, BaseHTTPRequestHandler

# Define the number of requests to handle at a time
MAX_REQUESTS = 1

class SerialDriverServer(HTTPServer):
    def handle_request(self):
        # Handle the next request
        super().handle_request()
        
        # Ignore any buffered requests
        for i in range(MAX_REQUESTS - 1):
            if self.socket.fileno() == -1:
                break
            super().handle_request()
