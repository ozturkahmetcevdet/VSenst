from pyb import UART
import time

class NEXTION():
    def __init__(self):
        super().__init__()
        self.Setup()
    
    def Setup(self):
        self.UART = UART(2, 38400)

    def Test(self, str = ""):
        self.UART.write(str)
        self.UART.write((0xFF, 0xFF, 0xFF))