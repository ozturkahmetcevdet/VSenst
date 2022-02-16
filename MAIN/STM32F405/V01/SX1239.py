from pyb import Pin, SPI
import time

RF_RECEIVER = 0
RF_SYNTHESIZER = 1
RF_STANDBY = 2
RF_SLEEP = 3

RF_STOP    = 0x01
RF_BUSY    = 0x02
RF_RX_DONE = 0x04
RF_TX_DONE = 0x08
RF_ERROR   = 0x10
RF_TIMEOUT = 0x20
OK         = 0x00
ERROR      = 0x01
RX_TIMEOUT = 0x02
RX_RUNNING = 0x03
TX_TIMEOUT = 0x04
TX_RUNNING = 0x05

class SX1239():
    def __init__(self):
        super().__init__()
        self.RFState = RF_STOP
        self.CenterFrequence = 915000000
        self.SPI = SPI(1, SPI.MASTER, baudrate=600000, polarity=0, phase=0, crc=None)
        self.NRST = Pin('Y6', Pin.OUT_PP)
        self.NSS = Pin('X5', Pin.OUT_PP)
        self.DIO0 = Pin('Y5', Pin.IN, Pin.PULL_UP)
        self.DIO1_DCLK = Pin('X12', Pin.IN, Pin.PULL_UP)
        self.DIO2_DATA = Pin('X11', Pin.IN, Pin.PULL_UP)
        self.Setup()

    def Setup(self):
        self.NRST.high()
        time.sleep(1)
        self.NRST.low()
        self.NSS.high()
        time.sleep(.01)

        #RC CALIBRATION (Once at POR)
        self.SetRfMode(RF_STANDBY)

        self.Write(0x57, 0x80)
        self.Write(0x0A, self.Read(0x0A, 1)[0] | 0x80)
        while (self.Read(0x0A, 1)[0] & 0x40) is 0:
            pass
        self.Write(0x0A, self.Read(0x0A, 1)[0] | 0x80)
        while (self.Read(0x0A, 1)[0] & 0x40) is 0:
            pass
        self.Write(0x57, 0x00)

        self.Write(0x01, 0b10000001) #RegOpMode
        self.Write(0x02, 0b00000000) #RegDataModul
        self.Write(0x03, 0x1A)       #RegBitrateMsb
        self.Write(0x04, 0x0B)       #RegBitrateLsb

        valF = (int)(self.CenterFrequence / 61.03515625)
        self.Write(0x07, (valF >> 16) & 0xFF)       #RegFrfMsb - 915MHz
        self.Write(0x08, (valF >>  8) & 0xFF)       #RegFrfMid - 915MHz
        self.Write(0x09, (valF >>  0) & 0xFF)       #RegFrfLsb - 915MHz

        self.Write(0x0B, 0b00000000) #RegAfcCtrl
        self.Write(0x0D, 0b11110010) #RegListen1
        self.Write(0x0E, 0xF5)       #RegListen2
        self.Write(0x0F, 0x20)       #RegListen3
        self.Write(0x18, 0b00000000) #RegLna
        self.Write(0x19, 0b01000000) #RegRxBw
        self.Write(0x1A, 0b10001011) #RegAfcBw
        self.Write(0x1B, 0b01000000) #RegOokPeak
        self.Write(0x1C, 0b10000000) #RegOokAvg
        self.Write(0x1D, 0b00000110) #RegOokFix
        self.Write(0x1E, 0b00000000) #RegAfcFei
        self.Write(0x23, 0b00000000) #RegRssiConfig
        self.Write(0x25, 0b00000000) #RegDioMapping1
        self.Write(0x26, 0b00000000) #RegDioMapping2
        self.Write(0x29, 228)        #RegRssiThresh - Must be set to (-Sensitivity x 2)
        self.Write(0x2A, 0x00)       #RegRxTimeout1
        self.Write(0x2B, 0x00)       #RegRxTimeout2
        self.Write(0x2E, 0b10011000) #RegSyncConfig
        self.Write(0x2F, 0x69)       #RegSyncValue1
        self.Write(0x30, 0x81)       #RegSyncValue2
        self.Write(0x31, 0x7E)       #RegSyncValue3
        self.Write(0x32, 0x96)       #RegSyncValue4
        self.Write(0x33, 0x00)       #RegSyncValue5
        self.Write(0x34, 0x00)       #RegSyncValue6
        self.Write(0x35, 0x00)       #RegSyncValue7
        self.Write(0x36, 0x00)       #RegSyncValue8
        self.Write(0x37, 0b00000000) #RegPacketConfig1
        self.Write(0x38, 16)        #RegPayloadLength
        self.Write(0x39, 0x00)       #RegNodeAdrs
        self.Write(0x3A, 0x00)       #RegNodeAdrs
        self.Write(0x3B, 0b00000000) #RegAutoModes
        self.Write(0x3C, 0b10001111) #RegFifoThresh
        self.Write(0x3D, 0b00000010) #RegPacketConfig2
        self.Write(0x3E, 0x00)       #RegAesKey1
        self.Write(0x3F, 0x00)       #RegAesKey2
        self.Write(0x40, 0x00)       #RegAesKey3
        self.Write(0x41, 0x00)       #RegAesKey4
        self.Write(0x42, 0x00)       #RegAesKey5
        self.Write(0x43, 0x00)       #RegAesKey6
        self.Write(0x44, 0x00)       #RegAesKey7
        self.Write(0x45, 0x00)       #RegAesKey8
        self.Write(0x46, 0x00)       #RegAesKey9
        self.Write(0x47, 0x00)       #RegAesKey10
        self.Write(0x48, 0x00)       #RegAesKey11
        self.Write(0x49, 0x00)       #RegAesKey12
        self.Write(0x4A, 0x00)       #RegAesKey13
        self.Write(0x4B, 0x00)       #RegAesKey14
        self.Write(0x4C, 0x00)       #RegAesKey15
        self.Write(0x4D, 0x00)       #RegAesKey16
        self.Write(0x4E, 0x01)       #RegTemp1
        
        self.SetRfMode(RF_SLEEP)


    def SetRfMode(self, mode = RF_STANDBY):
        var = self.Read(0x01, 1)[0]
        if mode is RF_STANDBY:
            self.Write(0x01, (var & 0b11100011) | 0b00000100)
        elif mode is RF_RECEIVER:
            self.Write(0x01, (var & 0b11100011) | 0b00010000)
        elif mode is RF_SYNTHESIZER:
            self.Write(0x01, (var & 0b11100011) | 0b00001000)
        elif mode is RF_SLEEP:
            self.Write(0x01, (var & 0b11100011) | 0b00000000)
        while (self.Read(0x27, 1)[0] & 0b10000000) is 0:
            pass
        return 1

    def Read(self, address = 0x00, numberOfByte = 1):
        self.NSS.low()
        self.SPI.send(address & 0x7F) # & 0x7F
        data = self.SPI.recv(numberOfByte)
        self.NSS.high()
        return data

    def Write(self, address = 0x00, data = bytearray(0)):
        sendDataBuffer = bytearray((address | 0x80, data))
        self.NSS.low()
        self.SPI.send(sendDataBuffer)
        self.NSS.high()

    def Receive(self):
        TempRFState = self.RFState
        receivedByteArray = bytearray(16)

        if TempRFState is RF_STOP:
            self.DIO0.irq(trigger=Pin.IRQ_RISING, handler=self.IsPayloadReady)
            self.Write(0x25, 0b01000000)
            self.SetRfMode(RF_RECEIVER)
            #self.Write(0x1E, 0b00000101)
            self.RFState = RF_BUSY
        elif TempRFState is RF_RX_DONE:
            self.SetRfMode(RF_SLEEP)
            receivedByteArray = self.Read(0x00, 16)
            self.RFState = RF_STOP

        return receivedByteArray

    def IsPayloadReady(self, p):
        self.RFState = RF_RX_DONE
        


