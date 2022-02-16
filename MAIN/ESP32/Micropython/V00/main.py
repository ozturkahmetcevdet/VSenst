
from network import STA_IF, WLAN
from machine import idle
import sys

#open json file from global settings to ctrl+shift+g

#print(sys.path)
#sys.path.append('/ili9341')
#print(sys.path)

wlan = WLAN(STA_IF)
wlan.active(True)


if __name__ == "__main__":
    while True:
        try:
            nets = wlan.scan()
            for net in nets:
                ssid = net[0]
                if ssid == b'AhmetsPhone':
                    wlan.connect(ssid, 'ahmet123')
                    while not wlan.isconnected():
                        idle()
                    print('WLAN connection succeeded!')
                    import pwn_search
                    break
        except:
            print("\n\r[M]-->\tUnexpected Error!!!")
            raise
