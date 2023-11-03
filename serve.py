from modules.FlaskAppHandler import FlaskAppHandler
from modules.HTTPServerHandler import HTTPServerHandler

if __name__ == '__main__':
    flask_app = FlaskAppHandler()
    flask_app.start()

    http_server = HTTPServerHandler(port=5731, directory='./songs')
    http_server.start_server()
    print("The HTTP server is running in the background...")
