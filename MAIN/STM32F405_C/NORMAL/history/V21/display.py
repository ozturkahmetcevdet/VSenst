from pyb import UART
import utime
import register

class LCDCommand:
    class Page:
        Buffer = str()
        Backup = str()
        Repeat = False
        Headline = "P."
        Entry    = "1"  #IMG_0
        Main     = "2"  #IMG_1
        Bye      = "3"  #IMG_20

        def ClearBuffer(self):
            self.Backup = str()

    class Ignition:
        Buffer = str()
        Backup = str()
        Repeat = False
        Headline = "I."
        On       = "1"  #IMG_3
        Off      = "2"  #IMG_2

        def ClearBuffer(self):
            self.Backup = str()

    class Seat:
        NumberOfSeats = register.MAX_SEAT_NUMBER
        Buffer = [str()] * NumberOfSeats
        Backup = [str()] * NumberOfSeats
        Repeat = False
        Headline     = "S."
        Saved        = "1"  #IMG_8
        Unregistered = "2"  #IMG_9
        Registered   = "3"  #IMG_10
        Full         = "4"  #IMG_11

        def ClearBuffer(self):
            self.Backup = [str()] * self.NumberOfSeats

    class Belt:
        NumberOfBelts = register.MAX_SEAT_NUMBER
        Buffer = [str()] * NumberOfBelts
        Backup = [str()] * NumberOfBelts
        Repeat = False
        Headline      = "B."
        Registered    = "1"  #IMG_12
        BeltOffSeatOn = "2"  #IMG_13
        BeltOnSeatOn  = "3"  #IMG_14

        def ClearBuffer(self):
            self.Backup = [str()] * self.NumberOfBelts

    class Record:
        Buffer = str()
        Backup = str()
        Repeat = False
        Headline   = "R."
        Default    = "1"  #IMG_4
        RecordMode = "2"  #IMG_5

        def ClearBuffer(self):
            self.Backup = str()

    class Instructions:
        Buffer = str()
        Backup = str()
        Repeat = False
        Headline = "L."
        Sleep    = "0"
        WakeUp   = "1"

        def ClearBuffer(self):
            self.Backup = str()


    def ClearAllBuffer(self):
        LCDCommand.Page.ClearBuffer(LCDCommand.Page)
        LCDCommand.Ignition.ClearBuffer(LCDCommand.Ignition)
        LCDCommand.Seat.ClearBuffer(LCDCommand.Seat)
        LCDCommand.Belt.ClearBuffer(LCDCommand.Belt)
        LCDCommand.Record.ClearBuffer(LCDCommand.Record)


class Display():
    def __init__(self):
        super().__init__()
        self.Setup()

    def Setup(self):
        #self.UART = UART(2, 115200)
        self.UART = UART(3, 921600) #2000000

    def Process(self):
        self.Instructions()
        self.Page()
        self.Ignition()
        self.Seat()
        self.Belt()
        self.Record()

    def Page(self):
        if LCDCommand.Page.Buffer != LCDCommand.Page.Backup or LCDCommand.Page.Repeat:
            self.SendCommand(LCDCommand.Page.Headline + LCDCommand.Page.Buffer)
            LCDCommand.Page.Backup = LCDCommand.Page.Buffer

    def Ignition(self):
        if LCDCommand.Ignition.Buffer != LCDCommand.Ignition.Backup or LCDCommand.Ignition.Repeat:
            self.SendCommand(LCDCommand.Ignition.Headline + LCDCommand.Ignition.Buffer)
            LCDCommand.Ignition.Backup = LCDCommand.Ignition.Buffer

    def Seat(self):
        for i in range(LCDCommand.Seat.NumberOfSeats):
            if LCDCommand.Seat.Buffer[i] != LCDCommand.Seat.Backup[i] or LCDCommand.Seat.Repeat:
                self.SendCommand(LCDCommand.Seat.Headline + str(i) + "." + LCDCommand.Seat.Buffer[i])
                LCDCommand.Seat.Backup[i] = LCDCommand.Seat.Buffer[i]

    def Belt(self):
        for i in range(LCDCommand.Belt.NumberOfBelts):
            if LCDCommand.Belt.Buffer[i] != LCDCommand.Belt.Backup[i] or LCDCommand.Belt.Repeat:
                self.SendCommand(LCDCommand.Belt.Headline + str(i) + "." + LCDCommand.Belt.Buffer[i])
                LCDCommand.Belt.Backup[i] = LCDCommand.Belt.Buffer[i]

    def Record(self):
        if LCDCommand.Record.Buffer != LCDCommand.Record.Backup or LCDCommand.Record.Repeat:
            self.SendCommand(LCDCommand.Record.Headline + LCDCommand.Record.Buffer)
            LCDCommand.Record.Backup = LCDCommand.Record.Buffer

    def Instructions(self):
        if LCDCommand.Instructions.Buffer != LCDCommand.Instructions.Backup or LCDCommand.Instructions.Repeat:
            self.SendCommand(LCDCommand.Instructions.Headline + LCDCommand.Instructions.Buffer)
            LCDCommand.Instructions.Backup = LCDCommand.Instructions.Buffer

    def SendCommand(self, buf=""):
        try:
            self.UART.write(buf)
            self.NextionEndCommand()
        except OSError as err:
            print("OS error: {0}".format(err))
        except ValueError:
            print("Could not send data over UART.")
        except:
            print("Unexpected error!")
            raise

    def NextionEndCommand(self):
        self.UART.write(b'\xff')

