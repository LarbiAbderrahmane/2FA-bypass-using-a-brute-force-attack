import threading
from classes.CConsole import CConsole

class Monitor:
    def __init__(self, console: CConsole):
        self.mutex = threading.Lock()
        self.buffer = []
        self.buffer_cond = threading.Condition(self.mutex)
        self.found = False
        self.limit = 100
        self.TOTAL = 10000
        self.n = self.TOTAL
        self.console = console

    def increment_n(self)->int:
        with self.mutex:
            self.n = self.n + 1
            return self.n
    
    def decrement_n(self)->int:
        with self.mutex:
            self.n = self.n - 1
            return self.n
    
    def get_n(self):
        with self.mutex:
            return self.n
    
    def set_found(self, value: bool):
        with self.mutex:
            self.found = value
    
    def get_found(self)->bool:
        with self.mutex:
            return self.found
    
    def get_buffer(self)->list:
        with self.mutex:
            if len(self.buffer) < self.limit and self.n > self.limit or len(self.buffer) == 0:
                self.console.log("waiting for some tokens...")
                self.buffer_cond.wait(10)
            return self.buffer
    
    def remove_from_buffer(self, value):
        with self.mutex:
            self.buffer.remove(value)
    
    def append_to_buffer(self, value):
        with self.mutex:
            self.buffer.append(value)
            if len(self.buffer) >= self.limit:
                self.buffer_cond.notify()