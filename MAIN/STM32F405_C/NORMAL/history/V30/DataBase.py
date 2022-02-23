import gc
from micropython import const
from SX1239 import RF_COMING_DATA_SIZE
from PXSensor import PxHub, key
import os
import peripheral
import binascii
import json


CONSOLE_DEBUG_TOOL      = False

OPEN_SCENE_SHOW_TIME    = const(1000)
CLOSING_TIME            = const(10000)
CLOSE_SCENE_SHOW_TIME   = const(1000)

RF_DATA_SIZE            = RF_COMING_DATA_SIZE
RTC_NOW                 = 0

class TextColour:
    HEADER      = '\033[95m'
    OKBLUE      = '\033[94m'
    OKCYAN      = '\033[96m'
    OKGREEN     = '\033[92m'
    WARNING     = '\033[93m'
    FAIL        = '\033[91m'
    ENDC        = '\033[0m'
    BOLD        = '\033[1m'
    UNDERLINE   = '\033[4m'

HUBDB_JSON_FILE_NAME            = "HUB_DB.json"
COORDB_JSON_FILE_NAME           = "COOR_DB.json"
INSTRUCTIONDB_JSON_FILE_NAME    = "INSTRUCTION_DB.json"

class DataBase():
    def __init__(self):
        self.HubList = []
        self.HubJson = {}
        self.CoorJson = {}
        self.InstructionJson = {}
        self.IsHubJsonFileExist = False
        self.IsCoorJsonFileExist = False
        self.IsInstructionJsonFileExist = False
        self.Setup()

    def Setup(self):
        self.CreateAndCheckJsonFiles()
        self.ImportRawDataFromInstructionJson()
        self.ImportRawDataFromHubJson()
        self.ImportRawDataFromCoorJson()
            
        self.UnzipRawData()
        
    def RefreshData(self, control=None, data=None, flag=False):
        answer = (control != data) or flag
        return answer, data

    def Process(self, fullData=bytearray(RF_COMING_DATA_SIZE)):
        if self.HubJson != {} or self.CoorJson != {}:
            self.ClearUnnecessaryFiles()

        if fullData != bytearray(RF_COMING_DATA_SIZE):
            for data in fullData:
                if self.HubList != []:
                    for item in self.HubList:
                        if item.Process(data=data, dateTime=RTC_NOW):
                            self.InstructionJson['Refresh'] = True
                            break

        if CONSOLE_DEBUG_TOOL:
            print("\f")
            if self.HubList != []:                
                for item in self.HubList:
                    debugLog = ""
                    if item.features[key.hub.px1]:
                        debugLog += "{tc0}{0:2}-{tc1} ID:{id_c1}{1:3}{id_c2}, Px Value:{re_c1}{2:5}{re_c2}, Px Cable:{se_c1}{3}{se_c2}, Seatbelt:{be_c1}{4}{be_c2}, Calibration:{ca_c1}{5}{ca_c2}, Count:{co_c1}{6:4}{co_c2} --> RF Count:{rf_c1}{7:6}{rf_c2}, Battery:{bt_c1}%{8:3}{bt_c2}"     \
                                    .format(item.features[key.hub.px1][key.px.number], binascii.hexlify(item.features[key.hub.idNumber]), item.features[key.hub.px1][key.px.currentValue], bool(item.features[key.hub.px1][key.px.cableStatus]), bool(item.features[key.hub.px1][key.px.beltStatus]), bool(not item.features[key.hub.px1][key.px.calibrationStatus]), item.features[key.hub.px1][key.px.seatCount], item.features[key.hub.dataCount], item.features[key.hub.battery]   \
                                                        , tc0   = TextColour.BOLD + TextColour.OKCYAN                                                                       , tc1   = TextColour.ENDC                          \
                                                        , id_c1 = TextColour.OKBLUE                                                                                         , id_c2 = TextColour.ENDC                          \
                                                        , re_c1 = TextColour.OKGREEN if     item.features[key.hub.px1][key.px.seatStatus]           else TextColour.WARNING , re_c2 = TextColour.ENDC                          \
                                                        , se_c1 = TextColour.OKGREEN if     item.features[key.hub.px1][key.px.cableStatus]          else TextColour.FAIL    , se_c2 = TextColour.ENDC                          \
                                                        , be_c1 = TextColour.OKGREEN if     item.features[key.hub.px1][key.px.beltStatus]           else TextColour.WARNING , be_c2 = TextColour.ENDC                          \
                                                        , ca_c1 = TextColour.OKGREEN if not item.features[key.hub.px1][key.px.calibrationStatus]    else TextColour.FAIL    , ca_c2 = TextColour.ENDC                          \
                                                        , co_c1 = TextColour.HEADER                                                                                         , co_c2 = TextColour.ENDC                          \
                                                        , rf_c1 = TextColour.OKGREEN if     item.features[key.hub.dataCount] > 0                    else TextColour.FAIL    , rf_c2 = TextColour.ENDC                          \
                                                        , bt_c1 = TextColour.OKGREEN if     item.features[key.hub.battery] > 20                     else TextColour.FAIL    , bt_c2 = TextColour.ENDC)
                    if item.features[key.hub.px2]:
                        debugLog += "\n\r{tc0}{0:2}-{tc1} ID:{id_c1}{1:3}{id_c2}, Px Value:{re_c1}{2:5}{re_c2}, Px Cable:{se_c1}{3}{se_c2}, Seatbelt:{be_c1}{4}{be_c2}, Calibration:{ca_c1}{5}{ca_c2}, Count:{co_c1}{6:4}{co_c2} --> RF Count:{rf_c1}{7:6}{rf_c2}, Battery:{bt_c1}%{8:3}{bt_c2}"     \
                                    .format(item.features[key.hub.px2][key.px.number], binascii.hexlify(item.features[key.hub.idNumber]), item.features[key.hub.px2][key.px.currentValue], bool(item.features[key.hub.px2][key.px.cableStatus]), bool(item.features[key.hub.px2][key.px.beltStatus]), bool(not item.features[key.hub.px2][key.px.calibrationStatus]), item.features[key.hub.px2][key.px.seatCount], item.features[key.hub.dataCount], item.features[key.hub.battery]   \
                                                        , tc0   = TextColour.BOLD + TextColour.OKCYAN                                                                       , tc1   = TextColour.ENDC                          \
                                                        , id_c1 = TextColour.OKBLUE                                                                                         , id_c2 = TextColour.ENDC                          \
                                                        , re_c1 = TextColour.OKGREEN if     item.features[key.hub.px2][key.px.seatStatus]           else TextColour.WARNING , re_c2 = TextColour.ENDC                          \
                                                        , se_c1 = TextColour.OKGREEN if     item.features[key.hub.px2][key.px.cableStatus]          else TextColour.FAIL    , se_c2 = TextColour.ENDC                          \
                                                        , be_c1 = TextColour.OKGREEN if     item.features[key.hub.px2][key.px.beltStatus]           else TextColour.WARNING , be_c2 = TextColour.ENDC                          \
                                                        , ca_c1 = TextColour.OKGREEN if not item.features[key.hub.px2][key.px.calibrationStatus]    else TextColour.FAIL    , ca_c2 = TextColour.ENDC                          \
                                                        , co_c1 = TextColour.HEADER                                                                                         , co_c2 = TextColour.ENDC                          \
                                                        , rf_c1 = TextColour.OKGREEN if     item.features[key.hub.dataCount] > 0                    else TextColour.FAIL    , rf_c2 = TextColour.ENDC                          \
                                                        , bt_c1 = TextColour.OKGREEN if     item.features[key.hub.battery] > 20                     else TextColour.FAIL    , bt_c2 = TextColour.ENDC)
                    print(debugLog)
            else:
                print("{0}{1}{2}".format(TextColour.WARNING, "There is no data available !!", TextColour.ENDC))
            
            print("\n\r{0}".format(self.free()))
        else:
            print("\f*Warning:\tDebug mode is OFF\n\r*Execute:\tUse [-d] command to toggle Debug mode.\n\r*MEMUsage:\t{0}".format(self.free()))
        return None

    def CreateAndCheckJsonFiles(self):
        try:
            open(HUBDB_JSON_FILE_NAME, 'r')
            self.IsHubJsonFileExist = True
        except OSError as err:
            print("OS error: {0}".format(err))
        except ValueError:
            print("Could not open file. ---{}".format(HUBDB_JSON_FILE_NAME))
        except:
            print("Unexpected error!")
            raise
        
        try:
            open(COORDB_JSON_FILE_NAME, 'r')
            self.IsCoorJsonFileExist = True
        except OSError as err:
            print("OS error: {0}".format(err))
        except ValueError:
            print("Could not open file. ---{}".format(COORDB_JSON_FILE_NAME))
        except:
            print("Unexpected error!")
            raise
        
        try:
            open(INSTRUCTIONDB_JSON_FILE_NAME, 'r')
            self.IsInstructionJsonFileExist = True
        except OSError as err:
            print("OS error: {0}".format(err))
        except ValueError:
            print("Could not open file. ---{}".format(INSTRUCTIONDB_JSON_FILE_NAME))
        except:
            print("Unexpected error!")
            raise

    def FlushRawDataToJson(self):
        self.HubJson = {}
        hubCounter = 0
        if self.HubList != []:
            for hub in self.HubList:
                self.HubJson[hubCounter] = hub.features
                hubCounter +=1
            with open(HUBDB_JSON_FILE_NAME, 'w') as jf:
                json.dump(self.HubJson, jf)
            jf.close()

    def ImportRawDataFromInstructionJson(self):
        if self.IsInstructionJsonFileExist:
            try:
                with open(INSTRUCTIONDB_JSON_FILE_NAME, 'r') as jf:
                    self.InstructionJson = json.load(jf)
                jf.close()
            except OSError as err:
                print("OS error: {0}".format(err))
            except ValueError:
                print("Could not read file. ---{}".format(INSTRUCTIONDB_JSON_FILE_NAME))
            except:
                print("Unexpected error!")
                raise

    def ImportRawDataFromHubJson(self):
        if self.IsHubJsonFileExist:
            try:
                with open(HUBDB_JSON_FILE_NAME, 'r') as jf:
                    self.HubJson = json.load(jf)
                jf.close()
            except OSError as err:
                print("OS error: {0}".format(err))
            except ValueError:
                print("Could not read file. ---{}".format(HUBDB_JSON_FILE_NAME))
            except:
                print("Unexpected error!")
                raise

    def ImportRawDataFromCoorJson(self):
        if self.IsCoorJsonFileExist:
            try:
                with open(COORDB_JSON_FILE_NAME, 'r') as jf:
                    self.CoorJson = json.load(jf)
                jf.close()
                del jf
            except OSError as err:
                print("OS error: {0}".format(err))
            except ValueError:
                print("Could not read file. ---{}".format(COORDB_JSON_FILE_NAME))
            except:
                print("Unexpected error!")
                raise

    def UnzipRawData(self):
        if self.HubJson != {}:
            self.HubList = []
            for key in self.HubJson:
                self.CreateHubObject(json=self.HubJson[key])
        if self.InstructionJson != {} and self.CoorJson != {}:
            self.InstructionJson['Coordinates'] = self.CoorJson
        self.InstructionJson['Refresh'] = True
        self.ClearUnnecessaryFiles()

    def DefineCoorJson(self, CoorJson=str):
        self.CoorJson = json.loads(CoorJson)
        with open(COORDB_JSON_FILE_NAME, 'w') as jf:
            json.dump(self.CoorJson)
        jf.close()
        self.ClearUnnecessaryFiles()

    def DefineHubObject(self, fullData=list(bytearray(RF_COMING_DATA_SIZE))):
        lastSeatNumber = -1
        for data in fullData:
            checkFlag = not (bool((data[3] >> 0) & 0x01) or bool((data[3] >> 1) & 0x01))
            if self.HubList != []:
                for item in self.HubList:
                    if item.features[key.hub.idNumber] == data[:3]:
                        checkFlag = True
                    if item.features[key.hub.px1]:
                        lastSeatNumber = item.features[key.hub.px1][key.px.number] if lastSeatNumber < item.features[key.hub.px1][key.px.number] else lastSeatNumber
                    if item.features[key.hub.px2]:
                        lastSeatNumber = item.features[key.hub.px2][key.px.number] if lastSeatNumber < item.features[key.hub.px2][key.px.number] else lastSeatNumber
            if checkFlag is False:
                self.CreateHubObject(data=data, lastSeatNumber=lastSeatNumber+1)
                self.InstructionJson['Refresh'] = True

    def CreateHubObject(self, json=dict(), data=bytearray(RF_COMING_DATA_SIZE), lastSeatNumber=0):
        if json != dict():
            self.HubList.append(PxHub(json=json, dateTime=RTC_NOW))
        elif data != bytearray(RF_COMING_DATA_SIZE):
            for i in range(40):
                self.HubList.append(PxHub(data=data, lastSeatNumber=lastSeatNumber, dateTime=RTC_NOW))
        
        if self.InstructionJson != {}:
            hubCounter = 0
            for item in self.HubList:
                self.InstructionJson['PxHubs'][hubCounter] = item.features
                hubCounter += 1
        peripheral.buzzerObject(replay=1, onTime=25)
        
    def ClearUnnecessaryFiles(self):
        self.HubJson = {}
        self.CoorJson = {}
        self.IsHubJsonFileExist = False
        gc.collect()

    def ClearAllData(self):
        for item in self.HubList:
            del item
        self.HubList = []
        self.ClearUnnecessaryFiles()
        self.RemoveFile(HUBDB_JSON_FILE_NAME)
        gc.collect()

    def RemoveFile(self, fileName=None):
        if fileName:
            try:
                os.remove(fileName)
            except OSError as err:
                print("OS error: {0}".format(err))
            except ValueError:
                print("Could not remove file. ---{}".format(fileName))
            except:
                print("Unexpected error!")
                raise

    def free(self):
        gc.collect()
        F = gc.mem_free()
        A = gc.mem_alloc()
        T = F+A
        P = '{0:.2f}%'.format(F/T*100)
        return ('[RAM] -> Total:{0} Free:{1} ({2})'.format(T,F,P))
