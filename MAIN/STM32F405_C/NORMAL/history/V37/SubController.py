import gc
from micropython import const
from pyb import UART, Pin
import json
import time

class CMD:
    class Page:
        Entry    = const(1)
        Main     = const(2)
        Bye      = const(3)
        Alarm    = const(4)

    class Ignition:
        On       = const(1)
        Off      = const(2)

    class Record:
        Default    = const(1) 
        RecordMode = const(2) 
        Services   = const(3) 

    class LowPower:
        Sleep    = const(0) 
        WakeUp   = const(1) 

class Sub(CMD):
    def __init__(self) -> None:
        super().__init__()
        self.RST  = Pin('B0', Pin.OUT_PP)
        self.CTRL = Pin('B1', Pin.OUT_PP)
        self.UART = UART(3, 1728000,  timeout=10, read_buf_len=512)
        self.Setup()

    def Setup(self):
        self.Reset()

    def Reset(self):
        self.CTRL.high()
        self.RST.low()
        time.sleep(0.01)
        self.RST.high()

    def Receive(self):
        if self.UART.any():
            data = self.UART.read()
            print(str(data))
            return data
        return None

    def Process(self, buffer=None):
        #self.Receive()

        answer = False
        if buffer == None:
            return None
            
        try:
            self.UART.write(buffer)
            #print(buffer)
            answer = True
        except OSError as err:
            print("OS error: {0}".format(err))
        except ValueError:
            print("Could not send data over UART.")
        except:
            print("Unexpected error!")
            raise

        return answer