import gc
from micropython import const
from pyb import Pin, SPI
import time

RCV = const(0)
SYN = const(1)
STD = const(2)
SLP = const(3)

STP = const(0x01)
BSY = const(0x02)
RXD = const(0x04)

RCF = const(915000000)
RCB = const(83330)

SZE = const(9)

class SX1239():
    def __init__(self):
        super().__init__()
        self.RFState = STP
        self.SPI = SPI(1, SPI.MASTER, baudrate=2400000, polarity=0, phase=0, crc=None)
        self.NRST = Pin('C5', Pin.OUT_PP)
        self.NSS = Pin('A4', Pin.OUT_PP)
        self.DIO0 = Pin('C4', Pin.IN, Pin.PULL_UP)
        self.buffer = []
        self.Setup()

    def Setup(self):
        self.ResetDevice()
        # RC CALIBRATION (Once at POR)
        self.SetRfMode(STD)
        self.StartOscillator()
        self.RegisterConfiguration()
        self.SetRfMode(SLP)
        self.DIO0.irq(trigger=Pin.IRQ_RISING, handler=self.IsPayloadReady)
        gc.collect()

    def ResetDevice(self):
        self.NRST.low()
        time.sleep(.01)
        self.NSS.high()

    def StartOscillator(self):
        self.Write(0x57, 0x80)
        self.Write(0x0A, self.Read(0x0A, 1)[0] | 0x80)
        timeOut = 10
        while (self.Read(0x0A, 1)[0] & 0x40) == 0 and timeOut > 0:
            timeOut -= 1
            time.sleep(.001)
        #if timeout is 0 goto errorhandler
        self.Write(0x0A, self.Read(0x0A, 1)[0] | 0x80)
        timeOut = 10
        while (self.Read(0x0A, 1)[0] & 0x40) == 0 and timeOut > 0:
            timeOut -= 1
            time.sleep(.001)
        #if timeout is 0 goto errorhandler
        self.Write(0x57, 0x00)

    def RegisterConfiguration(self):
        RegisterValues = [[0x01, 0b10000001],
                         [0x02, 0b00000000],
                         [0x03, ((int)(32000000 / RCB) >> 8) & 0xFF],
                         [0x04, ((int)(32000000 / RCB) >> 0) & 0xFF],
                         [0x07, ((int)(RCF / 61.03515625) >> 16) & 0xFF],
                         [0x08, ((int)(RCF / 61.03515625) >>  8) & 0xFF],
                         [0x09, ((int)(RCF / 61.03515625) >>  0) & 0xFF],
                         [0x0B, 0b00000000],
                         [0x0D, 0b01011010],
                         [0x0E, 0xF5],
                         [0x0F, 0x20],
                         [0x18, 0b00000001],
                         [0x19, 0b00000000],
                         [0x1A, 0b10001011],
                         [0x1B, 0b01000000],
                         [0x1C, 0b10000000],
                         [0x1D, 0b00000110],
                         [0x1E, 0b00000000],
                         [0x23, 0b00000000],
                         [0x25, 0b01000000],
                         [0x26, 0b00000000],
                         [0x29, 0xFF],
                         [0x2A, 0x00],
                         [0x2B, 0x00],
                         [0x2E, 0b10011000],
                         [0x2F, 0x1E],
                         [0x30, 0xAA],
                         [0x31, 0x55],
                         [0x32, 0xE1],
                         [0x33, 0x00],
                         [0x34, 0x00],
                         [0x35, 0x00],
                         [0x36, 0x00],
                         [0x37, 0b00000000],
                         [0x38, SZE],
                         [0x39, 0x00],
                         [0x3A, 0x00],
                         [0x3B, 0b00000000],
                         [0x3C, 0b10001111],
                         [0x3D, 0b00000010],
                         [0x3E, 0x00],
                         [0x3F, 0x00],
                         [0x40, 0x00],
                         [0x41, 0x00],
                         [0x42, 0x00],
                         [0x43, 0x00],
                         [0x44, 0x00],
                         [0x45, 0x00],
                         [0x46, 0x00],
                         [0x47, 0x00],
                         [0x48, 0x00],
                         [0x49, 0x00],
                         [0x4A, 0x00],
                         [0x4B, 0x00],
                         [0x4C, 0x00],
                         [0x4D, 0x00],
                         [0x4E, 0x01]]
        for item in RegisterValues:
            self.Write(item[0], item[1])
        del RegisterValues
        gc.collect()


    def SetRfMode(self, mode):
        var = self.Read(0x01, 1)[0]
        if mode == STD:
            self.Write(0x01, (var & 0b11100011) | 0b00000100)
        elif mode == RCV:
            self.Write(0x01, (var & 0b11100011) | 0b00010000)
        elif mode == SYN:
            self.Write(0x01, (var & 0b11100011) | 0b00001000)
        elif mode == SLP:
            self.Write(0x01, (var & 0b11100011) | 0b00000000)
        timeOut = 10
        while (self.Read(0x27, 1)[0] & 0b10000000) == 0 and timeOut > 0:
            timeOut -= 1
            time.sleep(.001)
        #if timeout is 0 goto errorhandler
        return 1

    def Read(self, address=0x00, numberOfByte=1):
        self.NSS.low()
        self.SPI.send(address & 0x7F)
        data = self.SPI.recv(numberOfByte)
        self.NSS.high()
        return data

    def Write(self, address=0x00, data=0x00):
        sendDataBuffer = bytearray((address | 0x80, data))
        self.NSS.low()
        self.SPI.send(sendDataBuffer)
        self.NSS.high()

    def Receive(self):
        if self.RFState == STP:
            self.SetRfMode(RCV)
            self.RFState = BSY
        elif self.RFState == RXD:
            for _ in range(6): # FIFO size is 66 byte
                readVal = self.Read(0x00, SZE)
                if readVal[0] != 0x00 or readVal[1] != 0x00 or readVal[2] != 0x00:
                    readVal += self.CheckCRC(readVal)
                    readVal += self.Read(0x24, 1)
                    self.buffer.append(readVal)
                else:
                    break
            self.RFState = BSY

    def CheckCRC(self, data=0x00):
        crc = 0xDB
        for i in range(len(data) - 1):
            crc ^= data[i]

        return  b'\x01' if crc == (data[len(data) - 1]) else b'\x00'

    def IsPayloadReady(self, p):
        self.RFState = RXD
        self.Receive()

    def IsBufferReady(self):
        return len(self.buffer) > 0

    def ReadBuffer(self):
        return self.buffer

    def ClearBuffer(self):
        self.buffer.clear()
        gc.collect()
