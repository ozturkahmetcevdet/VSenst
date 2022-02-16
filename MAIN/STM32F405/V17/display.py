from pyb import UART
import utime
import register


class NextionCommand:
    class Page:
        Buffer = str()
        Backup = str()
        Repeat = False
        Headline = "page "
        Zero = "0"
        FfV16 = "FfV16"
        FVM19 = "FVM19"
        f19 = "f19"
        f20 = "f20"
        M16 = "M16"
        D14 = "D14"
        S = "S"
        S1 = "S1"
        S2 = "S2"
        S3 = "S3"
        S4 = "S4"
        alarm = "alarm"
        SD = "SD"
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
        PadError = ".pic=9"
        Saved = ".pic=10"
        Unregistered = ".pic=11"
        Registered = ".pic=12"
        Full = ".pic=13"
        FullWithSeatBeltAttached = ".pic=14"
        BlankWithSeatBeltAttached = ".pic=15"
        HubError = ".pic=16"
        PadShortCircuit = ".pic=8"
        # kayıtlı boş sosyal 17 kayıtsız dolu 18

        def ClearBuffer(self):
            self.Backup = [str()] * self.NumberOfSeats

    class Counters:
        Buffer = str()
        Backup = str()
        Repeat = False
        Headline = "c.pic="
        Default = 84

        def ClearBuffer(self):
            self.Backup = str()

    class Record:
        Buffer = str()
        Backup = str()
        Repeat = False
        Headline = "rec.pic="
        Default = "20"
        Services = "19"
        RecordMode = "21"

        def ClearBuffer(self):
            self.Backup = str()

    class Services:
        Buffer = str()
        Backup = str()
        Repeat = False
        Headline = "rec.pic="
        On = "11"

        def ClearBuffer(self):
            self.Backup = str()

    class Door:
        Buffer = str()
        Backup = str()
        Repeat = False
        Headline = "door.pic="
        Open = "52"
        Close = "51"

        def ClearBuffer(self):
            self.Backup = str()

    class SocialDistance:
        Buffer = str()
        Backup = str()
        Repeat = False
        Headline = "SDC.pic"
        On = "23"
        Off = "24"

        def ClearBuffer(self):
            self.Backup = str()
            # SD.pic=26 yasaklı uyarı

    class Instructions:
        Buffer = str()
        Backup = str()
        Repeat = False
        Headline = "sleep="
        Sleep = "1"
        WakeUp = "0"

        def ClearBuffer(self):
            self.Backup = str()

    class Diagnostic:
        Buffer = str()
        Backup = str()
        Repeat = True
        Headline = "diag.txt="

        def ClearBuffer(self):
            self.Backup = str()


    def ClearAllBuffer(self):
        NextionCommand.Page.ClearBuffer(NextionCommand.Page)
        NextionCommand.Ignition.ClearBuffer(NextionCommand.Ignition)
        NextionCommand.Seat.ClearBuffer(NextionCommand.Seat)
        NextionCommand.Counters.ClearBuffer(NextionCommand.Counters)
        NextionCommand.Record.ClearBuffer(NextionCommand.Record)
        NextionCommand.Services.ClearBuffer(NextionCommand.Services)
        NextionCommand.Door.ClearBuffer(NextionCommand.Door)
        NextionCommand.SocialDistance.ClearBuffer(NextionCommand.SocialDistance)
        NextionCommand.Diagnostic.ClearBuffer(NextionCommand.Diagnostic)


class Display():
    def __init__(self):
        super().__init__()
        self.Setup()

    def Setup(self):
        #self.UART = UART(2, 115200)
        self.UART = UART(3, 2000000) #921600

    def Process(self):
        self.Instructions()
        self.Page()
        self.Ignition()
        self.Seat()
        self.Counters()
        self.Record()
        self.Services()
        self.Door()
        # self.SocialDistance()
        #self.Diagnostic()

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

    def Counters(self):
        if NextionCommand.Counters.Buffer != NextionCommand.Counters.Backup or NextionCommand.Counters.Repeat:
            self.SendCommand(NextionCommand.Counters.Headline + NextionCommand.Counters.Buffer)
            NextionCommand.Counters.Backup = NextionCommand.Counters.Buffer

    def Record(self):
        if NextionCommand.Record.Buffer != NextionCommand.Record.Backup or NextionCommand.Record.Repeat:
            self.SendCommand(NextionCommand.Record.Headline + NextionCommand.Record.Buffer)
            NextionCommand.Record.Backup = NextionCommand.Record.Buffer

    def Services(self):
        if NextionCommand.Services.Buffer != NextionCommand.Services.Backup or NextionCommand.Services.Repeat:
            self.SendCommand(NextionCommand.Services.Headline + NextionCommand.Services.Buffer)
            NextionCommand.Services.Backup = NextionCommand.Services.Buffer

    def Door(self):
        if NextionCommand.Door.Buffer != NextionCommand.Door.Backup or NextionCommand.Door.Repeat:
            self.SendCommand(NextionCommand.Door.Headline + NextionCommand.Door.Buffer)
            NextionCommand.Door.Backup = NextionCommand.Door.Buffer

    def SocialDistance(self):
        if NextionCommand.SocialDistance.Buffer != NextionCommand.SocialDistance.Backup or NextionCommand.SocialDistance.Repeat:
            self.SendCommand(NextionCommand.SocialDistance.Headline + NextionCommand.SocialDistance.Buffer)
            NextionCommand.SocialDistance.Backup = NextionCommand.SocialDistance.Buffer

    def Instructions(self):
        if NextionCommand.Instructions.Buffer != NextionCommand.Instructions.Backup or NextionCommand.Instructions.Repeat:
            self.SendCommand(NextionCommand.Instructions.Headline + NextionCommand.Instructions.Buffer)
            NextionCommand.Instructions.Backup = NextionCommand.Instructions.Buffer

    def Diagnostic(self):
        if NextionCommand.Diagnostic.Buffer != NextionCommand.Diagnostic.Backup or NextionCommand.Diagnostic.Repeat:
            self.SendCommand(NextionCommand.Diagnostic.Headline + NextionCommand.Diagnostic.Buffer)
            NextionCommand.Diagnostic.Backup = NextionCommand.Diagnostic.Buffer

    def SendCommand(self, buf=""):
        try:
            self.UART.write(buf)
            self.NextionEndCommand()
        except OSError:
            pass

    def NextionEndCommand(self):
        self.UART.write(b'\xff\xff\xff')

