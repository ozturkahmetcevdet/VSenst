import system
import machine
import sys
import system
import userControl


if __name__ == "__main__":
    while True:
        try:
            #userControl.REDLed(True)
            system.loop()
            #userControl.REDLed(False)
        except:
            #machine.reset()
            pass
else:
    #sys.exit()
    pass
