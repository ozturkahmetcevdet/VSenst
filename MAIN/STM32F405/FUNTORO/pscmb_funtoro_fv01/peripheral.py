from pyb import Pin, Timer
import utime


IGNITION = Pin('Y7', Pin.IN, Pin.PULL_DOWN)

startTime = 0
stopTime = 0
ignitionFlag = False
ignitionTriggerValue = 250


def IGNITIONCallback():
    global startTime
    global stopTime
    global ignitionFlag
    global ignitionTriggerValue

    if IGNITION.value() is 1 and ignitionFlag is False:
        stopTime = 0
        if startTime == 0:
            startTime = utime.ticks_ms()
        if (utime.ticks_ms() - startTime) > ignitionTriggerValue:
            ignitionFlag = True
    elif IGNITION.value() is 0 and ignitionFlag is True:
        startTime = 0
        if stopTime == 0:
            stopTime = utime.ticks_ms()
        if (utime.ticks_ms() - stopTime) > ignitionTriggerValue:
            ignitionFlag = False

    return ignitionFlag


buzPin = Pin('X1')
buzTimer = Timer(2, freq=1000)
buzChannel = buzTimer.channel(1, Timer.PWM, pin=buzPin)

buzzerOrderList = []


def buzzer(value=0):
    buzChannel.pulse_width_percent(value)


toggleValue = False


def buzzerToggle(timer):
    global toggleValue
    global buzzerOrderList
    if toggleValue is False:
        buzzer(50)
        toggleValue = True
    else:
        buzzer(0)
        toggleValue = False

    # if toggleValue is True:
    #    timer.freq(1000 / buzzerOrderList[1])
    # else:
    #    timer.freq(1000 / buzzerOrderList[2])

    if buzzerOrderList[0] > 0 and toggleValue is True:
        buzzerOrderList[0] -= 1
    elif buzzerOrderList[0] < 1 and toggleValue is False:
        buzzer(0)
        buzzerOrderList = []
        timer.callback(None)
        timer.deinit()


def buzzerObject(replay=1, onTime=100, offTime=100, priority=1):
    global buzzerOrderList
    global toggleValue

    buzzerOrderList = [replay, onTime, offTime, priority]
    toggleValue = False
    periodicTimer = Timer(4, freq=1000 / buzzerOrderList[1])
    periodicTimer.callback(buzzerToggle)
