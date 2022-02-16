from pyb import UART
import time
import register

class NextionCommand:
    class Page:
        Buffer = str()
        Backup= str()
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
        def ClearBuffer(self):
            self.Backup = str()
    class Ignition:
        Buffer = str()
        Backup= str()
        Repeat = False
        Headline = "ign.pic="
        On = "3"
        Off = "2"
        def ClearBuffer(self):
            self.Backup = str()
    class Seat:
        NumberOfSeats = register.MAX_SEAT_NUMBER
        Buffer = [str()] * NumberOfSeats
        Backup= [str()] * NumberOfSeats
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
        #kayıtlı boş sosyal 17 kayıtsız dolu 18
        def ClearBuffer(self):
            self.Backup = [str()] * self.NumberOfSeats
    class Counters:
        Buffer = str()
        Backup= str()
        Repeat = False
        Headline = "c.pic="
        Default = 84
        def ClearBuffer(self):
            self.Backup = str()
    class Record:
        Buffer = str()
        Backup= str()
        Headline = "rec.pic="
        Default = "20"
        Services = "19"
        RecordMode = "21"
        def ClearBuffer(self):
            self.Backup = str()
    class Services:
        Buffer = str()
        Backup= str()
        Repeat = False
        Headline = "rec.pic="
        On = "11"
        def ClearBuffer(self):
            self.Backup = str()
    class Door:
        Buffer = str()
        Backup= str()
        Repeat = False
        Headline = "door.pic="
        Open = "52"
        Close = "51"
        def ClearBuffer(self):
            self.Backup = str()
    class SocialDistance:
        Buffer = str()
        Backup= str()
        Repeat = False
        Headline = "SDC.pic"
        On = "23"
        Off = "24"
        def ClearBuffer(self):
            self.Backup = str()
            #SD.pic=26 yasaklı uyarı

    def ClearAllBuffer(self):
        NextionCommand.Page.ClearBuffer(NextionCommand.Page)
        NextionCommand.Ignition.ClearBuffer(NextionCommand.Ignition)
        NextionCommand.Seat.ClearBuffer(NextionCommand.Seat)
        NextionCommand.Counters.ClearBuffer(NextionCommand.Counters)
        NextionCommand.Record.ClearBuffer(NextionCommand.Record)
        NextionCommand.Services.ClearBuffer(NextionCommand.Services)
        NextionCommand.Door.ClearBuffer(NextionCommand.Door)
        NextionCommand.SocialDistance.ClearBuffer(NextionCommand.SocialDistance)


class Display():
    def __init__(self):
        super().__init__()
        self.Setup()
    
    def Setup(self):
        self.UART = UART(2, 38400)

    def Process(self):
        self.Page()
        self.Ignition()
        self.Seat()
        self.Counters()
        self.Record()
        self.Services()
        self.Door()

    def Page(self):
        if NextionCommand.Page.Buffer is not NextionCommand.Page.Backup:
            self.SendCommand(NextionCommand.Page.Headline + NextionCommand.Page.Buffer)
            NextionCommand.Page.Backup = NextionCommand.Page.Buffer

    def Ignition(self):
        if NextionCommand.Ignition.Buffer is not NextionCommand.Ignition.Backup:
            self.SendCommand(NextionCommand.Ignition.Headline + NextionCommand.Ignition.Buffer)
            NextionCommand.Ignition.Backup = NextionCommand.Ignition.Buffer

    def Seat(self):
        for i in range(NextionCommand.Seat.NumberOfSeats):
            if NextionCommand.Seat.Buffer[i] is not NextionCommand.Seat.Backup[i]:
                self.SendCommand(NextionCommand.Seat.Headline + str(i + 1) + NextionCommand.Seat.Buffer[i])
                NextionCommand.Seat.Backup[i] = NextionCommand.Seat.Buffer[i]

    def Counters(self):
        if NextionCommand.Counters.Buffer is not NextionCommand.Counters.Backup:
            self.SendCommand(NextionCommand.Counters.Headline + NextionCommand.Counters.Buffer)
            NextionCommand.Counters.Backup = NextionCommand.Counters.Buffer

    def Record(self):
        if NextionCommand.Record.Buffer is not NextionCommand.Record.Backup:
            self.SendCommand(NextionCommand.Record.Headline + NextionCommand.Record.Buffer)
            NextionCommand.Record.Backup = NextionCommand.Record.Buffer

    def Services(self):
        if NextionCommand.Services.Buffer is not NextionCommand.Services.Backup:
            self.SendCommand(NextionCommand.Services.Headline + NextionCommand.Services.Buffer)
            NextionCommand.Services.Backup = NextionCommand.Services.Buffer

    def Door(self):
        if NextionCommand.Door.Buffer is not NextionCommand.Door.Backup:
            self.SendCommand(NextionCommand.Door.Headline + NextionCommand.Door.Buffer)
            NextionCommand.Door.Backup = NextionCommand.Door.Buffer

    def SendCommand(self, buf = ""):
        self.UART.write(buf)
        self.NextionEndCommand()
    
    def NextionEndCommand(self):
        self.UART.write(b'\xff\xff\xff')
        
