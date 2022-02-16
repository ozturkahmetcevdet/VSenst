from pyb import Pin, Timer
import time, utime

ESP32RESET      = Pin('B0', Pin.OUT_PP)
ESP32CONTROL    = Pin('B1', Pin.OUT_PP)
IGNITION        = Pin('A14', Pin.IN, Pin.PULL_DOWN)

def ESP32_RESTART():
    ESP32CONTROL.high()
    ESP32RESET.low()
    time.sleep(0.01)
    ESP32RESET.high()


startTime            = 0
stopTime             = 0
ignitionFlag         = False
ignitionTriggerValue = 25

def IGNITIONCallback():
    global startTime
    global stopTime
    global ignitionFlag
    global ignitionTriggerValue

    if IGNITION.value() == 1 and ignitionFlag == False:
        stopTime = 0
        if startTime == 0:
            startTime = utime.ticks_ms()
        if (utime.ticks_ms() - startTime) > ignitionTriggerValue:
            ignitionFlag = True
    elif IGNITION.value() == 0 and ignitionFlag == True:
        startTime = 0
        if stopTime == 0:
            stopTime = utime.ticks_ms()
        if (utime.ticks_ms() - stopTime) > ignitionTriggerValue:
            ignitionFlag = False

    return ignitionFlag



buzPin          = Pin('B13')
buzTimer        = Timer(1, freq=1000)
buzChannel      = buzTimer.channel(1, Timer.PWM, pin=buzPin)
toggleValue     = False
buzzerOrderList = []

def buzzer(value=0):
    buzChannel.pulse_width_percent(value)

def buzzerToggle(timer):
    global toggleValue
    global buzzerOrderList
    if toggleValue == False:
        buzzer(50)
        toggleValue = True
    else:
        buzzer(0)
        toggleValue = False

    # if toggleValue == True:
    #    timer.freq(1000 / buzzerOrderList[1])
    # else:
    #    timer.freq(1000 / buzzerOrderList[2])

    if buzzerOrderList[0] > 0 and toggleValue == True:
        buzzerOrderList[0] -= 1
    elif buzzerOrderList[0] < 1 and toggleValue == False:
        buzzer(0)
        buzzerOrderList = []
        timer.callback(None)
        timer.deinit()


def buzzerObject(replay=1, onTime=100, offTime=100, priority=1):
    global toggleValue
    global buzzerOrderList

    buzzerOrderList = [replay, onTime, offTime, priority]
    toggleValue = False
    periodicTimer = Timer(4, freq=1000 // buzzerOrderList[1])
    periodicTimer.callback(buzzerToggle)
