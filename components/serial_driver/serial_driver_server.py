import select
from http.server import HTTPServer

class SerialDriverServer(HTTPServer):


    def handle_request(self):
        # Check if there are new requests in the buffer
        r_list, _, _ = select.select([self.socket], [], [], 0)

        if r_list:
            # Handle the newest request
            super().handle_request()

            # Discard all the older requests in the buffer
            while select.select([self.socket], [], [], 0)[0]:
                super().handle_request()