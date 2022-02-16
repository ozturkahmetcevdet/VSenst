import utime
import peripheral
import userControl
import SX1239
import display
import register

DB = register.DataBase()

SX1239 = SX1239.SX1239()
SX1239.Receive()

peripheral.ESP32_RESTART()

Display = display.Display()
LCDCOMMAND = display.LCDCommand()
LCDCOMMAND.ClearAllBuffer()

#LCDCOMMAND.Page.Buffer = LCDCOMMAND.Page.Zero
#LCDCOMMAND.Ignition.Buffer = LCDCOMMAND.Ignition.Off


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
        Calibrate = True

ignitionFlag = False

def defineOperationMode(holdTime=0):
    global ignitionFlag

    if ignitionFlag == False:
        return

    if holdTime > 100 and holdTime < 1250 and Operation.Mode.ShortLock == False:
        if Operation.Mode.Value == Operation.Mode.Standby:
            Operation.Mode.Value = Operation.Mode.Register
            LCDCOMMAND.ClearAllBuffer()
        elif Operation.Mode.Value == Operation.Mode.Register:
            Operation.Mode.Value = Operation.Mode.Standby
            Operation.Mode.Save = True
            Operation.Mode.ClearBuffer = True
            Operation.Mode.Calibrate = True
            LCDCOMMAND.ClearAllBuffer()
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
    global ignitionFlag
    global openingTime
    global closingTime
    global closingSceneTime

    ignitionFlag = value
    
    if value == True:
        peripheral.ESP32RESET.high()
        LCDCOMMAND.Instructions.Buffer = LCDCOMMAND.Instructions.WakeUp
        if Operation.Mode.Value == Operation.Mode.Sleep:
            if openingTime == 0:
                openingTime = utime.ticks_ms()
                LCDCOMMAND.Page.Buffer = LCDCOMMAND.Page.Entry
            if (utime.ticks_ms() - openingTime) > register.OPEN_SCENE_SHOW_TIME:
                LCDCOMMAND.Page.Buffer = LCDCOMMAND.Page.Main
                LCDCOMMAND.Ignition.Buffer = LCDCOMMAND.Ignition.On

                if Operation.Mode.Value == Operation.Mode.Sleep:
                    Operation.Mode.Value = Operation.Mode.Standby
                    LCDCOMMAND.ClearAllBuffer()
                    #peripheral.ESP32_RESET()
                    #utime.sleep_ms(1000)
                    # machine.reset()
        elif LCDCOMMAND.Ignition.Buffer != LCDCOMMAND.Ignition.On:
            for i in range(LCDCOMMAND.Seat.NumberOfSeats):
                LCDCOMMAND.Seat.Buffer[i] = LCDCOMMAND.Seat.Unregistered
            LCDCOMMAND.Page.Buffer = LCDCOMMAND.Page.Main
            LCDCOMMAND.Ignition.Buffer = LCDCOMMAND.Ignition.On

        closingTime = 0
        closingSceneTime = 0
    else:
        LCDCOMMAND.Ignition.Buffer = LCDCOMMAND.Ignition.Off
        if closingTime == 0:
            closingTime = utime.ticks_ms()
            # kapanırken alarm var ise buraya yazılacak
        if (utime.ticks_ms() - closingTime) > register.CLOSING_TIME:
            if closingSceneTime == 0:
                closingSceneTime = utime.ticks_ms()
                LCDCOMMAND.Page.Buffer = LCDCOMMAND.Page.Bye            
            if (utime.ticks_ms() - closingSceneTime) > register.CLOSE_SCENE_SHOW_TIME:
                if Operation.Mode.Value != Operation.Mode.Sleep:
                    LCDCOMMAND.ClearAllBuffer()
                LCDCOMMAND.Instructions.Buffer = LCDCOMMAND.Instructions.Sleep
                Operation.Mode.Value = Operation.Mode.Sleep
                peripheral.ESP32RESET.low()
        openingTime = 0

def loop():    
    defineIgnitionBehavior(peripheral.IGNITIONCallback())
    defineOperationMode(userControl.USERBTNCallback())

    if Operation.Mode.Value == Operation.Mode.Sleep:
        utime.sleep_ms(250)

    if Operation.Mode.Value == Operation.Mode.Standby:
        if Operation.Mode.Save is True:
            DB.FlushRawDataToJson()
            Operation.Mode.Save = False

        if Operation.Mode.Calibrate is True:
            if DB.HubList:
                for item in DB.HubList:
                    item.calibrationRequest = True
            Operation.Mode.Calibrate = False

        userControl.BLUELed(False)
        #LCDCOMMAND.Record.Buffer = LCDCOMMAND.Record.Default
        #c = 0
        #counter = 0
        #for item in DB.SensorList:
        #    if item.Prox2_SeatHasSensor == True:
        #        if item.Prox2_IsSeatActive == True:
        #            if item.Prox2_IsSeatHasPassanger == True:
        #                LCDCOMMAND.Seat.Buffer[c] = LCDCOMMAND.Seat.FullWithSeatBeltAttached if item.Prox2_IsSeatHasBelt == True else LCDCOMMAND.Seat.Full
        #                counter += 1
        #            else:
        #                LCDCOMMAND.Seat.Buffer[c] = LCDCOMMAND.Seat.BlankWithSeatBeltAttached if item.Prox2_IsSeatHasBelt == True else LCDCOMMAND.Seat.Registered
        #        else:
        #            LCDCOMMAND.Seat.Buffer[c] = LCDCOMMAND.Seat.PadError
        #        c += 1
#
        #    if item.Prox1_SeatHasSensor == True:
        #        if item.Prox1_IsSeatActive == True:
        #            if item.Prox1_IsSeatHasPassanger == True:
        #                LCDCOMMAND.Seat.Buffer[c] = LCDCOMMAND.Seat.FullWithSeatBeltAttached if item.Prox1_IsSeatHasBelt == True else LCDCOMMAND.Seat.Full
        #                counter += 1
        #            else:
        #                LCDCOMMAND.Seat.Buffer[c] = LCDCOMMAND.Seat.BlankWithSeatBeltAttached if item.Prox1_IsSeatHasBelt == True else LCDCOMMAND.Seat.Registered
        #        else:
        #            LCDCOMMAND.Seat.Buffer[c] = LCDCOMMAND.Seat.PadError
        #        c += 1
        #        
        #LCDCOMMAND.Counters.Buffer = str(LCDCOMMAND.Counters.Default + counter)

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
        LCDCOMMAND.Record.Buffer = LCDCOMMAND.Record.RecordMode

        for i in range(LCDCOMMAND.Seat.NumberOfSeats):
            LCDCOMMAND.Seat.Buffer[i] = LCDCOMMAND.Seat.Unregistered
        LCDCOMMAND.Counters.Buffer = str(LCDCOMMAND.Counters.Default + 0)

        if SX1239.IsBufferReady() == True:
            userControl.REDLed(True)
            DB.DefineHubObject(SX1239.ReadBuffer())
        else:
            userControl.REDLed(False)

        if DB.HubList:
            for item in DB.HubList:
                pass
                #if item.Prox1_SeatHasSensor == True:
                #    LCDCOMMAND.Seat.Buffer[c] = LCDCOMMAND.Seat.Saved
                #    c += 1
                #if item.Prox2_SeatHasSensor == True:
                #    LCDCOMMAND.Seat.Buffer[c] = LCDCOMMAND.Seat.Saved
                #    c += 1

    if Operation.Mode.Value == Operation.Mode.Delete:
        SX1239.ClearBuffer()
        DB.ClearAllData()
        for i in range(LCDCOMMAND.Seat.NumberOfSeats):
            LCDCOMMAND.Seat.Buffer[i] = LCDCOMMAND.Seat.Unregistered
        LCDCOMMAND.Counters.Buffer = str(LCDCOMMAND.Counters.Default + 0)

        userControl.BLUELed(True)
        utime.sleep_ms(250)
        Operation.Mode.Value = Operation.Mode.Standby
        
    Display.Process()
