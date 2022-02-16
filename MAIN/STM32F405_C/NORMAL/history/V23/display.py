from pyb import UART
import utime
import register


class LCDCommand:
    class Page:
        Buffer = str()
        Backup = str()
        Repeat = False
        Headline = "P."
        Entry    = "1" #Page 0_1
        Main     = "2" #Page_1
        Bye      = "3" #Page_Bye
        Alarm    = "4" #Page_Alarm

        def ClearBuffer(self):
            self.Backup = str()

    class Ignition:
        Buffer = str()
        Backup = str()
        Repeat = False
        Headline = "I."
        On       = "1" #Ignition_On
        Off      = "2" #Ignition_Off

        def ClearBuffer(self):
            self.Backup = str()

    class Seat:
        NumberOfSeats = register.MAX_SEAT_NUMBER
        Buffer = [str()] * NumberOfSeats
        Backup = [str()] * NumberOfSeats
        Repeat = False
        Headline                  = "S."
        Saved                     = "1" #Seat_Ok
        Unregistered              = "2" #Seat_Unregistered
        Registered                = "3" #Seat_Registered
        Full                      = "4" #Seat_Red
        FullWithSeatBeltAttached  = "5" #Seat_Green
        BlankWithSeatBeltAttached = "6" #Seat_Yellow
        PadError                  = "7" #Seat_Fault
        HubError                  = "8" #Seat_Fault
        PadShortCircuit           = "9" #Seat_Fault

        def ClearBuffer(self):
            self.Backup = [str()] * self.NumberOfSeats

    class Counters:
        Buffer = str()
        Backup = str()
        Repeat = False
        Headline = "C."
        Default  = 1 #C0-25

        def ClearBuffer(self):
            self.Backup = str()

    class Record:
        Buffer = str()
        Backup = str()
        Repeat = False
        Headline   = "R."
        Default    = "1" #Mode_Null
        RecordMode = "2" #Mode_Record
        Services   = "3" #Mode_Service

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
        Headline = "L."
        Sleep    = "0"
        WakeUp   = "1"

        def ClearBuffer(self):
            self.Backup = str()

    class ProgressBar:
        Buffer = str()
        Backup = str()
        Repeat = False
        Headline = "sens.val="

        def ClearBuffer(self):
            self.Backup = str()

    class Diagnostic:
        Buffer = str()
        Backup = str()
        Repeat = False
        Headline = "diag.txt="

        def ClearBuffer(self):
            self.Backup = str()


    def ClearAllBuffer(self):
        LCDCommand.Page.ClearBuffer(LCDCommand.Page)
        LCDCommand.Ignition.ClearBuffer(LCDCommand.Ignition)
        LCDCommand.Seat.ClearBuffer(LCDCommand.Seat)
        LCDCommand.Counters.ClearBuffer(LCDCommand.Counters)
        LCDCommand.Record.ClearBuffer(LCDCommand.Record)
        LCDCommand.Services.ClearBuffer(LCDCommand.Services)
        LCDCommand.Door.ClearBuffer(LCDCommand.Door)
        LCDCommand.SocialDistance.ClearBuffer(LCDCommand.SocialDistance)
        LCDCommand.ProgressBar.ClearBuffer(LCDCommand.ProgressBar)
        LCDCommand.Diagnostic.ClearBuffer(LCDCommand.Diagnostic)


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
        self.Counters()
        self.Record()
        #self.ProgressBar()
        #self.Services()
        #self.Door()
        # self.SocialDistance()
        #self.Diagnostic()

    def Page(self):
        if (LCDCommand.Page.Buffer != LCDCommand.Page.Backup) or LCDCommand.Page.Repeat:
            self.SendCommand(LCDCommand.Page.Headline + LCDCommand.Page.Buffer)
            LCDCommand.Page.Backup = LCDCommand.Page.Buffer

    def Ignition(self):
        if (LCDCommand.Ignition.Buffer != LCDCommand.Ignition.Backup) or LCDCommand.Ignition.Repeat:
            self.SendCommand(LCDCommand.Ignition.Headline + LCDCommand.Ignition.Buffer)
            LCDCommand.Ignition.Backup = LCDCommand.Ignition.Buffer

    def Seat(self):
        for i in range(LCDCommand.Seat.NumberOfSeats):
            if (LCDCommand.Seat.Buffer[i] != LCDCommand.Seat.Backup[i]) or LCDCommand.Seat.Repeat:
                self.SendCommand(LCDCommand.Seat.Headline + str(i) + "." + LCDCommand.Seat.Buffer[i])
                LCDCommand.Seat.Backup[i] = LCDCommand.Seat.Buffer[i]

    def Counters(self):
        if (LCDCommand.Counters.Buffer != LCDCommand.Counters.Backup) or LCDCommand.Counters.Repeat:
            self.SendCommand(LCDCommand.Counters.Headline + LCDCommand.Counters.Buffer)
            LCDCommand.Counters.Backup = LCDCommand.Counters.Buffer

    def Record(self):
        if (LCDCommand.Record.Buffer != LCDCommand.Record.Backup) or LCDCommand.Record.Repeat:
            self.SendCommand(LCDCommand.Record.Headline + LCDCommand.Record.Buffer)
            LCDCommand.Record.Backup = LCDCommand.Record.Buffer

    def Services(self):
        if (LCDCommand.Services.Buffer != LCDCommand.Services.Backup) or LCDCommand.Services.Repeat:
            self.SendCommand(LCDCommand.Services.Headline + LCDCommand.Services.Buffer)
            LCDCommand.Services.Backup = LCDCommand.Services.Buffer

    def Door(self):
        if (LCDCommand.Door.Buffer != LCDCommand.Door.Backup) or LCDCommand.Door.Repeat:
            self.SendCommand(LCDCommand.Door.Headline + LCDCommand.Door.Buffer)
            LCDCommand.Door.Backup = LCDCommand.Door.Buffer

    def SocialDistance(self):
        if (LCDCommand.SocialDistance.Buffer != LCDCommand.SocialDistance.Backup) or LCDCommand.SocialDistance.Repeat:
            self.SendCommand(LCDCommand.SocialDistance.Headline + LCDCommand.SocialDistance.Buffer)
            LCDCommand.SocialDistance.Backup = LCDCommand.SocialDistance.Buffer

    def Instructions(self):
        if (LCDCommand.Instructions.Buffer != LCDCommand.Instructions.Backup) or LCDCommand.Instructions.Repeat:
            self.SendCommand(LCDCommand.Instructions.Headline + LCDCommand.Instructions.Buffer)
            LCDCommand.Instructions.Backup = LCDCommand.Instructions.Buffer

    def ProgressBar(self):
        if (LCDCommand.ProgressBar.Buffer != LCDCommand.ProgressBar.Backup) or LCDCommand.ProgressBar.Repeat:
            self.SendCommand(LCDCommand.ProgressBar.Headline + LCDCommand.ProgressBar.Buffer)
            LCDCommand.ProgressBar.Backup = LCDCommand.ProgressBar.Buffer

    def Diagnostic(self):
        if (LCDCommand.Diagnostic.Buffer != LCDCommand.Diagnostic.Backup) or LCDCommand.Diagnostic.Repeat:
            self.SendCommand(LCDCommand.Diagnostic.Headline + LCDCommand.Diagnostic.Buffer)
            LCDCommand.Diagnostic.Backup = LCDCommand.Diagnostic.Buffer

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