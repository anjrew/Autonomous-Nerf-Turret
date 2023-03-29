import select
from http.server import HTTPServer

# Define the number of requests to handle at a time
MAX_REQUESTS = 1

class SerialDriverServer(HTTPServer):

    # def handle_request(self):
    #     # Handle the next request
    #     super().handle_request()
        
    #     # Ignore any buffered requests
    #     for i in range(MAX_REQUESTS - 1):
    #         if self.socket.fileno() == -1:
    #             break
    #         super().handle_request()
    def handle_request(self):
        # Check if there are new requests in the buffer
        r_list, _, _ = select.select([self.socket], [], [], 0)

        if r_list:
            # Handle the newest request
            super().handle_request()

            # Discard all the older requests in the buffer
            while select.select([self.socket], [], [], 0)[0]:
                super().handle_request()