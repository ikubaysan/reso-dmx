import subprocess

class NgrokTunnel:
    def __init__(self, port):
        self.port = port
        self.process = None

    def start_tunnel(self):
        command = f"ngrok http {self.port} --log=stdout"
        self.process = subprocess.Popen(command, shell=True)

    def stop_tunnel(self):
        if self.process:
            self.process.terminate()