import time
from rich.text import Text
from rich.live import Live

class CConsole:
    def __init__(self):
        self.live = Live()
    
    def __enter__(self):
        self.live.start()
        return self
    
    def __exit__(self, a, b, c):
        self.live.stop()
    
    def log(self, *args):
        args = ", ".join(list(map(lambda e: str(e), args)))
        self.live.update(Text(args))
    