from time import sleep
from itertools import count

class Daemon:
    def __init__(self):
        pass

    def start(self):
        for i in count():
            print(f"\rdaemon is running for {i} seconds", end="", flush=True)
            sleep(1)