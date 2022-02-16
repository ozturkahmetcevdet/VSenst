import gc
from micropython import const
from pyb import Pin, SPI
import time

RF_RECEIVER                     = const(0)
RF_SYNTHESIZER                  = const(1)
RF_STANDBY                      = const(2)
RF_SLEEP                        = const(3)

RF_STOP                         = const(0x01)
RF_BUSY                         = const(0x02)
RF_RX_DONE                      = const(0x04)

RF_CENTER_FREQUENCE             = const(915000000)
RF_COM_FREQUENCE                = const(83330)

RF_COMING_DATA_SIZE             = const(9)


class RF_CONFIG():
    RegisterValues          = [[const(0x01), const(0b10000001)],
                               [const(0x02), const(0b00000000)],
                               [const(0x03), const(((int)(32000000 / RF_COM_FREQUENCE) >> 8) & 0xFF)],
                               [const(0x04), const(((int)(32000000 / RF_COM_FREQUENCE) >> 0) & 0xFF)],
                               [const(0x07), const(((int)(RF_CENTER_FREQUENCE / 61.03515625) >> 16) & 0xFF)],
                               [const(0x08), const(((int)(RF_CENTER_FREQUENCE / 61.03515625) >>  8) & 0xFF)],
                               [const(0x09), const(((int)(RF_CENTER_FREQUENCE / 61.03515625) >>  0) & 0xFF)],
                               [const(0x0B), const(0b00000000)],
                               [const(0x0D), const(0b11110010)],
                               [const(0x0E), const(0xF5)],
                               [const(0x0F), const(0x20)],
                               [const(0x18), const(0b00000001)],
                               [const(0x19), const(0b00000000)],
                               [const(0x1A), const(0b10001011)],
                               [const(0x1B), const(0b01000000)],
                               [const(0x1C), const(0b10000000)],
                               [const(0x1D), const(0b00000110)],
                               [const(0x1E), const(0b00000000)],
                               [const(0x23), const(0b00000000)],
                               [const(0x25), const(0b01000000)],
                               [const(0x26), const(0b00000000)],
                               [const(0x29), const(228)],
                               [const(0x2A), const(0x00)],
                               [const(0x2B), const(0x00)],
                               [const(0x2E), const(0b10011000)],
                               [const(0x2F), const(0x1E)],
                               [const(0x30), const(0xAA)],
                               [const(0x31), const(0x55)],
                               [const(0x32), const(0xE1)],
                               [const(0x33), const(0x00)],
                               [const(0x34), const(0x00)],
                               [const(0x35), const(0x00)],
                               [const(0x36), const(0x00)],
                               [const(0x37), const(0b00000000)],
                               [const(0x38), const(RF_COMING_DATA_SIZE)],
                               [const(0x39), const(0x00)],
                               [const(0x3A), const(0x00)],
                               [const(0x3B), const(0b00000000)],
                               [const(0x3C), const(0b10001111)],
                               [const(0x3D), const(0b00000010)],
                               [const(0x3E), const(0x00)],
                               [const(0x3F), const(0x00)],
                               [const(0x40), const(0x00)],
                               [const(0x41), const(0x00)],
                               [const(0x42), const(0x00)],
                               [const(0x43), const(0x00)],
                               [const(0x44), const(0x00)],
                               [const(0x45), const(0x00)],
                               [const(0x46), const(0x00)],
                               [const(0x47), const(0x00)],
                               [const(0x48), const(0x00)],
                               [const(0x49), const(0x00)],
                               [const(0x4A), const(0x00)],
                               [const(0x4B), const(0x00)],
                               [const(0x4C), const(0x00)],
                               [const(0x4D), const(0x00)],
                               [const(0x4E), const(0x01)]]

class SX1239():
    class Buffer:
        Size = 0
        Value = []

    def __init__(self):
        super().__init__()
        self.RFState = RF_STOP
        self.SPI = SPI(1, SPI.MASTER, baudrate=2400000, polarity=0, phase=0, crc=None)
        self.NRST = Pin('C5', Pin.OUT_PP)
        self.NSS = Pin('A4', Pin.OUT_PP)
        self.DIO0 = Pin('C4', Pin.IN, Pin.PULL_UP)
        self.timeOut = 0
        self.Config = RF_CONFIG()
        self.Setup()

    def Setup(self):
        self.ResetDevice()
        # RC CALIBRATION (Once at POR)
        self.SetRfMode(RF_STANDBY)
        self.StartOscillator()
        self.RegisterConfiguration()
        self.SetRfMode(RF_SLEEP)
        self.DIO0.irq(trigger=Pin.IRQ_RISING, handler=self.IsPayloadReady)
        gc.collect()

    def ResetDevice(self):
        self.NRST.low()
        time.sleep(.01)
        self.NSS.high()

    def StartOscillator(self):
        self.Write(0x57, 0x80)
        self.Write(0x0A, self.Read(0x0A, 1)[0] | 0x80)
        self.timeOut = 10
        while (self.Read(0x0A, 1)[0] & 0x40) == 0 and self.timeOut > 0:
            self.timeOut -= 1
            time.sleep(.001)
        #if timeout is 0 goto errorhandler
        self.Write(0x0A, self.Read(0x0A, 1)[0] | 0x80)
        self.timeOut = 10
        while (self.Read(0x0A, 1)[0] & 0x40) == 0 and self.timeOut > 0:
            self.timeOut -= 1
            time.sleep(.001)
        #if timeout is 0 goto errorhandler
        self.Write(0x57, 0x00)

    def RegisterConfiguration(self):
        for item in self.Config.RegisterValues:
            self.Write(item[0], item[1])
        del RF_CONFIG.RegisterValues
        del self.Config
        gc.collect()


    def SetRfMode(self, mode=RF_STANDBY):
        var = self.Read(0x01, 1)[0]
        if mode == RF_STANDBY:
            self.Write(0x01, (var & 0b11100011) | 0b00000100)
        elif mode == RF_RECEIVER:
            self.Write(0x01, (var & 0b11100011) | 0b00010000)
        elif mode == RF_SYNTHESIZER:
            self.Write(0x01, (var & 0b11100011) | 0b00001000)
        elif mode == RF_SLEEP:
            self.Write(0x01, (var & 0b11100011) | 0b00000000)
        self.timeOut = 10
        while (self.Read(0x27, 1)[0] & 0b10000000) == 0 and self.timeOut > 0:
            self.timeOut -= 1
            time.sleep(.001)
        return 1

    def Read(self, address=0x00, numberOfByte=1):
        self.NSS.low()
        self.SPI.send(address & 0x7F)  # & 0x7F
        data = self.SPI.recv(numberOfByte)
        self.NSS.high()
        return data

    def Write(self, address=0x00, data=bytearray(0)):
        sendDataBuffer = bytearray((address | 0x80, data))
        self.NSS.low()
        self.SPI.send(sendDataBuffer)
        self.NSS.high()

    def Receive(self):
        TempRFState = self.RFState

        if TempRFState == RF_STOP:
            self.SetRfMode(RF_RECEIVER)
            self.RFState = RF_BUSY
        elif TempRFState == RF_RX_DONE:
            for j in range(6): # FIFO size is 66 byte
                readVal = self.Read(j * RF_COMING_DATA_SIZE, RF_COMING_DATA_SIZE)
                if readVal[0] != 0x00 or readVal[1] != 0x00 or readVal[2] != 0x00:
                    if self.CheckCRC(readVal):
                        self.Buffer.Value.append(readVal)
                        self.Buffer.Size += 1
                else:
                    break
            self.RFState = RF_BUSY

    def CheckCRC(self, data=bytearray(RF_COMING_DATA_SIZE)):
        crc = 0xDB
        for i in range(len(data) - 1):
            crc ^= data[i]
        #print("\n\rCRC:{}, C:{}, Status: {}\n\r{}".format(crc, data[len(data) - 1], bool(crc == data[len(data) - 1]), data))

        return bool(crc == data[len(data) - 1])

    def IsPayloadReady(self, p):
        self.RFState = RF_RX_DONE
        self.Receive()

    def IsBufferReady(self):
        return self.Buffer.Size > 0

    def ReadBuffer(self):
        buff = []
        for receiveItems in self.Buffer.Value:
            if receiveItems != bytearray(RF_COMING_DATA_SIZE):
                buff.append(receiveItems)
            else:
                break
        self.Buffer.Value.clear()
        self.Buffer.Size = 0
        gc.collect()
        return buff

    def ClearBuffer(self):
        self.Buffer.Value.clear()
        self.Buffer.Size = 0
