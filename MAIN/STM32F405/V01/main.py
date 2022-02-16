import pyb
from pyb import Pin, ExtInt, CAN
import time

from SX1239 import SX1239

RF_RECEIVER = 0
RF_SYNTHESIZER = 1
RF_STANDBY = 2
RF_SLEEP = 3

RED = Pin('Y1', Pin.OUT_PP)
USERBTN = Pin('Y2', Pin.IN, Pin.PULL_UP)

SX1239 = SX1239()

def USERBTNCallback(value):
    if value is 1:
        RED.high()
    else:
        RED.low()

if __name__ == "__main__":

    while True:
        USERBTNCallback(SX1239.DIO0.value())

        data = SX1239.Receive()
        if data[1] is not 0x00:
            print(data)
            
        time.sleep(.025)