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

#NEXTIONCOMMAND.Page.Buffer = NEXTIONCOMMAND.Page.Zero
#NEXTIONCOMMAND.Ignition.Buffer = NEXTIONCOMMAND.Ignition.Off


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
        else:
            Operation.Mode.Value = Operation.Mode.Standby
            userControl.BLUELed(False)
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
        if Operation.Mode.Value == Operation.Mode.Sleep:
            if openingTime == 0:
                openingTime = utime.ticks_ms()
                NEXTIONCOMMAND.Page.Buffer = NEXTIONCOMMAND.Page.Zero
            if (utime.ticks_ms() - openingTime) > register.OPEN_SCENE_SHOW_TIME:
                NEXTIONCOMMAND.Page.Buffer = NEXTIONCOMMAND.Page.FfV16
                NEXTIONCOMMAND.Ignition.Buffer = NEXTIONCOMMAND.Ignition.On
                for i in range(NEXTIONCOMMAND.Seat.NumberOfSeats):
                    NEXTIONCOMMAND.Seat.Buffer[i] = NEXTIONCOMMAND.Seat.Unregistered
                if Operation.Mode.Value == Operation.Mode.Sleep:
                    Operation.Mode.Value = Operation.Mode.Standby
                    # machine.reset()
        else:
            NEXTIONCOMMAND.Page.Buffer = NEXTIONCOMMAND.Page.FfV16
            NEXTIONCOMMAND.Ignition.Buffer = NEXTIONCOMMAND.Ignition.On
            for i in range(NEXTIONCOMMAND.Seat.NumberOfSeats):
                NEXTIONCOMMAND.Seat.Buffer[i] = NEXTIONCOMMAND.Seat.Unregistered
        closingTime = 0
        closingSceneTime = 0
    else:
        NextionCommand.Ignition.Buffer = NextionCommand.Ignition.Off
        if closingTime == 0:
            closingTime = utime.ticks_ms()
            # kapan??rken alarm var ise buraya yaz??lacak
        if (utime.ticks_ms() - closingTime) > register.CLOSING_TIME:
            if closingSceneTime == 0:
                closingSceneTime = utime.ticks_ms()
                NEXTIONCOMMAND.Page.Buffer = NEXTIONCOMMAND.Page.Bye
            if (utime.ticks_ms() - closingSceneTime) > register.CLOSE_SCENE_SHOW_TIME:
                NEXTIONCOMMAND.ClearAllBuffer()
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
        counter = 0
        for item in DB.SensorList:
            if item.Prox2_IsSeatActive == True:
                if item.Prox2_IsSeatHasPassanger == True:
                    if item.Prox2_IsSeatHasBelt == True:
                        NEXTIONCOMMAND.Seat.Buffer[c] = NEXTIONCOMMAND.Seat.FullWithSeatBeltAttached
                    else:
                        NEXTIONCOMMAND.Seat.Buffer[c] = NEXTIONCOMMAND.Seat.Full
                    counter += 1
                else:
                    if item.Prox2_IsSeatHasBelt == True:
                        NEXTIONCOMMAND.Seat.Buffer[c] = NEXTIONCOMMAND.Seat.BlankWithSeatBeltAttached
                    else:
                        NEXTIONCOMMAND.Seat.Buffer[c] = NEXTIONCOMMAND.Seat.Registered
                c += 1
            if item.Prox1_IsSeatActive == True:
                if item.Prox1_IsSeatHasPassanger == True:
                    if item.Prox1_IsSeatHasBelt == True:
                        NEXTIONCOMMAND.Seat.Buffer[c] = NEXTIONCOMMAND.Seat.FullWithSeatBeltAttached
                    else:
                        NEXTIONCOMMAND.Seat.Buffer[c] = NEXTIONCOMMAND.Seat.Full
                    counter += 1
                else:
                    if item.Prox1_IsSeatHasBelt == True:
                        NEXTIONCOMMAND.Seat.Buffer[c] = NEXTIONCOMMAND.Seat.BlankWithSeatBeltAttached
                    else:
                        NEXTIONCOMMAND.Seat.Buffer[c] = NEXTIONCOMMAND.Seat.Registered
                c += 1
        NEXTIONCOMMAND.Counters.Buffer = str(NEXTIONCOMMAND.Counters.Default + counter)

        if SX1239.IsBufferReady() == True:
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
            if item.Prox1_IsSeatActive == True:
                NEXTIONCOMMAND.Seat.Buffer[c] = NEXTIONCOMMAND.Seat.Saved
                c += 1
            if item.Prox2_IsSeatActive == True:
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
        NEXTIONCOMMAND.Counters.Buffer = str(NEXTIONCOMMAND.Counters.Default + 0)

        userControl.BLUELed(True)
        utime.sleep_ms(250)
        Operation.Mode.Value = Operation.Mode.Standby
        
    Display.Process()
