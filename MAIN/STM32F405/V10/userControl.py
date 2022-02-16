from pyb import Pin, LED
import utime

#USER LED FUCTION
RED = Pin('Y1', Pin.OUT_PP)
BLUE = LED(4)

def REDLed(value=False):
    if value is True:
        RED.high()
    else:
        RED.low()

def BLUELed(value=False):
    if value is True:
        BLUE.on()
    else:
        BLUE.off()

#TACTILE SWITCH FUNCTION
pressTime = 0
releaseTime = 0
holdTime = 0
USERBTN = Pin('Y2', Pin.IN, Pin.PULL_UP)

def USERBTNCallback():
    global pressTime
    global releaseTime
    global holdTime

    if USERBTN.value() is 1:
        pressTime = 0
        releaseTime = 0
        holdTime = 0

    if USERBTN.value() is 0 and pressTime is 0:
        pressTime = utime.ticks_ms()
    elif pressTime is not 0:
        releaseTime = utime.ticks_ms()
        holdTime = releaseTime - pressTime
        return holdTime
    return 0
        #print(holdTime, Operation.Mode.Value)