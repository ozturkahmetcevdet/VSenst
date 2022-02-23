import utime
import peripheral
import userControl
import DataBase
import SX1239
import SubController

DB = DataBase.DataBase()

SX1239 = SX1239.SX1239()
SX1239.Receive()

Sub = SubController.Sub()


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

ignitionFlag = False

def defineOperationMode(holdTime=0):
    global ignitionFlag

    if ignitionFlag == False:
        return

    if holdTime > 100 and holdTime < 1250 and Operation.Mode.ShortLock == False:
        if Operation.Mode.Value == Operation.Mode.Standby:
            Operation.Mode.Value = Operation.Mode.Register
        elif Operation.Mode.Value == Operation.Mode.Register:
            Operation.Mode.Value = Operation.Mode.Standby
            Operation.Mode.Save = True
            Operation.Mode.ClearBuffer = True
        else:
            Operation.Mode.Value = Operation.Mode.Standby
            userControl.BLUELed(False)
        Operation.Mode.ShortLock = True
        DB.InstructionJsonRefresh = True
    if holdTime > 1249 and Operation.Mode.LongLock == False:
        Operation.Mode.Value = Operation.Mode.Delete
        Operation.Mode.LongLock = True
        DB.InstructionJsonRefresh = True

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
        Sub.RST.high()

        DB.InstructionJson['LowPower'] = Sub.LowPower.WakeUp
        if Operation.Mode.Value == Operation.Mode.Sleep:
            if openingTime == 0:
                openingTime = utime.ticks_ms()
                DB.InstructionJson['Page'] = Sub.Page.Entry
            if (utime.ticks_ms() - openingTime) > DataBase.OPEN_SCENE_SHOW_TIME:
                DB.InstructionJson['Page'] = Sub.Page.Main
                DB.InstructionJson['Ignition'] = Sub.Ignition.On

                if Operation.Mode.Value == Operation.Mode.Sleep:
                    Operation.Mode.Value = Operation.Mode.Standby
                    SX1239.Start()
                Sub.Process(buffer=DB.GetCoordinateJsonAsString())
                utime.sleep_ms(250)
                Sub.Process(buffer=DB.GetInstructionJsonAsString())
                utime.sleep_ms(50)
                DB.InstructionJsonRefresh = True
        else:
            DB.InstructionJson['Page'] = Sub.Page.Main
            DB.InstructionJson['Ignition'] = Sub.Ignition.On

        closingTime = 0
        closingSceneTime = 0
    else:
        DB.InstructionJson['Ignition'] = Sub.Ignition.Off
        if closingTime == 0:
            closingTime = utime.ticks_ms()
            # kapanırken alarm var ise buraya yazılacak
        if (utime.ticks_ms() - closingTime) > DataBase.CLOSING_TIME:
            if closingSceneTime == 0:
                closingSceneTime = utime.ticks_ms()
                DB.InstructionJson['Page'] = Sub.Page.Bye
            if (utime.ticks_ms() - closingSceneTime) > DataBase.CLOSE_SCENE_SHOW_TIME:
                DB.InstructionJson['LowPower'] = Sub.LowPower.Sleep
                Operation.Mode.Value = Operation.Mode.Sleep
                Sub.RST.low()
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

        userControl.BLUELed(False)
        DB.InstructionJson['Record'] = Sub.Record.Default

        if SX1239.IsBufferReady() == True:
            userControl.REDLed(True)
            DB.Process(SX1239.ReadBuffer())
            userControl.REDLed(False)
        else:
            userControl.REDLed(False)


    if Operation.Mode.Value == Operation.Mode.Register:
        if Operation.Mode.ClearBuffer == True:
            SX1239.ClearBuffer()
            Operation.Mode.ClearBuffer = False

        userControl.BLUELed(True)
        DB.InstructionJson['Record'] = Sub.Record.RecordMode
        DB.InstructionJson['Counter'] = 0

        if SX1239.IsBufferReady() == True:
            userControl.REDLed(True)
            DB.DefineHubObject(SX1239.ReadBuffer())
        else:
            userControl.REDLed(False)

    if Operation.Mode.Value == Operation.Mode.Delete:
        SX1239.ClearBuffer()
        DB.ClearAllData()

        userControl.BLUELed(True)
        utime.sleep_ms(250)
        Operation.Mode.Value = Operation.Mode.Standby

    recivedData = Sub.Receive()
    if recivedData == b'BOOT\r\n':
        Sub.Process(buffer=DB.GetCoordinateJsonAsString())
        utime.sleep_ms(250)
        Sub.Process(buffer=DB.GetInstructionJsonAsString())
        utime.sleep_ms(50)
        DB.InstructionJsonRefresh = True
    elif recivedData == b'uOTA start\r\n':
        import uOTA

        while uOTA.uOTALoop:
            uOTA.ReadAndSaveFile(Sub.ReceiveLine())


    if DB.InstructionJsonRefresh:
        Sub.Process(buffer=DB.GetInstructionJsonAsString())
        DB.ClearUnnecessaryFiles()
        DB.InstructionJsonRefresh = False
