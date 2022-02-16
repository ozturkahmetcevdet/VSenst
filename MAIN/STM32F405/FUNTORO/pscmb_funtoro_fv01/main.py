import system
import machine
import sys

if __name__ == "__main__":
    while True:
        try:
            system.loop()
        except:
            machine.reset()
else:
    sys.exit()
