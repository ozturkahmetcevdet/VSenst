import system
import machine
import sys
import select


def ConsoleCommand():
    if select.select([sys.stdin,],[],[],0.0)[0]:
        ExecuteCommand(input())

def ExecuteCommand(command=None):
    if not command:
        return None

    if command == "restart":
        machine.reset()
    if command == "debug-on":
        system.register.CONSOLE_DEBUG_TOOL = True
    if command == "debug-off":
        system.register.CONSOLE_DEBUG_TOOL = False

if __name__ == "__main__":
    while True:
        ConsoleCommand()
        try:
            system.loop()
        except OSError as err:
            print("OS error: {0}".format(err))
        except ValueError:
            print("Main Loop Error.")
        except:
            print("Unexpected error!")
            raise
