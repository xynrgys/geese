import subprocess
import uuid
import time
import os

class DevBoxManager:
    def __init__(self, codebase_path: str):
        self.codebase_path = os.path.abspath(codebase_path)
        self.container_name = f"devbox-{uuid.uuid4().hex[:8]}"

    def start(self):
        """Starts the Docker container with network isolation and read-only codebase mount."""
        cmd = [
            "docker", "run", "-d",
            "--name", self.container_name,
            "--network", "none",
            "-v", f"{self.codebase_path}:/code:ro",
            "alpine:latest",
            "tail", "-f", "/dev/null"
        ]

        start_time = time.time()
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            raise RuntimeError(f"Failed to start container: {result.stderr}")

        elapsed = time.time() - start_time
        if elapsed > 10:
            print(f"Warning: Container took {elapsed:.2f} seconds to start, which exceeds the 10s requirement.")

    def stop(self):
        """Stops and removes the Docker container."""
        cmd_stop = ["docker", "stop", self.container_name]
        subprocess.run(cmd_stop, capture_output=True, text=True)

        cmd_rm = ["docker", "rm", self.container_name]
        subprocess.run(cmd_rm, capture_output=True, text=True)

    def execute_command(self, command: str) -> str:
        """Executes a shell command inside the container and returns its output."""
        cmd = [
            "docker", "exec", self.container_name,
            "sh", "-c", command
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            raise RuntimeError(f"Command execution failed: {result.stderr}")

        return result.stdout
