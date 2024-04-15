class process():
    def __init__(self, PID, BT):
        self.pid = PID
        self.remaining_bt = BT
    
    def burst(self, tq=None):
        if tq == None:
            return self.remaining_bt, True
        else:
            if self.remaining_bt > tq:
                self.remaining_bt -= tq
                return tq, False
            elif self.remaining_bt == tq:
                return tq, True
            else:
                return self.remaining_bt, True