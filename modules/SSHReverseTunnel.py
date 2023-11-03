import subprocess
from subprocess import Popen
from typing import Optional

class SSHReverseTunnel:
    def __init__(self, local_port: str, vps_port: str, vps_ip: str, vps_user: str):
        """
        Initialize the SSH reverse tunnel.

        :param local_port: The port on the local machine to forward to the VPS.
        :param vps_port: The port on the VPS that will be exposed to the internet.
        :param vps_ip: The IP address of the VPS server.
        :param vps_user: The username for the SSH connection to the VPS.
        """
        self.local_port = local_port
        self.vps_port = vps_port
        self.vps_ip = vps_ip
        self.vps_user = vps_user
        self.ssh_process: Optional[Popen] = None

    def start_tunnel(self) -> None:
        """
        Start the SSH reverse tunnel subprocess.
        """
        # Construct the SSH command for the reverse tunnel
        ssh_command = [
            "ssh",
            "-R",
            f"*:{self.vps_port}:localhost:{self.local_port}",  # Remote forwarding
            "-o", "ServerAliveInterval=60",  # Keep the connection alive
            "-o", "ExitOnForwardFailure=yes",  # Exit if the forwarding fails
            "-N",  # Don't execute a remote command
            f"{self.vps_user}@{self.vps_ip}"
        ]
        # Start the SSH process
        self.ssh_process = subprocess.Popen(ssh_command)
        print(f"SSH reverse tunnel established on {self.vps_ip}:{self.vps_port}")

    def stop_tunnel(self) -> None:
        """
        Terminate the SSH reverse tunnel subprocess if it is running.
        """
        if self.ssh_process:
            self.ssh_process.terminate()  # Send a signal to terminate the process
            self.ssh_process.wait()  # Wait for the process to finish
            print("SSH reverse tunnel terminated.")

# Example usage
if __name__ == '__main__':
    tunnel = SSHReverseTunnel(
        local_port="5731",
        vps_port="80",
        vps_ip="your.vps.ip",
        vps_user="your_vps_user"
    )

    try:
        tunnel.start_tunnel()
        input("Press Enter to exit and close the tunnel...")
    finally:
        tunnel.stop_tunnel()
