import subprocess
import os.path

class Runner:
    def __init__(self, command):
        self.command = command
        self.process = None

    def start(self):
        self.process = subprocess.Popen(
            self.command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE
        )

    def read(self):
        return self.process.stdout.readline().decode("utf-8").strip()

    def write(self, message):
        self.process.stdin.write(f"{message.strip()}\n".encode("utf-8"))
        self.process.stdin.flush()

    def terminate(self):
        self.process.stdin.close()
        self.process.terminate()
        self.process = None
