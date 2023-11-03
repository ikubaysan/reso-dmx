from modules.FlaskAppHandler import FlaskAppHandler
from modules.HTTPServerHandler import HTTPServerHandler
from modules.NgrokTunnel import NgrokTunnel
import time

if __name__ == '__main__':
    print("Starting Flask app...")
    flask_app = FlaskAppHandler()
    flask_app.start()

    print("Starting HTTP server...")
    http_server = HTTPServerHandler(port=5731, directory='./songs')
    http_server.start_server()

    print("Servers are running. Now starting ngrok tunnel...")
    ngrok_tunnel = NgrokTunnel(port=5731)
    ngrok_tunnel.start_tunnel()

    print("All servers started.")

    # Keep the main thread alive, otherwise python might close down all daemon threads.
    try:
        while True:
            # This can be a place to check for a stop condition if needed.
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping servers...")
        # Here you can add commands to stop your servers and cleanup if necessary.
        http_server.stop_server()
        ngrok_tunnel.stop_tunnel()
        print("Servers stopped.")
