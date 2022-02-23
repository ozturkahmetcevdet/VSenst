import gc
from micropython import const
from PXSensor import PxHub, key, T
import os
import peripheral
import binascii
import ujson as js
from machine import RTC


DEBUG = False

OPEN_SCENE_SHOW_TIME    = const(5000)
CLOSING_TIME            = const(10000)
CLOSE_SCENE_SHOW_TIME   = const(1000)

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
COORDINATEDB_JSON_FILE_NAME     = "jf/COORDINATE_DB.json"
INSTRUCTIONDB_JSON_FILE_NAME    = "jf/INSTRUCTION_DB.json"
LANGUAGEDB_JSON_FILE_NAME       = "jf/LANGUAGE_DB.json"
MENUDB_JSON_FILE_NAME           = "jf/MENU_DB.json"
NOTIFICATIONDB_JSON_FILE_NAME   = "jf/NOTIFICATION_DB.json"

class DataBase(RTC):
    def __init__(self):
        self.HubList                 = []
        self.HubJson                 = {}
        self.HubJsonIsExist          = False
        self.CoordinateJson          = {}
        self.CoordinateJsonIsExist   = False
        self.CoordinateJsonRefresh   = False
        self.InstructionJson         = {}
        self.InstructionJsonIsExist  = False
        self.InstructionJsonRefresh  = False
        self.LanguageJson            = {}
        self.LanguageJsonIsExist     = False
        self.LanguageJsonRefresh     = False
        self.MenuJson                = {}
        self.MenuJsonIsExist         = False
        self.MwnuJsonRefresh         = False
        self.NotificationJson        = {}
        self.NotificationJsonIsExist = False
        self.NotificationJsonRefresh = False
        self.init()
        self.Setup()

    def Setup(self):
        self.CreateAndCheckJsonFiles()
        self.ImportRawDataFromCoordinateJson()
        self.ImportRawDataFromInstructionJson()
        self.ImportRawDataFromHubJson()
            
        self.UnzipRawData()

    def Process(self, fullData=None):
        if fullData != None:
            for data in fullData:
                if self.HubList != []:
                    for item in self.HubList:
                        if item.Process(data=data):
                            self.InstructionJsonRefresh = True
                            break
        
        if self.InstructionJsonRefresh:
            self.InstructionJson['DateTime'] = self.datetime()
            if self.HubList != []:
                self.InstructionJson['Counter'] = sum([item.GetPassangerCount() for item in self.HubList])

        if DEBUG:
            print("\f***RF Data:\t{0}{1}{2}".format(TextColour.BOLD + TextColour.OKCYAN, [binascii.hexlify(d, ',') for d in fullData], TextColour.ENDC))
            print("***Seat Count:\t{0}{1:2}{2}".format(TextColour.BOLD + TextColour.OKCYAN, self.InstructionJson['Counter'], TextColour.ENDC))
            print("***CRC Err:\t{0}{1}{2}\n\r".format(TextColour.BOLD + TextColour.FAIL, sum([crc.features[key.hub.crcErrorCount] for crc in self.HubList]), TextColour.ENDC))
            if self.HubList != []:
                for item in self.HubList:
                    debugLog = ""
                    if item.features[key.hub.px1]:
                        debugLog += "{tc0}{0:2}-{tc1} ID:{id_c1}{1:3}{id_c2}, PxV:{re_c1}{2:5}{re_c2}, PxBV:{rv_c1}{3:5}{rv_c2}, Px Cable:{se_c1}{4}{se_c2}, Seatbelt:{be_c1}{5}{be_c2}, Count:{co_c1}{6:4}{co_c2} --> RF Count:{rf_c1}{7:6}{rf_c2}, RSSI:{rs_c1}{8:4}dBm{rs_c2}, CRCErr:{cc_c1}{9:6}{cc_c2}, Battery:{bt_c1}%{10:3}{bt_c2}"     \
                                    .format(item.features[key.hub.px1][key.px.number], binascii.hexlify(item.features[key.hub.idNumber], '-'), item.features[key.hub.px1][key.px.currentValue], item.features[key.hub.px1][key.px.baseLine], bool(item.features[key.hub.px1][key.px.cableStatus]), bool(item.features[key.hub.px1][key.px.beltStatus]), item.features[key.hub.px1][key.px.seatCount], item.features[key.hub.dataCount], item.features[key.hub.rssi], item.features[key.hub.crcErrorCount], item.features[key.hub.battery]   \
                                    , tc0   = TextColour.BOLD + TextColour.OKCYAN                                                                       , tc1   = TextColour.ENDC                          \
                                    , id_c1 = TextColour.OKBLUE                                                                                         , id_c2 = TextColour.ENDC                          \
                                    , re_c1 = TextColour.OKGREEN if     item.features[key.hub.px1][key.px.seatStatus]           else TextColour.WARNING , re_c2 = TextColour.ENDC                          \
                                    , rv_c1 = TextColour.BOLD + TextColour.OKCYAN                                                                       , rv_c2 = TextColour.ENDC                          \
                                    , se_c1 = TextColour.OKGREEN if     item.features[key.hub.px1][key.px.cableStatus]          else TextColour.FAIL    , se_c2 = TextColour.ENDC                          \
                                    , be_c1 = TextColour.OKGREEN if     item.features[key.hub.px1][key.px.beltStatus]           else TextColour.WARNING , be_c2 = TextColour.ENDC                          \
                                    , co_c1 = TextColour.HEADER                                                                                         , co_c2 = TextColour.ENDC                          \
                                    , rf_c1 = TextColour.OKGREEN if     item.features[key.hub.dataCount] > 0                    else TextColour.FAIL    , rf_c2 = TextColour.ENDC                          \
                                    , rs_c1 = TextColour.HEADER                                                                                         , rs_c2 = TextColour.ENDC                          \
                                    , cc_c1 = TextColour.FAIL                                                                                           , cc_c2 = TextColour.ENDC                          \
                                    , bt_c1 = TextColour.OKGREEN if     item.features[key.hub.battery] > 20                     else TextColour.FAIL    , bt_c2 = TextColour.ENDC)
                    if item.features[key.hub.px2]:
                        debugLog += "\n\r{tc0}{0:2}-{tc1} ID:{id_c1}{1:3}{id_c2}, PxV:{re_c1}{2:5}{re_c2}, PxBV:{rv_c1}{3:5}{rv_c2}, Px Cable:{se_c1}{4}{se_c2}, Seatbelt:{be_c1}{5}{be_c2}, Count:{co_c1}{6:4}{co_c2} --> RF Count:{rf_c1}{7:6}{rf_c2}, RSSI:{rs_c1}{8:4}dBm{rs_c2}, CRCErr:{cc_c1}{9:6}{cc_c2}, Battery:{bt_c1}%{10:3}{bt_c2}"     \
                                    .format(item.features[key.hub.px2][key.px.number], binascii.hexlify(item.features[key.hub.idNumber], '-'), item.features[key.hub.px2][key.px.currentValue], item.features[key.hub.px2][key.px.baseLine], bool(item.features[key.hub.px2][key.px.cableStatus]), bool(item.features[key.hub.px2][key.px.beltStatus]), item.features[key.hub.px2][key.px.seatCount], item.features[key.hub.dataCount], item.features[key.hub.rssi], item.features[key.hub.crcErrorCount], item.features[key.hub.battery]   \
                                    , tc0   = TextColour.BOLD + TextColour.OKCYAN                                                                       , tc1   = TextColour.ENDC                          \
                                    , id_c1 = TextColour.OKBLUE                                                                                         , id_c2 = TextColour.ENDC                          \
                                    , re_c1 = TextColour.OKGREEN if     item.features[key.hub.px2][key.px.seatStatus]           else TextColour.WARNING , re_c2 = TextColour.ENDC                          \
                                    , rv_c1 = TextColour.BOLD + TextColour.OKCYAN                                                                       , rv_c2 = TextColour.ENDC                          \
                                    , se_c1 = TextColour.OKGREEN if     item.features[key.hub.px2][key.px.cableStatus]          else TextColour.FAIL    , se_c2 = TextColour.ENDC                          \
                                    , be_c1 = TextColour.OKGREEN if     item.features[key.hub.px2][key.px.beltStatus]           else TextColour.WARNING , be_c2 = TextColour.ENDC                          \
                                    , co_c1 = TextColour.HEADER                                                                                         , co_c2 = TextColour.ENDC                          \
                                    , rf_c1 = TextColour.OKGREEN if     item.features[key.hub.dataCount] > 0                    else TextColour.FAIL    , rf_c2 = TextColour.ENDC                          \
                                    , rs_c1 = TextColour.HEADER                                                                                         , rs_c2 = TextColour.ENDC                          \
                                    , cc_c1 = TextColour.FAIL                                                                                           , cc_c2 = TextColour.ENDC                          \
                                    , bt_c1 = TextColour.OKGREEN if     item.features[key.hub.battery] > 20                     else TextColour.FAIL    , bt_c2 = TextColour.ENDC)
                    print(debugLog)
                    del debugLog
            else:
                print("{0}{1}{2}".format(TextColour.WARNING, "There is no data available !!", TextColour.ENDC))
            
            print("\n\r{0}".format(self.free()))
        else:
            print("\f***RF Data:\t{0}{1}{2}".format(TextColour.BOLD + TextColour.OKCYAN, [binascii.hexlify(d, ',') for d in fullData], TextColour.ENDC))
            print("***Seat Count:\t{0}{1:2}{2}".format(TextColour.BOLD + TextColour.OKCYAN, self.InstructionJson['Counter'], TextColour.ENDC))
            print("***CRC Err:\t{0}{1}{2}".format(TextColour.BOLD + TextColour.FAIL, sum([crc.features[key.hub.crcErrorCount] for crc in self.HubList]), TextColour.ENDC))
            print("*Warning:\tDebug mode is OFF\n\r*Execute:\tUse [-d] command to toggle Debug mode.\n\r*MEMUsage:\t{0}\n\r*Time:\t\t{1}".format(self.free(), self.datetime()))
            #pass
        return None

    def CreateAndCheckJsonFiles(self):
        try:
            open(HUBDB_JSON_FILE_NAME, 'r')
            self.HubJsonIsExist = True
        except OSError as err:
            print("OS error: {0}".format(err))
        except ValueError:
            print("Could not open file. ---{}".format(HUBDB_JSON_FILE_NAME))
        except:
            print("Unexpected error!")
            raise
        
        try:
            open(COORDINATEDB_JSON_FILE_NAME, 'r')
            self.CoordinateJsonIsExist = True
        except OSError as err:
            print("OS error: {0}".format(err))
        except ValueError:
            print("Could not open file. ---{}".format(COORDINATEDB_JSON_FILE_NAME))
        except:
            print("Unexpected error!")
            raise
        
        try:
            open(INSTRUCTIONDB_JSON_FILE_NAME, 'r')
            self.InstructionJsonIsExist = True
        except OSError as err:
            print("OS error: {0}".format(err))
        except ValueError:
            print("Could not open file. ---{}".format(INSTRUCTIONDB_JSON_FILE_NAME))
        except:
            print("Unexpected error!")
            raise
        
        try:
            open(LANGUAGEDB_JSON_FILE_NAME, 'r')
            self.LanguageJsonIsExist = True
        except OSError as err:
            print("OS error: {0}".format(err))
        except ValueError:
            print("Could not open file. ---{}".format(LANGUAGEDB_JSON_FILE_NAME))
        except:
            print("Unexpected error!")
            raise
        
        try:
            open(MENUDB_JSON_FILE_NAME, 'r')
            self.MenuJsonIsExist = True
        except OSError as err:
            print("OS error: {0}".format(err))
        except ValueError:
            print("Could not open file. ---{}".format(MENUDB_JSON_FILE_NAME))
        except:
            print("Unexpected error!")
            raise
        
        try:
            open(NOTIFICATIONDB_JSON_FILE_NAME, 'r')
            self.NotificationJsonIsExist = True
        except OSError as err:
            print("OS error: {0}".format(err))
        except ValueError:
            print("Could not open file. ---{}".format(NOTIFICATIONDB_JSON_FILE_NAME))
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
                js.dump(self.HubJson, jf, separators=(',', ':'))
            jf.close()
        self.ClearUnnecessaryFiles()

    def ImportRawDataFromCoordinateJson(self):
        if self.CoordinateJsonIsExist :
            try:
                with open(COORDINATEDB_JSON_FILE_NAME, 'r') as jf:
                    self.CoordinateJson = js.load(jf)
                jf.close()
            except OSError as err:
                print("OS error: {0}".format(err))
            except ValueError:
                print("Could not read file. ---{}".format(COORDINATEDB_JSON_FILE_NAME))
            except:
                print("Unexpected error!")
                raise

    def ImportRawDataFromInstructionJson(self):
        if self.InstructionJsonIsExist :
            try:
                with open(INSTRUCTIONDB_JSON_FILE_NAME, 'r') as jf:
                    self.InstructionJson = js.load(jf)
                jf.close()
            except OSError as err:
                print("OS error: {0}".format(err))
            except ValueError:
                print("Could not read file. ---{}".format(INSTRUCTIONDB_JSON_FILE_NAME))
            except:
                print("Unexpected error!")
                raise

    def ImportRawDataFromHubJson(self):
        if self.HubJsonIsExist:
            try:
                with open(HUBDB_JSON_FILE_NAME, 'r') as jf:
                    self.HubJson = js.load(jf)
                jf.close()
            except OSError as err:
                print("OS error: {0}".format(err))
            except ValueError:
                print("Could not read file. ---{}".format(HUBDB_JSON_FILE_NAME))
            except:
                print("Unexpected error!")
                raise

    def GetCoordinateJsonAsString(self):
        return js.dumps(self.CoordinateJson, separators=(',', ':'))

    def GetInstructionJsonAsString(self):
        return js.dumps(self.InstructionJson, separators=(',', ':'))

    def UnzipRawData(self):
        if self.HubJson != {}:
            self.HubList = []
            for key in self.HubJson:
                self.CreateHubObject(json=self.HubJson[key])
        self.InstructionJsonRefresh = True
        self.ClearUnnecessaryFiles()

    def DefineHubObject(self, fullData=None):
        if fullData != None:
            sNo = -1
            for data in fullData:
                if bool(data[20] & 0x01):
                    checkFlag = not (bool((data[2] >> 0) & 0x01) or bool((data[2] >> 1) & 0x01))
                    if self.HubList != []:
                        for item in self.HubList:
                            if item.features[key.hub.idNumber] == data[:2]:
                                item.Process(data=data)
                                checkFlag = True
                            if item.features[key.hub.px1]:
                                sNo = item.features[key.hub.px1][key.px.number] if sNo < item.features[key.hub.px1][key.px.number] else sNo
                            if item.features[key.hub.px2]:
                                sNo = item.features[key.hub.px2][key.px.number] if sNo < item.features[key.hub.px2][key.px.number] else sNo
                    if checkFlag is False:
                        self.InstructionJsonRefresh = True
                        if int((data[9] << 8) | data[10]) > T.D or int((data[17] << 8) | data[18]) > T.D:
                            self.CreateHubObject(data=data, sNo=sNo+1)

    def CreateHubObject(self, json=dict(), data=None, sNo=0):
        if json != dict():
            self.HubList.append(PxHub(json=json, dateTime=self.datetime()))
        elif data != None:
            #for _ in range(40):
            self.HubList.append(PxHub(data=data, sNo=sNo, dateTime=self.datetime()))
        
        if self.InstructionJson != {}:
            hubCounter = 0
            for item in self.HubList:
                self.InstructionJson['PxHubs'][hubCounter] = item.features
                hubCounter += 1
        peripheral.buzzerObject(replay=1, onTime=25)
        
    def ClearUnnecessaryFiles(self):
        self.HubJson = {}
        gc.collect()

    def ClearAllData(self):
        for item in self.HubList:
            del item
        self.HubList = []
        self.InstructionJson['PxHubs'] = {}
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
