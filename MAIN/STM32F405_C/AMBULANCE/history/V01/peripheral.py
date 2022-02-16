from pyb import Pin, Timer
import time

NEXTIONCOMMAND = ""
ESP32RESET = Pin('B0', Pin.OUT_PP)
ESP32CONTROL = Pin('B1', Pin.OUT_PP)
IGNITION = Pin('A14', Pin.IN, Pin.PULL_DOWN)

startTime = 0
stopTime = 0
ignitionFlag = False
ignitionTriggerValue = 250

def ESP32_RESET():
    ESP32CONTROL.high()
    ESP32RESET.low()
    time.sleep(0.1)
    ESP32RESET.high()



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

    return True#ignitionFlag




buzPin = Pin('B13')
buzTimer = Timer(1, freq=1000)
buzChannel = buzTimer.channel(1, Timer.PWM, pin=buzPin)

buzzerOrderList = []
toggleBuzzerValue = False
toggleObjectValue = False
BuzzerActivity = False
BuzzerShutdown = False

def buzzer(value=0):
    buzChannel.pulse_width_percent(value)

def buzzerToggle(timer):
    global toggleBuzzerValue
    global buzzerOrderList

    if toggleBuzzerValue == False:
        buzzer(50)
        toggleBuzzerValue = True
    else:
        buzzer(0)
        toggleBuzzerValue = False

    # if toggleBuzzerValue == True:
    #    timer.freq(1000 / buzzerOrderList[1])
    # else:
    #    timer.freq(1000 / buzzerOrderList[2])

    if buzzerOrderList[0] > 0 and toggleBuzzerValue == True:
        buzzerOrderList[0] -= 1
    elif buzzerOrderList[0] < 1 and toggleBuzzerValue == False:
        buzzer(0)
        buzzerOrderList = []
        timer.callback(None)
        timer.deinit()



def buzzerObject(replay=1, onTime=100, offTime=100, priority=1):
    global buzzerOrderList
    global toggleBuzzerValue

    buzzerOrderList = [replay, onTime, offTime, priority]
    toggleBuzzerValue = False
    periodicTimer = Timer(4, freq=1000 / buzzerOrderList[1])
    periodicTimer.callback(buzzerToggle)


BuzzerLevelCounter = 0
ToggleObjectList = []
BuzzerActivityCounter = 0
BuzzerActivityDeCounter = 0

def ToggleAddObject(_object, _value1, _value2):
    global ToggleObjectList

    OK = False
    for item in ToggleObjectList:
        #print(item)
        if item == [_object, _value1, _value2]:
            OK = True
    if OK == False:
        ToggleObjectList.append([_object, _value1, _value2])

def ToggleRemoveObject(_object, _value1, _value2):
    global ToggleObjectList
    ToggleObjectList.remove([_object, _value1, _value2])

def ms100Timer(timer):
    global BuzzerActivity
    global toggleBuzzerValue
    global toggleObjectValue
    global buzTimer
    global BuzzerLevelCounter
    global ToggleObjectList
    global BuzzerActivityCounter
    global BuzzerActivityDeCounter
    global BuzzerShutdown

    if BuzzerActivity == True and BuzzerShutdown == False:
        if toggleObjectValue == False:
            toggleObjectValue = True
            for item in ToggleObjectList:
                NEXTIONCOMMAND.Belt.Buffer[item[0]] = item[1]
        else:
            toggleObjectValue = False
            for item in ToggleObjectList:
                NEXTIONCOMMAND.Belt.Buffer[item[0]] = item[2]

        BuzzerActivityDeCounter = 0
        BuzzerActivityCounter += 1
        if BuzzerActivityCounter > 20:
            BuzzerActivityCounter = 100
            if toggleBuzzerValue == False:
                buzzer(50)
                toggleBuzzerValue = True
            else:
                buzzer(0)
                toggleBuzzerValue = False

            BuzzerLevelCounter += 1
            if BuzzerLevelCounter > 60:
                buzTimer.freq(1000)
            else:
                buzTimer.freq(1250)
    
    if BuzzerActivity == False or BuzzerShutdown == True:
        buzzer(0)
        BuzzerActivityDeCounter += 1
        if BuzzerActivityDeCounter > 2:
            buzTimer.freq(1250)
            toggleBuzzerValue = False
            toggleObjectValue = False
            BuzzerLevelCounter = 0
            BuzzerActivityCounter = 0
            BuzzerActivityDeCounter = 0

        
ms100TimerObject = Timer(3, freq=2)
ms100TimerObject.callback(ms100Timer)