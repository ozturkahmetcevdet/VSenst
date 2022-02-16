import pyb
from pyb import Pin, ExtInt, CAN
import time

from SX1239 import SX1239


RED = Pin('Y1', Pin.OUT_PP)
USERBTN = Pin('Y2', Pin.IN, Pin.PULL_UP)

SX1239 = SX1239()
counter = 0
valCounter = 6660

def USERBTNCallback(value):
    if value is 1:
        RED.high()
    else:
        RED.low()

if __name__ == "__main__":

    while True:
        USERBTNCallback(SX1239.DIO2_DATA.value())

        data = SX1239.Read(0x00, 24)
        RSSI = SX1239.Read(0x27, 1)

        if RSSI[0] is not 144:
            strv = ''
            for item in data:
                strv += str(item) + ', '
            #if RSSI[0] is 217:
            print("\n", strv, RSSI[0], "\n")

        #counter += 1
        #if counter is 2:
        #    counter = 0
        #    valCounter -= 1
        #    SX1239.Write(0x03, (valCounter >> 8) & 0xFF)       #RegBitrateMsb
        #    SX1239.Write(0x04, valCounter & 0xFF)              #RegBitrateLsb
        #    if RSSI[0] is 217:
        #        print("\rBitRate: " + str(valCounter) + ", ")
        #if valCounter is 0:
        #    print("\nDone!!!!!\n")
            
        time.sleep(0.025)