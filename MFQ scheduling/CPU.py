class CPU():
    def __init__(self):
        self.isrunning = False
    
    def run(self, p, return_index, running_time):
        self.p = p
        self.return_index = return_index
        self.running_time = running_time
        self.isrunning = True
    
    def terminate(self):
        self.isrunning = False
        return self.p, self.return_index