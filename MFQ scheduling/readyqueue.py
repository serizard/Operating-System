from collections import deque


class round_robin():
    def __init__(self, time_quantum, priority):
        self.tq = time_quantum
        self.priority = priority
        self.queue = deque([])

    def add(self, p):
        self.queue.append(p)
    
    def isempty(self):
        return len(self.queue) == 0
    
    def dispatch(self):
        return self.queue.popleft(), self.tq


class FCFS():
    def __init__(self, priority):
        self.priority = priority
        self.queue = deque([])

    def add(self, p):
        self.queue.append(p)
    
    def isempty(self):
        return len(self.queue) == 0
    
    def dispatch(self):
        return self.queue.popleft(), None