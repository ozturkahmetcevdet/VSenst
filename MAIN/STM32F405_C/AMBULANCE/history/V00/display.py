from pyb import UART
import utime
import register


class NextionCommand:
    class Page:
        Buffer = str()
        Backup = str()
        Repeat = False
        Headline = "page "
        Entry = "0"
        Main = "1"
        Bye = "bye"

        def ClearBuffer(self):
            self.Backup = str()

    class Ignition:
        Buffer = str()
        Backup = str()
        Repeat = False
        Headline = "ign.pic="
        On = "3"
        Off = "2"

        def ClearBuffer(self):
            self.Backup = str()

    class Seat:
        NumberOfSeats = register.MAX_SEAT_NUMBER
        Buffer = [str()] * NumberOfSeats
        Backup = [str()] * NumberOfSeats
        Repeat = False
        Headline = "seat"
        Saved = ".pic=8"
        Unregistered = ".pic=9"
        Registered = ".pic=10"
        Full = ".pic=11"

        def ClearBuffer(self):
            self.Backup = [str()] * self.NumberOfSeats

    class Belt:
        NumberOfBelts = register.MAX_SEAT_NUMBER
        Buffer = [str()] * NumberOfBelts
        Backup = [str()] * NumberOfBelts
        Repeat = False
        Headline = "belt"
        Registered = ".pic=12"
        BeltOffSeatOn = ".pic=13"
        BeltOnSeatOn = ".pic=14"

        def ClearBuffer(self):
            self.Backup = [str()] * self.NumberOfBelts

    class Record:
        Buffer = str()
        Backup = str()
        Repeat = False
        Headline = "rec.pic="
        Default = "4"
        RecordMode = "5"

        def ClearBuffer(self):
            self.Backup = str()

    class Instructions:
        Buffer = str()
        Backup = str()
        Repeat = False
        Headline = "sleep="
        Sleep = "1"
        WakeUp = "0"

        def ClearBuffer(self):
            self.Backup = str()


    def ClearAllBuffer(self):
        NextionCommand.Page.ClearBuffer(NextionCommand.Page)
        NextionCommand.Ignition.ClearBuffer(NextionCommand.Ignition)
        NextionCommand.Seat.ClearBuffer(NextionCommand.Seat)
        NextionCommand.Belt.ClearBuffer(NextionCommand.Belt)
        NextionCommand.Record.ClearBuffer(NextionCommand.Record)


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
        if NextionCommand.Page.Buffer != NextionCommand.Page.Backup or NextionCommand.Page.Repeat:
            self.SendCommand(NextionCommand.Page.Headline + NextionCommand.Page.Buffer)
            NextionCommand.Page.Backup = NextionCommand.Page.Buffer

    def Ignition(self):
        if NextionCommand.Ignition.Buffer != NextionCommand.Ignition.Backup or NextionCommand.Ignition.Repeat:
            self.SendCommand(NextionCommand.Ignition.Headline + NextionCommand.Ignition.Buffer)
            NextionCommand.Ignition.Backup = NextionCommand.Ignition.Buffer

    def Seat(self):
        for i in range(NextionCommand.Seat.NumberOfSeats):
            if NextionCommand.Seat.Buffer[i] != NextionCommand.Seat.Backup[i] or NextionCommand.Seat.Repeat:
                self.SendCommand(NextionCommand.Seat.Headline + str(i + 1) + NextionCommand.Seat.Buffer[i])
                NextionCommand.Seat.Backup[i] = NextionCommand.Seat.Buffer[i]

    def Belt(self):
        for i in range(NextionCommand.Belt.NumberOfBelts):
            if NextionCommand.Belt.Buffer[i] != NextionCommand.Belt.Backup[i] or NextionCommand.Belt.Repeat:
                self.SendCommand(NextionCommand.Belt.Headline + str(i + 1) + NextionCommand.Belt.Buffer[i])
                NextionCommand.Belt.Backup[i] = NextionCommand.Belt.Buffer[i]

    def Record(self):
        if NextionCommand.Record.Buffer != NextionCommand.Record.Backup or NextionCommand.Record.Repeat:
            self.SendCommand(NextionCommand.Record.Headline + NextionCommand.Record.Buffer)
            NextionCommand.Record.Backup = NextionCommand.Record.Buffer

    def Instructions(self):
        if NextionCommand.Instructions.Buffer != NextionCommand.Instructions.Backup or NextionCommand.Instructions.Repeat:
            self.SendCommand(NextionCommand.Instructions.Headline + NextionCommand.Instructions.Buffer)
            NextionCommand.Instructions.Backup = NextionCommand.Instructions.Buffer

    def SendCommand(self, buf=""):
        try:
            self.UART.write(buf)
            self.NextionEndCommand()
        except OSError:
            pass

    def NextionEndCommand(self):
        self.UART.write(b'\xff\xff\xff')

