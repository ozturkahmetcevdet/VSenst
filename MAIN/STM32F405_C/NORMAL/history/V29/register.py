import gc
from micropython import const
from SX1239 import RF_COMING_DATA_SIZE
from PXSensor import PxHub
import os
import peripheral
import binascii
import json

CONSOLE_DEBUG_TOOL      = True

OPEN_SCENE_SHOW_TIME    = const(1000)
CLOSING_TIME            = const(10000)
CLOSE_SCENE_SHOW_TIME   = const(1000)
MAX_SEAT_NUMBER         = const(33)

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

HUBDB_JSON_FILE_NAME    = "HUB_DB.json"
COORDB_JSON_FILE_NAME   = "COOR_DB.json"

class DataBase():
    def __init__(self):
        self.HubList = []
        self.HubFeatures = {}
        self.coorJson = {}
        self.IsHubJsonFileExist = False
        self.IsCoorJsonFileExist = False
        self.Setup()

    def Setup(self):
        self.CreateAndCheckJsonFiles()
        self.ImportRawDataFromHubJson()
        self.ImportRawDataFromCoorJson()
            
        self.UnzipRawData()

    def Process(self, fullData=bytearray(RF_COMING_DATA_SIZE)):
        if self.HubFeatures != {} or self.coorJson != {}:
            self.ClearUnnecessaryFiles()

        if fullData != bytearray(RF_COMING_DATA_SIZE):
            for data in fullData:
                if self.HubList != []:
                    for item in self.HubList:
                        if item.Process(data=data, dateTime=RTC_NOW):
                            break

        if CONSOLE_DEBUG_TOOL:
            debugLog = "\f"
            if self.HubList != []:                
                for item in self.HubList:
                    if item.features['proxS1']:
                        debugLog += "{tc0}{0:2}-{tc1} ID:{id_c1}{1:3}{id_c2}, Px Value:{re_c1}{2:5}{re_c2}, Px Cable:{se_c1}{3}{se_c2}, Seatbelt:{be_c1}{4}{be_c2}, Calibration:{ca_c1}{5}{ca_c2}, Count:{co_c1}{6:4}{co_c2} --> RF Count:{rf_c1}{7:6}{rf_c2}, Battery:{bt_c1}%{8:3}{bt_c2}\n\r"     \
                                    .format(item.features['proxS1']['number'], binascii.hexlify(item.features['pHubID']), item.features['proxS1']['pCuVal'], bool(item.features['proxS1']['cablSt']), bool(item.features['proxS1']['beltSt']), bool(not item.features['proxS1']['calbSt']), item.features['proxS1']['seatCo'], item.features['dataCo'], item.features['batLvl']   \
                                                        , tc0   = TextColour.BOLD + TextColour.OKCYAN                                                   , tc1   = TextColour.ENDC                          \
                                                        , id_c1 = TextColour.OKBLUE                                                                     , id_c2 = TextColour.ENDC                          \
                                                        , re_c1 = TextColour.OKGREEN if     item.features['proxS1']['seatSt']   else TextColour.WARNING , re_c2 = TextColour.ENDC                          \
                                                        , se_c1 = TextColour.OKGREEN if     item.features['proxS1']['cablSt']   else TextColour.FAIL    , se_c2 = TextColour.ENDC                          \
                                                        , be_c1 = TextColour.OKGREEN if     item.features['proxS1']['beltSt']   else TextColour.WARNING , be_c2 = TextColour.ENDC                          \
                                                        , ca_c1 = TextColour.OKGREEN if not item.features['proxS1']['calbSt']   else TextColour.FAIL    , ca_c2 = TextColour.ENDC                          \
                                                        , co_c1 = TextColour.HEADER                                                                     , co_c2 = TextColour.ENDC                          \
                                                        , rf_c1 = TextColour.OKGREEN if     item.features['dataCo'] > 0         else TextColour.FAIL    , rf_c2 = TextColour.ENDC                          \
                                                        , bt_c1 = TextColour.OKGREEN if     item.features['batLvl'] > 20        else TextColour.FAIL    , bt_c2 = TextColour.ENDC)
                    if item.features['proxS2']:
                        debugLog += "{tc0}{0:2}-{tc1} ID:{id_c1}{1:3}{id_c2}, Px Value:{re_c1}{2:5}{re_c2}, Px Cable:{se_c1}{3}{se_c2}, Seatbelt:{be_c1}{4}{be_c2}, Calibration:{ca_c1}{5}{ca_c2}, Count:{co_c1}{6:4}{co_c2} --> RF Count:{rf_c1}{7:6}{rf_c2}, Battery:{bt_c1}%{8:3}{bt_c2}\n\r"     \
                                    .format(item.features['proxS2']['number'], binascii.hexlify(item.features['pHubID']), item.features['proxS2']['pCuVal'], bool(item.features['proxS2']['cablSt']), bool(item.features['proxS2']['beltSt']), bool(not item.features['proxS2']['calbSt']), item.features['proxS2']['seatCo'], item.features['dataCo'], item.features['batLvl']   \
                                                        , tc0   = TextColour.BOLD + TextColour.OKCYAN                                                   , tc1   = TextColour.ENDC                          \
                                                        , id_c1 = TextColour.OKBLUE                                                                     , id_c2 = TextColour.ENDC                          \
                                                        , re_c1 = TextColour.OKGREEN if     item.features['proxS2']['seatSt']   else TextColour.WARNING , re_c2 = TextColour.ENDC                          \
                                                        , se_c1 = TextColour.OKGREEN if     item.features['proxS2']['cablSt']   else TextColour.FAIL    , se_c2 = TextColour.ENDC                          \
                                                        , be_c1 = TextColour.OKGREEN if     item.features['proxS2']['beltSt']   else TextColour.WARNING , be_c2 = TextColour.ENDC                          \
                                                        , ca_c1 = TextColour.OKGREEN if not item.features['proxS2']['calbSt']   else TextColour.FAIL    , ca_c2 = TextColour.ENDC                          \
                                                        , co_c1 = TextColour.HEADER                                                                     , co_c2 = TextColour.ENDC                          \
                                                        , rf_c1 = TextColour.OKGREEN if     item.features['dataCo'] > 0         else TextColour.FAIL    , rf_c2 = TextColour.ENDC                          \
                                                        , bt_c1 = TextColour.OKGREEN if     item.features['batLvl'] > 20        else TextColour.FAIL    , bt_c2 = TextColour.ENDC)
            else:
                debugLog += TextColour.WARNING + "There is no data available !!" + TextColour.ENDC
            
            debugLog += self.free()
            print(debugLog)
        else:
            print(self.free())
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

    def FlushRawDataToJson(self):
        self.HubFeatures = {}
        hubCounter = 0
        if self.HubList != []:
            for hub in self.HubList:
                self.HubFeatures[hubCounter] = hub.features
                hubCounter +=1
            with open(HUBDB_JSON_FILE_NAME, 'w') as jf:
                json.dump(self.HubFeatures, jf)
            jf.close()

    def ImportRawDataFromHubJson(self):
        if self.IsHubJsonFileExist:
            try:
                with open(HUBDB_JSON_FILE_NAME, 'r') as jf:
                    self.HubFeatures = json.load(jf)
                jf.close()
                del jf
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
                    self.coorJson = json.load(jf)
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
        if self.HubFeatures != {}:
            self.HubList = []

            for key in self.HubFeatures:
                self.CreateHubObject(json=self.HubFeatures[key], coorJson=self.coorJson)

        self.ClearUnnecessaryFiles()

    def DefineCoorJson(self, coorJson=str):
        self.coorJson = json.loads(coorJson)
        with open(COORDB_JSON_FILE_NAME, 'w') as jf:
            json.dump(self.coorJson)
        jf.close()
        self.UpdateHubObject()
        self.ClearUnnecessaryFiles()
        
    def UpdateHubObject(self):
        if self.coorJson == {}:
            self.ImportRawDataFromCoorJson()

        if self.HubList != []:
            if self.coorJson != {}:
                for key, item in self.coorJson.items():
                    if self.HubList[key].features['proxS1']:
                        self.HubList[key].features['proxS1']['coordX'] = item['proxS1']['coordX']
                        self.HubList[key].features['proxS1']['coordY'] = item['proxS1']['coordY']
                        self.HubList[key].features['proxS1']['width_'] = item['proxS1']['width_']
                        self.HubList[key].features['proxS1']['height'] = item['proxS1']['height']
                    if self.HubList[key].features['proxS2']:
                        self.HubList[key].features['proxS2']['coordX'] = item['proxS2']['coordX']
                        self.HubList[key].features['proxS2']['coordY'] = item['proxS2']['coordY']
                        self.HubList[key].features['proxS2']['width_'] = item['proxS2']['width_']
                        self.HubList[key].features['proxS2']['height'] = item['proxS2']['height']

    def DefineHubObject(self, fullData=list(bytearray(RF_COMING_DATA_SIZE))):
        if self.coorJson == {}:
            self.ImportRawDataFromCoorJson()

        lastSeatNumber = -1
        for data in fullData:
            checkFlag = not (bool((data[3] >> 0) & 0x01) or bool((data[3] >> 1) & 0x01))
            if self.HubList != []:
                for item in self.HubList:
                    if item.features['pHubID'] == data[:3]:
                        checkFlag = True
                    if item.features['proxS1']:
                        lastSeatNumber = item.features['proxS1']['number'] if lastSeatNumber < item.features['proxS1']['number'] else lastSeatNumber
                    if item.features['proxS2']:
                        lastSeatNumber = item.features['proxS2']['number'] if lastSeatNumber < item.features['proxS2']['number'] else lastSeatNumber
            if checkFlag is False:
                self.CreateHubObject(coorJson=self.coorJson, data=data, lastSeatNumber=lastSeatNumber+1)

    def CreateHubObject(self, json=dict(), coorJson=dict(), data=bytearray(RF_COMING_DATA_SIZE), lastSeatNumber=0):
        if json != dict():
            self.HubList.append(PxHub(json=json, coorJson=coorJson, dateTime=RTC_NOW))
        elif data != bytearray(RF_COMING_DATA_SIZE):
            self.HubList.append(PxHub(data=data, lastSeatNumber=lastSeatNumber, coorJson=coorJson if coorJson != dict() else None, dateTime=RTC_NOW))
        peripheral.buzzerObject(replay=1, onTime=25)
        

    def ClearUnnecessaryFiles(self):
        self.HubFeatures = {}
        self.coorJson = {}
        self.IsHubJsonFileExist = False
        gc.collect()

    def ClearAllData(self):
        self.HubList = []
        self.ClearUnnecessaryFiles()
        self.RemoveFile(HUBDB_JSON_FILE_NAME)

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
        return ('\n\r[RAM] -> Total:{0} Free:{1} ({2})'.format(T,F,P))
