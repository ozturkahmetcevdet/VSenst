from pyb import Pin, LED
import utime

#USER LED FUCTION
RED = Pin('B14', Pin.OUT_PP)
BLUE = Pin('B12', Pin.OUT_PP)

def REDLed(value=False):
    if value == True:
        RED.high()
    else:
        RED.low()

def BLUELed(value=False):
    if value == True:
        BLUE.high()
    else:
        BLUE.low()

#TACTILE SWITCH FUNCTION
pressTime = 0
releaseTime = 0
holdTime = 0
USERBTN = Pin('A13', Pin.IN, Pin.PULL_UP)

def USERBTNCallback():
    global pressTime
    global releaseTime
    global holdTime

    if USERBTN.value() == 1:
        pressTime = 0
        releaseTime = 0
        holdTime = 0

    if USERBTN.value() == 0 and pressTime == 0:
        pressTime = utime.ticks_ms()
    elif pressTime != 0:
        releaseTime = utime.ticks_ms()
        holdTime = releaseTime - pressTime
        return holdTime
    return 0
        #print(holdTime, Operation.Mode.Value)