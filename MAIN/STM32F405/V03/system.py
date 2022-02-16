import utime
from SX1239 import SX1239
from display import Display, NextionCommand
import userControl
from register import DataBase

DB = DataBase()

SX1239 = SX1239()

Display = Display()
NEXTIONCOMMAND = NextionCommand()
NEXTIONCOMMAND.ClearAllBuffer()

NEXTIONCOMMAND.Page.Buffer = NEXTIONCOMMAND.Page.FfV16
NEXTIONCOMMAND.Ignition.Buffer = NEXTIONCOMMAND.Ignition.On
for i in range(NEXTIONCOMMAND.Seat.NumberOfSeats):
    NEXTIONCOMMAND.Seat.Buffer[i] = NEXTIONCOMMAND.Seat.Unregistered
NEXTIONCOMMAND.Counters.Buffer = str(NEXTIONCOMMAND.Counters.Default + 10)

class Operation:
    class Mode:
        Value = 0
        Standby = 0
        Register = 1
        Delete = 2
        ShortLock = False
        LongLock = False

def defineOperationMode(holdTime=0):
    if holdTime > 100 and holdTime < 1250 and Operation.Mode.ShortLock is False:
        if Operation.Mode.Value is Operation.Mode.Standby:
            Operation.Mode.Value = Operation.Mode.Register
        elif Operation.Mode.Value is Operation.Mode.Register:
            Operation.Mode.Value = Operation.Mode.Standby
        else:
            Operation.Mode.Value = Operation.Mode.Standby
            userControl.BLUELed(False)
        Operation.Mode.ShortLock = True
    if holdTime > 1249 and Operation.Mode.LongLock is False:
        Operation.Mode.Value = Operation.Mode.Delete
        Operation.Mode.LongLock = True

    if holdTime is 0:
        Operation.Mode.ShortLock = False
        Operation.Mode.LongLock = False
    


def loop():
    Display.Process()
    defineOperationMode(userControl.USERBTNCallback())

    if Operation.Mode.Value is Operation.Mode.Standby:
        userControl.BLUELed(False)
        NEXTIONCOMMAND.Record.Buffer = NEXTIONCOMMAND.Record.Default

        #if SX1239.IsBufferReady() is True:
        #    #data = SX1239.Buffer.Value[0]
        #    print(SX1239.ReadBuffer(0))
        #    SX1239.Buffer.Size = 0

    if Operation.Mode.Value is Operation.Mode.Register:
        userControl.BLUELed(True)
        NEXTIONCOMMAND.Record.Buffer = NEXTIONCOMMAND.Record.RecordMode

    if Operation.Mode.Value is Operation.Mode.Delete:
        userControl.BLUELed(True)
        utime.sleep_ms(1000)
        Operation.Mode.Value = Operation.Mode.Standby

