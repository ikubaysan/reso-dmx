import os
from http.server import HTTPServer, SimpleHTTPRequestHandler
import threading

class HTTPServerHandler:
    def __init__(self, port=8000, directory=None):
        self.port = port
        self.directory = os.path.abspath(directory) if directory else os.path.abspath(os.getcwd())
        self.httpd = None

    def start_server(self):
        def run_server():
            os.chdir(self.directory if self.directory else os.getcwd())
            server_address = ('0.0.0.0', self.port)
            handler_class = lambda *args, **kwargs: SimpleHTTPRequestHandler(*args, directory=self.directory, **kwargs)
            self.httpd = HTTPServer(server_address, handler_class)
            print(f"Serving HTTP on 0.0.0.0 port {self.port} (http://0.0.0.0:{self.port}/) ...")
            self.httpd.serve_forever()

        thread = threading.Thread(target=run_server)
        thread.daemon = True  # This ensures that the thread will close when the main program exits
        thread.start()

    def stop_server(self):
        if self.httpd:
            self.httpd.shutdown()