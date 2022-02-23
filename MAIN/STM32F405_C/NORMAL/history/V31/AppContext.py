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
        Calibrate = True

ignitionFlag = False

def defineOperationMode(holdTime=0):
    global ignitionFlag

    if ignitionFlag == False:
        return

    if holdTime > 100 and holdTime < 1250 and Operation.Mode.ShortLock == False:
        if Operation.Mode.Value == Operation.Mode.Standby:
            Operation.Mode.Value = Operation.Mode.Register
            DB.InstructionJson['Refresh'] = True
        elif Operation.Mode.Value == Operation.Mode.Register:
            Operation.Mode.Value = Operation.Mode.Standby
            Operation.Mode.Save = True
            Operation.Mode.ClearBuffer = True
            Operation.Mode.Calibrate = True
            DB.InstructionJson['Refresh'] = True
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
        Sub.RST.high()

        DB.RefreshData('LowPower', Sub.LowPower.WakeUp)
        if Operation.Mode.Value == Operation.Mode.Sleep:
            if openingTime == 0:
                openingTime = utime.ticks_ms()
                DB.RefreshData('Page', Sub.Page.Entry)
            if (utime.ticks_ms() - openingTime) > DataBase.OPEN_SCENE_SHOW_TIME:
                DB.RefreshData('Page', Sub.Page.Main)
                DB.RefreshData('Ignition', Sub.Ignition.On)

                if Operation.Mode.Value == Operation.Mode.Sleep:
                    Operation.Mode.Value = Operation.Mode.Standby
                    DB.InstructionJson['Refresh'] = True
        else:
            DB.RefreshData('Page', Sub.Page.Main)
            DB.RefreshData('Ignition', Sub.Ignition.On)

        closingTime = 0
        closingSceneTime = 0
    else:
        DB.RefreshData('Ignition', Sub.Ignition.Off)
        if closingTime == 0:
            closingTime = utime.ticks_ms()
            # kapanırken alarm var ise buraya yazılacak
        if (utime.ticks_ms() - closingTime) > DataBase.CLOSING_TIME:
            if closingSceneTime == 0:
                closingSceneTime = utime.ticks_ms()
                DB.RefreshData('Page', Sub.Page.Bye)          
            if (utime.ticks_ms() - closingSceneTime) > DataBase.CLOSE_SCENE_SHOW_TIME:
                DB.RefreshData('LowPower', Sub.LowPower.Sleep)  
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

        if Operation.Mode.Calibrate is True:
            if DB.HubList:
                for item in DB.HubList:
                    item.calibrationRequest = True
            Operation.Mode.Calibrate = False

        userControl.BLUELed(False)
        DB.RefreshData('Record', Sub.Record.Default)

        if SX1239.IsBufferReady() == True:
            userControl.REDLed(True)
            DB.Process(SX1239.ReadBuffer())
            SX1239.ClearBuffer()

        else:
            userControl.REDLed(False)

    if Operation.Mode.Value == Operation.Mode.Register:
        if Operation.Mode.ClearBuffer == True:
            SX1239.ClearBuffer()
            Operation.Mode.ClearBuffer = False

        userControl.BLUELed(True)
        DB.RefreshData('Record', Sub.Record.RecordMode)
        DB.RefreshData('Counter', 0)

        if SX1239.IsBufferReady() == True:
            userControl.REDLed(True)
            DB.DefineHubObject(SX1239.ReadBuffer())
            SX1239.ClearBuffer()
        else:
            userControl.REDLed(False)

    if Operation.Mode.Value == Operation.Mode.Delete:
        SX1239.ClearBuffer()
        DB.ClearAllData()

        userControl.BLUELed(True)
        utime.sleep_ms(250)
        Operation.Mode.Value = Operation.Mode.Standby

    if DB.InstructionJson['Refresh']:
        Sub.Process(buffer=DB.GetInstructionJsonAsString())
        DB.ClearUnnecessaryFiles()
        print("\n\r{0}".format(DB.free()))
