from pyb import Pin, SPI
import time


class SX1239():
    def __init__(self):
        super().__init__()
        self.SPI = SPI(1, SPI.MASTER, baudrate=600000, polarity=0, phase=0, crc=None)
        self.NRST = Pin('Y6', Pin.OUT_PP)
        self.NSS = Pin('X5', Pin.OUT_PP)
        self.DIO0 = Pin('Y5', Pin.IN, Pin.PULL_UP)
        self.DIO1_DCLK = Pin('X12', Pin.IN, Pin.PULL_UP)
        self.DIO2_DATA = Pin('X11', Pin.IN, Pin.PULL_UP)
        self.Setup()

    def Setup(self):
        self.NRST.low()
        time.sleep(.005)
        self.NSS.high()
        time.sleep(.01)
        time.sleep(.01)
        self.Write(0x01, 0b00010000) #RegOpMode - SX1239_SEQUENCER_AUTO + SX1239_LISTEN_DIS + SX1239_MODE_RX
        self.Write(0x02, 0b00000000) #RegDataModul - SX1239_DATAMODE_CONTINUOUS_NO_SYNC + SX1239_MODULATION_FSK
        self.Write(0x03, 0x0D)       #RegBitrateMsb
        self.Write(0x04, 0x05)       #RegBitrateLsb
        #self.Write(0x07, 0xE5)       #RegFrfMsb - 916MHz
        #self.Write(0x08, 0x21)       #RegFrfMid - 916MHz
        #self.Write(0x09, 0xC9)       #RegFrfLsb - 916MHz
        #self.Write(0x07, 0xD9)       #RegFrfMsb - 868.3Hz
        #self.Write(0x08, 0x33)       #RegFrfMid - 868.3Hz
        #self.Write(0x09, 0x3A)       #RegFrfLsb - 868.3Hz
        #self.Write(0x0D, 0b10010001) #RegListen1
        self.Write(0x18, 0b00001001) #RegLna
        self.Write(0x19, 0b01010011) #RegRxBw - SX1239_BW_DCCFREQ_DEFAULT + SX1239_BW_MANT_24 + SX1239_BW_EXP_0
        #self.Write(0x1B, 0b10000000) #RegOokPeak - SX1239_THRESH_PEAK_TYPE_AVERAGE + SX1239_THRESH_PEAK_STEP_05dB + SX1239_THRESH_PEAK_DEC_0
        self.Write(0x29, 0xB0)       #RegRssiThresh - SX1239_RSSITHRESH_DEFAULT
        self.Write(0x2E, 0b10011000) #RegSyncConfig - SX1239_SYNC_DIS
        self.Write(0x2F, 0x69) #RegSyncValue1 - 
        self.Write(0x30, 0x81) #RegSyncValue2 - 
        self.Write(0x31, 0x7E) #RegSyncValue3 - 
        self.Write(0x32, 0x96) #RegSyncValue4 - 
        self.Write(0x37, 0b10000010) #RegPacketConfig1 - 
        self.Write(0x38, 24)         #RegPayloadLength - 
        self.Write(0x39, 0x64) #RegNodeAdrs - 
        self.Write(0x3A, 0x64) #RegNodeAdrs - 
        self.Write(0x3B, 0b00100010) #RegAutoModes - 
        self.Write(0x58, 0x2D)       #RegTestLna - 


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
