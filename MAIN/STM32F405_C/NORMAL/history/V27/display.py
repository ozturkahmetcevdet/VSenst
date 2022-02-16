from micropython import const
from pyb import UART
import utime
import register

LCD_COM_SPEED = const(921600)
LCD_COM_PORT  = const(3)

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
        LCDCommand.Counters.ClearBuffer(LCDCommand.Counters)
        LCDCommand.Record.ClearBuffer(LCDCommand.Record)


class Display():
    def __init__(self):
        super().__init__()
        self.Setup()

    def Setup(self):
        self.UART = UART(LCD_COM_PORT, LCD_COM_SPEED)

    def Process(self):
        self.Instructions()
        self.Page()
        self.Ignition()
        self.Seat()
        self.Counters()
        self.Record()

    def Instructions(self):
        if (LCDCommand.Instructions.Buffer != LCDCommand.Instructions.Backup) or LCDCommand.Instructions.Repeat:
            self.SendCommand("{}{}".format(LCDCommand.Instructions.Headline, LCDCommand.Instructions.Buffer))
            LCDCommand.Instructions.Backup = LCDCommand.Instructions.Buffer

    def Page(self):
        if (LCDCommand.Page.Buffer != LCDCommand.Page.Backup) or LCDCommand.Page.Repeat:
            self.SendCommand("{}{}".format(LCDCommand.Page.Headline, LCDCommand.Page.Buffer))
            LCDCommand.Page.Backup = LCDCommand.Page.Buffer

    def Ignition(self):
        if (LCDCommand.Ignition.Buffer != LCDCommand.Ignition.Backup) or LCDCommand.Ignition.Repeat:
            self.SendCommand("{}{}".format(LCDCommand.Ignition.Headline, LCDCommand.Ignition.Buffer))
            LCDCommand.Ignition.Backup = LCDCommand.Ignition.Buffer

    def Seat(self):
        for i in range(LCDCommand.Seat.NumberOfSeats):
            if (LCDCommand.Seat.Buffer[i] != LCDCommand.Seat.Backup[i]) or LCDCommand.Seat.Repeat:
                self.SendCommand("{}{}.{}".format(LCDCommand.Seat.Headline, i, LCDCommand.Seat.Buffer[i]))
                LCDCommand.Seat.Backup[i] = LCDCommand.Seat.Buffer[i]

    def Counters(self):
        if (LCDCommand.Counters.Buffer != LCDCommand.Counters.Backup) or LCDCommand.Counters.Repeat:
            self.SendCommand("{}{}".format(LCDCommand.Counters.Headline, LCDCommand.Counters.Buffer))
            LCDCommand.Counters.Backup = LCDCommand.Counters.Buffer

    def Record(self):
        if (LCDCommand.Record.Buffer != LCDCommand.Record.Backup) or LCDCommand.Record.Repeat:
            self.SendCommand("{}{}".format(LCDCommand.Record.Headline, LCDCommand.Record.Buffer))
            LCDCommand.Record.Backup = LCDCommand.Record.Buffer

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