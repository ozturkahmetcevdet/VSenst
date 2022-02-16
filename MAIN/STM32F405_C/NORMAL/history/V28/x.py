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

class RF_CONFIG:
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
                               [const(0x25), const(0b00000000)],
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
                               [const(0x38), const(10)],
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