import AppContext
import machine
import sys
import select

class Command:
    HELP  = "help"
    RESET = "-r"
    DEBUG = "-d"

def any():
    return select.select([sys.stdin,],[],[],0.0)[0]

def ConsoleCommand():
    if any():
        ExecuteCommand(input())

def ExecuteCommand(command=None):
    if not command:
        return None

    if command == Command.HELP:  #Send all commands
        print("\n\r-->\t{0}\t#Restart system\
               \n\r-->\t{1}\t#Debug mode toggle".format(Command.RESET, Command.DEBUG))
    if command == Command.RESET: #Restart system
        machine.reset()
    if command == Command.DEBUG: #Debug mode toggle
        AppContext.DataBase.DEBUG = not AppContext.DataBase.DEBUG

if __name__ == "__main__":
    while True:
        try:
            ConsoleCommand()
            AppContext.loop()
        except OSError as err:
            print("\n\r[M]-->\tOS error: {0}".format(err))
        except ValueError as err:
            print("\n\r[M]-->\tValueError: {0}".format(err))
        except OverflowError as err:
            print("\n\r[M]-->\tOverflowError: {0}".format(err))
        except:
            print("\n\r[M]-->\tUnexpected Error!!!")
            raise
