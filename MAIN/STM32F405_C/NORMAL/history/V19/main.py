import system
import machine
import sys
import select

def AutoRestart():
    if select.select([sys.stdin,],[],[],0.0)[0]:
        if input() == "restart":
            machine.reset()

if __name__ == "__main__":
    while True:
        AutoRestart()
        try:
            system.loop()
        except OSError as err:
            print("OS error: {0}".format(err))
        except ValueError:
            print("Could not convert data to an integer.")
        except:
            print("Unexpected error!")
            raise
else:
    #sys.exit()
    pass
