from pyngrok import ngrok
import logging

# Get the pyngrok logger and set its level to CRITICAL
logger = logging.getLogger('pyngrok')
logger.setLevel(logging.CRITICAL)

class NgrokTunnel:
    def __init__(self, port: int):
        self.port = port
        self.tunnel = None

    def start_tunnel(self):
        # ngrok.set_auth_token("<NGROK_AUTH_TOKEN>")  # Optionally set the auth token
        self.tunnel = ngrok.connect(self.port, "http")
        print(f"Ngrok tunnel started at {self.tunnel.public_url}")

    def stop_tunnel(self):
        if self.tunnel:
            ngrok.disconnect(self.tunnel.public_url)  # You can disconnect using the public URL
            self.tunnel = None
            print("Ngrok tunnel stopped")


if __name__ == "__main__":
    tunnel = NgrokTunnel(8080)
    tunnel.start_tunnel()

    # Do something with the tunnel

    #tunnel.stop_tunnel()