import subprocess

class NgrokTunnel:
    def __init__(self, port):
        self.port = port
        self.process = None

    def start_tunnel(self):
        # Kill ngrok if it's already running
        result = subprocess.run("taskkill /f /im ngrok.exe", shell=True, capture_output=True, text=True)
        print(result.stdout)
        print(result.stderr)

        #command = f"ngrok http {self.port} --log=stdout"
        command = f"ngrok http {self.port}"
        self.process = subprocess.Popen(command, shell=True)

    def stop_tunnel(self):
        if self.process:
            self.process.terminate()