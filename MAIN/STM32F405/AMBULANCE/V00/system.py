import utime
import peripheral
from SX1239 import SX1239
from display import Display, NextionCommand
import userControl
import register
import machine

DB = register.DataBase()

SX1239 = SX1239()
SX1239.Receive()

Display = Display()
NEXTIONCOMMAND = NextionCommand()
NEXTIONCOMMAND.ClearAllBuffer()
peripheral.NEXTIONCOMMAND = NEXTIONCOMMAND


class Operation:
    class Mode:
        Value = 3
        Standby = 0
        Register = 1
        Delete = 2
        Sleep = 3
        ShortLock = False
        LongLock = False
        Save = False
        ClearBuffer = False


def defineOperationMode(holdTime=0):
    if holdTime > 100 and holdTime < 1250 and Operation.Mode.ShortLock == False:
        if Operation.Mode.Value == Operation.Mode.Standby:
            Operation.Mode.Value = Operation.Mode.Register
            NEXTIONCOMMAND.ClearAllBuffer()
        elif Operation.Mode.Value == Operation.Mode.Register:
            Operation.Mode.Value = Operation.Mode.Standby
            Operation.Mode.Save = True
            Operation.Mode.ClearBuffer = True
            NEXTIONCOMMAND.ClearAllBuffer()
            DB.Process()
        else:
            Operation.Mode.Value = Operation.Mode.Standby
            userControl.BLUELed(False)
            DB.Process()
        Operation.Mode.ShortLock = True
    if holdTime > 1249 and Operation.Mode.LongLock == False:
        Operation.Mode.Value = Operation.Mode.Delete
        Operation.Mode.LongLock = True

    if holdTime == 0:
        Operation.Mode.ShortLock = False
        Operation.Mode.LongLock = False


openingTime = 0
closingTime = 0
closingSceneTime = 0


def defineIgnitionBehavior(value=False):
    global openingTime
    global closingTime
    global closingSceneTime

    if value == True:
        NEXTIONCOMMAND.Instructions.Buffer = NEXTIONCOMMAND.Instructions.WakeUp
        peripheral.BuzzerShutdown = False
        if Operation.Mode.Value == Operation.Mode.Sleep:
            if openingTime == 0:
                openingTime = utime.ticks_ms()
                NEXTIONCOMMAND.Page.Buffer = NEXTIONCOMMAND.Page.Entry
            if (utime.ticks_ms() - openingTime) > register.OPEN_SCENE_SHOW_TIME:
                NEXTIONCOMMAND.Page.Buffer = NEXTIONCOMMAND.Page.Main
                NEXTIONCOMMAND.Ignition.Buffer = NEXTIONCOMMAND.Ignition.On

                if Operation.Mode.Value == Operation.Mode.Sleep:
                    Operation.Mode.Value = Operation.Mode.Standby
                    NEXTIONCOMMAND.ClearAllBuffer()
                    DB.Process()
                    #peripheral.ESP32_RESET()
                    #utime.sleep_ms(1000)
                    # machine.reset()
        else:
            NEXTIONCOMMAND.Page.Buffer = NEXTIONCOMMAND.Page.Main
            NEXTIONCOMMAND.Ignition.Buffer = NEXTIONCOMMAND.Ignition.On

        closingTime = 0
        closingSceneTime = 0
    else:
        NextionCommand.Ignition.Buffer = NextionCommand.Ignition.Off
        peripheral.BuzzerActivity = False
        peripheral.BuzzerShutdown = True
        if closingTime == 0:
            closingTime = utime.ticks_ms()
            # kapanırken alarm var ise buraya yazılacak
        if (utime.ticks_ms() - closingTime) > register.CLOSING_TIME:
            if closingSceneTime == 0:
                closingSceneTime = utime.ticks_ms()
                NEXTIONCOMMAND.Page.Buffer = NEXTIONCOMMAND.Page.Bye
            if (utime.ticks_ms() - closingSceneTime) > register.CLOSE_SCENE_SHOW_TIME:
                NEXTIONCOMMAND.ClearAllBuffer()
                DB.Process()
                NEXTIONCOMMAND.Instructions.Buffer = NEXTIONCOMMAND.Instructions.Sleep
                Operation.Mode.Value = Operation.Mode.Sleep
        openingTime = 0

def loop():    
    defineIgnitionBehavior(peripheral.IGNITIONCallback())
    defineOperationMode(userControl.USERBTNCallback())

    if Operation.Mode.Value == Operation.Mode.Sleep:
        pass

    if Operation.Mode.Value == Operation.Mode.Standby:
        if Operation.Mode.Save is True:
            DB.FlushRawDataToDB()
            Operation.Mode.Save = False

        userControl.BLUELed(False)
        NEXTIONCOMMAND.Record.Buffer = NEXTIONCOMMAND.Record.Default
        c = 0
        alarmBuzzerFlag = False
        for item in DB.SensorList:
            if item.Prox2_SeatHasSensor == True:
                if item.Prox2_IsSeatActive == True:
                    if item.Prox2_IsSeatHasPassanger == True:
                        NEXTIONCOMMAND.Seat.Buffer[c] = NEXTIONCOMMAND.Seat.Full
                        if item.Prox2_IsSeatHasBelt == True:
                            NEXTIONCOMMAND.Belt.Buffer[c] = NEXTIONCOMMAND.Belt.BeltOnSeatOn 
                        else:
                            alarmBuzzerFlag = True
                            peripheral.ToggleAddObject(c, NEXTIONCOMMAND.Belt.BeltOffSeatOn, NEXTIONCOMMAND.Belt.Registered)
                        
                    else:
                        NEXTIONCOMMAND.Seat.Buffer[c] = NEXTIONCOMMAND.Seat.Registered
                        NEXTIONCOMMAND.Belt.Buffer[c] = NEXTIONCOMMAND.Belt.Registered
                c += 1
            if item.Prox1_SeatHasSensor == True:
                if item.Prox1_IsSeatActive == True:
                    if item.Prox1_IsSeatHasPassanger == True:
                        NEXTIONCOMMAND.Seat.Buffer[c] = NEXTIONCOMMAND.Seat.Full
                        if item.Prox1_IsSeatHasBelt == True:
                            NEXTIONCOMMAND.Belt.Buffer[c] = NEXTIONCOMMAND.Belt.BeltOnSeatOn 
                        else:
                            alarmBuzzerFlag = True
                            peripheral.ToggleAddObject(c, NEXTIONCOMMAND.Belt.BeltOffSeatOn, NEXTIONCOMMAND.Belt.Registered)
                        
                    else:
                        NEXTIONCOMMAND.Seat.Buffer[c] = NEXTIONCOMMAND.Seat.Registered
                        NEXTIONCOMMAND.Belt.Buffer[c] = NEXTIONCOMMAND.Belt.Registered
                c += 1

        peripheral.BuzzerActivity = alarmBuzzerFlag

        #print("loop")
        if SX1239.IsBufferReady() == True:
            #print("buffer ready")
            userControl.REDLed(True)
            DB.Process(SX1239.ReadBuffer())
        else:
            userControl.REDLed(False)

    if Operation.Mode.Value == Operation.Mode.Register:
        if Operation.Mode.ClearBuffer == True:
            SX1239.ClearBuffer()
            Operation.Mode.ClearBuffer = False

        userControl.BLUELed(True)
        NEXTIONCOMMAND.Record.Buffer = NEXTIONCOMMAND.Record.RecordMode
        c = 0
        for item in DB.SensorList:
            if item.Prox1_SeatHasSensor == True:
                NEXTIONCOMMAND.Seat.Buffer[c] = NEXTIONCOMMAND.Seat.Saved
                c += 1
            if item.Prox2_SeatHasSensor == True:
                NEXTIONCOMMAND.Seat.Buffer[c] = NEXTIONCOMMAND.Seat.Saved
                c += 1

        if SX1239.IsBufferReady() == True:
            userControl.REDLed(True)
            DB.DefineSensorObject(SX1239.ReadBuffer())
        else:
            userControl.REDLed(False)

    if Operation.Mode.Value == Operation.Mode.Delete:
        SX1239.ClearBuffer()
        DB.ClearAllData()
        for i in range(NEXTIONCOMMAND.Seat.NumberOfSeats):
            NEXTIONCOMMAND.Seat.Buffer[i] = NEXTIONCOMMAND.Seat.Unregistered
            NEXTIONCOMMAND.Belt.Buffer[i] = NEXTIONCOMMAND.Belt.Registered

        userControl.BLUELed(True)
        utime.sleep_ms(250)
        Operation.Mode.Value = Operation.Mode.Standby
        
    Display.Process()
