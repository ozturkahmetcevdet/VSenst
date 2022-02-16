from micropython import const
import os
import peripheral
import time
import binascii


OPEN_SCENE_SHOW_TIME    = const(2500)
CLOSING_TIME            = const(10000)
CLOSE_SCENE_SHOW_TIME   = const(1000)
MAX_SEAT_NUMBER         = const(55)

RF_DATA_SIZE            = const(109)

class TextColour:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class Proximity:
    class Default:
        Threshold = 60
        thresholdDivider = 2
        ThresholdSingle = Threshold / thresholdDivider


class Sensor():
    FullData = bytearray(RF_DATA_SIZE)

    def __init__(self, ID=bytearray(3), IsSensorHasID=False, Prox1Active=False, Prox1Config=bytearray(5), Prox2Active=False, Prox2Config=bytearray(5)):
        super().__init__()
        self.ID = ID
        self.IsSensorHasID = IsSensorHasID

        self.Prox1_ConfigAddressInArray = 3
        self.Prox1_ResolationAddressInArray = 5
        self.Prox1_Threshold = Proximity.Default.Threshold

        self.Prox1_CurrentResolation = 0
        self.Prox1_Counter = 0
        self.Prox1_PeakValue = 0
        self.Prox1_CounterLimit = 4
        self.Prox1_FilterValue = 10
        self.Prox1_ADCReferance = 0
        self.Prox1_NegativeThreshold = -30
        self.Prox1_Calibrate = True

        self.Prox1_SeatHasSensor = Prox1Active
        self.Prox1_IsSeatActive = False
        self.Prox1_IsSeatHasPassanger = False
        self.Prox1_IsSeatHasBelt = False
        self.Prox1_Count = 0

        self.Prox2_ConfigAddressInArray = 4
        self.Prox2_ResolationAddressInArray = 7
        self.Prox2_Threshold = Proximity.Default.Threshold

        self.Prox2_CurrentResolation = 0
        self.Prox2_Counter = 0
        self.Prox2_PeakValue = 0
        self.Prox2_CounterLimit = 4
        self.Prox2_FilterValue = 10
        self.Prox2_ADCReferance = 0
        self.Prox2_NegativeThreshold = -30
        self.Prox2_Calibrate = True

        self.Prox2_SeatHasSensor = Prox2Active
        self.Prox2_IsSeatActive = False
        self.Prox2_IsSeatHasPassanger = False
        self.Prox2_IsSeatHasBelt = False
        self.Prox2_Count = 0

        self.SeatCount = 0

        self.BatteryMeasurementPercent = 0

        self.InComingDataCount = 0

        if Prox1Active == True:
            self.Prox1_ConfigAddressInArray = Prox1Config[0]
            self.Prox1_ResolationAddressInArray = Prox1Config[1]
            self.Prox1_Threshold = Prox1Config[2]
            #self.Prox1_ADCReferance = (Prox1Config[3] << 8) | Prox1Config[4]
            self.Prox1_IsSeatActive = True
            self.SeatCount += 1
        if Prox2Active == True:
            self.Prox2_ConfigAddressInArray = Prox2Config[0]
            self.Prox2_ResolationAddressInArray = Prox2Config[1]
            self.Prox2_Threshold = Prox2Config[2]
            #self.Prox2_ADCReferance = (Prox2Config[3] << 8) | Prox2Config[4]
            self.Prox2_IsSeatActive = True
            self.SeatCount += 1

    def DataIn(self, data=bytearray(RF_DATA_SIZE)):
        if data[:3] != self.ID:
            return False

        self.InComingDataCount += 1
        
        self.Prox1_IsSeatActive = (data[self.Prox1_ConfigAddressInArray] & 0x01) == 1
        self.Prox2_IsSeatActive = (data[self.Prox2_ConfigAddressInArray] & 0x01) == 1

        Prox1ResolationCurrentValue = 0 if self.Prox1_IsSeatActive == False else (data[self.Prox1_ResolationAddressInArray + 1] | (data[self.Prox1_ResolationAddressInArray] << 8)) << 0
        Prox2ResolationCurrentValue = 0 if self.Prox2_IsSeatActive == False else (data[self.Prox2_ResolationAddressInArray + 1] | (data[self.Prox2_ResolationAddressInArray] << 8)) << 0
        
        self.BatteryMeasurementPercent = (data[3] & 0xF0 | (data[4] & 0xF0) >> 4)

        self.Calibration(Prox1ResolationCurrentValue, Prox2ResolationCurrentValue)

        if self.Prox1_SeatHasSensor == True:
            if self.Prox1_IsSeatActive == True:
                if self.Prox1_CurrentResolation > self.Prox1_Threshold:
                    self.Prox1_Count += 1 if self.Prox1_IsSeatHasPassanger == False else 0
                    self.Prox1_IsSeatHasPassanger = True
                elif self.Prox1_CurrentResolation < self.Prox1_Threshold:
                    self.Prox1_IsSeatHasPassanger = False

                self.Prox1_IsSeatHasBelt = True if ((data[self.Prox1_ConfigAddressInArray] >> 1) & 0x01) == 1 else False
            else:
                self.Prox1_CurrentResolation = 0
                self.Prox1_IsSeatHasPassanger = False
            

        if self.Prox2_SeatHasSensor == True:
            if self.Prox2_IsSeatActive == True:
                if self.Prox2_CurrentResolation > self.Prox2_Threshold:
                    self.Prox2_Count += 1 if self.Prox2_IsSeatHasPassanger == False else 0
                    self.Prox2_IsSeatHasPassanger = True
                elif self.Prox2_CurrentResolation < self.Prox2_Threshold:
                    self.Prox2_IsSeatHasPassanger = False

                self.Prox2_IsSeatHasBelt = True if ((data[self.Prox2_ConfigAddressInArray] >> 1) & 0x01) == 1 else False
            else:
                self.Prox2_CurrentResolation = 0
                self.Prox2_IsSeatHasPassanger = False

        return True

    def Calibration(self, p1Res=0, p2Res=0):

        if self.Prox1_IsSeatActive:
            if p1Res < (self.Prox1_ADCReferance >> 3):
                self.Prox1_Calibrate = True

            self.Prox1_CurrentResolation = p1Res - self.Prox1_ADCReferance
            if self.Prox1_CurrentResolation < self.Prox1_NegativeThreshold:
                self.Prox1_ADCReferance = p1Res
                self.Prox1_Counter = 0
                self.Prox1_CurrentResolation = 0
            elif self.Prox1_Calibrate == False:
                self.Prox1_PeakValue = self.Prox1_CurrentResolation if self.Prox1_PeakValue < self.Prox1_CurrentResolation else self.Prox1_PeakValue
                self.Prox1_Counter += 1 if self.Prox1_Counter < self.Prox1_CounterLimit else -self.Prox1_Counter
                if self.Prox1_Counter > (self.Prox1_CounterLimit >> 2) and self.Prox1_PeakValue < self.Prox1_FilterValue:
                    self.Prox1_ADCReferance = p1Res + self.Prox1_FilterValue
                    self.Prox1_CurrentResolation = 0
                if self.Prox1_Counter == 0 and self.Prox1_PeakValue < (Proximity.Default.Threshold if self.SeatCount == 2 else Proximity.Default.ThresholdSingle):
                    self.Prox1_ADCReferance = p1Res + self.Prox1_PeakValue
                    self.Prox1_CurrentResolation = 0
                self.Prox1_PeakValue = 0 if self.Prox1_Counter == 0 else self.Prox1_PeakValue
            else:
                self.Prox1_ADCReferance = p1Res if self.Prox1_CurrentResolation >= (self.Prox1_NegativeThreshold >> 2) else self.Prox1_ADCReferance
                self.Prox1_Counter += 1 if self.Prox1_CurrentResolation <= 0 and self.Prox1_CurrentResolation >= self.Prox1_NegativeThreshold else -self.Prox1_Counter
                self.Prox1_Calibrate = False if self.Prox1_Counter > (self.Prox1_CounterLimit >> 2) else self.Prox1_Calibrate
                self.Prox1_Counter = 0 if self.Prox1_Calibrate == False else self.Prox1_Counter
            self.Prox1_CurrentResolation = 0 if self.Prox1_CurrentResolation < 0 or self.Prox1_Calibrate else self.Prox1_CurrentResolation

        if self.Prox2_IsSeatActive:
            if p2Res < (self.Prox2_ADCReferance >> 3):
                self.Prox2_Calibrate = True

            self.Prox2_CurrentResolation = p2Res - self.Prox2_ADCReferance
            if self.Prox2_CurrentResolation < self.Prox2_NegativeThreshold:
                self.Prox2_ADCReferance = p2Res
                self.Prox2_Counter = 0
                self.Prox2_CurrentResolation = 0
            elif self.Prox2_Calibrate == False:
                self.Prox2_PeakValue = self.Prox2_CurrentResolation if self.Prox2_PeakValue < self.Prox2_CurrentResolation else self.Prox2_PeakValue
                self.Prox2_Counter += 1 if self.Prox2_Counter < self.Prox2_CounterLimit else -self.Prox2_Counter
                if self.Prox2_Counter > (self.Prox2_CounterLimit >> 2) and self.Prox2_PeakValue < self.Prox2_FilterValue:
                    self.Prox2_ADCReferance = p2Res + self.Prox2_FilterValue
                    self.Prox2_CurrentResolation = 0
                if self.Prox2_Counter == 0 and self.Prox2_PeakValue < (Proximity.Default.Threshold if self.SeatCount == 2 else Proximity.Default.ThresholdSingle):
                    self.Prox2_ADCReferance = p2Res + self.Prox2_PeakValue
                    self.Prox2_CurrentResolation = 0
                self.Prox2_PeakValue = 0 if self.Prox2_Counter == 0 else self.Prox2_PeakValue
            else:
                self.Prox2_ADCReferance = p2Res if self.Prox2_CurrentResolation >= (self.Prox2_NegativeThreshold >> 2) else self.Prox2_ADCReferance
                self.Prox2_Counter += 1 if self.Prox2_CurrentResolation <= 0 and self.Prox2_CurrentResolation >= self.Prox2_NegativeThreshold else -self.Prox2_Counter
                self.Prox2_Calibrate = False if self.Prox2_Counter > (self.Prox2_CounterLimit >> 2) else self.Prox2_Calibrate
                self.Prox2_Counter = 0 if self.Prox2_Calibrate == False else self.Prox2_Counter
            self.Prox2_CurrentResolation = 0 if self.Prox2_CurrentResolation < 0 or self.Prox2_Calibrate else self.Prox2_CurrentResolation

        if self.SeatCount == 2: 
            if self.Prox1_CurrentResolation > self.Prox2_CurrentResolation and self.Prox1_CurrentResolation > Proximity.Default.Threshold:
                calc = self.Prox1_CurrentResolation * 0.4
                self.Prox1_Threshold = calc if self.Prox1_Threshold < calc else self.Prox1_Threshold
                self.Prox2_Threshold = self.Prox1_Threshold * 2
                
            elif self.Prox2_CurrentResolation > self.Prox1_CurrentResolation and self.Prox2_CurrentResolation > Proximity.Default.Threshold:
                calc = self.Prox2_CurrentResolation * 0.4
                self.Prox2_Threshold = calc if self.Prox2_Threshold < calc else self.Prox2_Threshold
                self.Prox1_Threshold = self.Prox2_Threshold * 2

            if (self.Prox1_Threshold != Proximity.Default.Threshold and self.Prox1_CurrentResolation < self.Prox1_Threshold) and (self.Prox2_Threshold != Proximity.Default.Threshold and self.Prox2_CurrentResolation < self.Prox2_Threshold):
                self.Prox1_ADCReferance += self.Prox1_CurrentResolation
                self.Prox1_CurrentResolation = 0
                self.Prox2_ADCReferance += self.Prox2_CurrentResolation
                self.Prox2_CurrentResolation = 0
                
            if self.Prox1_CurrentResolation < Proximity.Default.Threshold and self.Prox2_CurrentResolation < Proximity.Default.Threshold:
                self.Prox1_Threshold = Proximity.Default.Threshold
                self.Prox2_Threshold = Proximity.Default.Threshold

        elif self.SeatCount == 1:
            if self.Prox1_CurrentResolation > Proximity.Default.ThresholdSingle:
                calc = self.Prox1_CurrentResolation * 0.4
                self.Prox1_Threshold = calc if self.Prox1_Threshold < calc else self.Prox1_Threshold
                
            if self.Prox1_Threshold != Proximity.Default.ThresholdSingle and self.Prox1_CurrentResolation < self.Prox1_Threshold:
                self.Prox1_ADCReferance += self.Prox1_CurrentResolation
                self.Prox1_CurrentResolation = 0
            
            if self.Prox1_CurrentResolation < Proximity.Default.ThresholdSingle:
                self.Prox1_Threshold = Proximity.Default.Threshold / Proximity.Default.thresholdDivider



class DataBase():
    def __init__(self):
        super().__init__()
        self.SensorList = []
        self.dbRaw = ""
        self.rawList = ""
        self.file = ""
        self.IsDbFileExist = False
        self.Setup()

    def Setup(self):
        self.CreateDbFile("SensorDB.db")
        if self.IsDbFileExist == True:
            self.ImportRawDataFromDB()
            self.UnzipRawData()

    def CreateDbFile(self, name="SensorDB.db"):
        try:
            self.file = open(name, "r")
            self.IsDbFileExist = True
        except OSError as err:
            print("OS error: {0}".format(err))
        except ValueError:
            print("Could not open file. ---{0}".format(name))
        except:
            print("Unexpected error!")
            raise

    def FlushRawDataToDB(self):
        if self.dbRaw == "":
            return
        with open("SensorDB.db", "w") as self.file:
            self.file.write(self.dbRaw)
            time.sleep(.01)
            self.file.flush()
            time.sleep(.01)
            self.file.close()
            time.sleep(.01)

    def ImportRawDataFromDB(self):
        with open("SensorDB.db", "r") as self.file:
            self.dbRaw = self.file.read()
            time.sleep(.01)
            self.file.close()

    def UnzipRawData(self):
        if self.dbRaw == "":
            return
        self.rawList = self.dbRaw.splitlines()
        self.dbRaw = ""
        self.SensorList.clear()
        tList = []

        for item in self.rawList:
            temporaryData = item.split('*')
            for d in temporaryData[0].split(','):
                if d != "":
                    tList.append(int(d))
            D1 = bytearray(tList)
            tList.clear()
            if temporaryData[1] == "True":
                D2 = True
            else:
                D2 = False
            if temporaryData[2] == "True":
                D3 = True
            else:
                D3 = False
            for d in temporaryData[3].split(','):
                if d != "":
                    tList.append(int(d))
            D4 = bytearray(tList)
            tList.clear()
            if temporaryData[4] == "True":
                D5 = True
            else:
                D5 = False
            for d in temporaryData[5].split(','):
                if d != "":
                    tList.append(int(d))
            D6 = bytearray(tList)
            tList.clear()

            self.CreateSensorObject(D1, D2, D3, D4, D5, D6)

    def Process(self, fullData=[]):
        itemCount = 0
        debugLog = "\f"
        for data in fullData:
            if self.SensorList and self.CheckCRC(data) == True:
                for item in self.SensorList:
                    if item.DataIn(data) == True:
                        continue
        for item in self.SensorList:
            if item.Prox2_SeatHasSensor == True:
                itemCount += 1

                debugLog += "{tc0}{0:2}-{tc1} ID:{id_c1}{1:3}{id_c2}, Sensor Resolation:{re_c1}{2:4}{re_c2}, Sensor Cable:{se_c1}{3}{se_c2}, Seat Belt:{be_c1}{4}{be_c2}, Calibration:{ca_c1}{5}{ca_c2}, Count:{co_c1}{6:4}{co_c2} --> RF Received Data Count:{rf_c1}{7:6}{rf_c2}, Battery:{bt_c1}%{8:3}{bt_c2}\n\r"     \
                            .format(itemCount, binascii.hexlify(item.ID), item.Prox2_CurrentResolation, bool(item.Prox2_IsSeatActive), bool(item.Prox2_IsSeatHasBelt), bool(not item.Prox2_Calibrate), item.Prox2_Count, item.InComingDataCount, item.BatteryMeasurementPercent   \
                                                , tc0   = TextColour.BOLD + TextColour.OKCYAN                                               , tc1   = TextColour.ENDC                          \
                                                , id_c1 = TextColour.OKBLUE                                                                 , id_c2 = TextColour.ENDC                          \
                                                , re_c1 = TextColour.OKGREEN if item.Prox2_IsSeatHasPassanger       else TextColour.WARNING , re_c2 = TextColour.ENDC                          \
                                                , se_c1 = TextColour.OKGREEN if item.Prox2_IsSeatActive             else TextColour.FAIL    , se_c2 = TextColour.ENDC                          \
                                                , be_c1 = TextColour.OKGREEN if item.Prox2_IsSeatHasBelt            else TextColour.WARNING , be_c2 = TextColour.ENDC                          \
                                                , ca_c1 = TextColour.OKGREEN if not item.Prox2_Calibrate            else TextColour.FAIL    , ca_c2 = TextColour.ENDC                          \
                                                , co_c1 = TextColour.HEADER                                                                 , co_c2 = TextColour.ENDC                          \
                                                , rf_c1 = TextColour.OKGREEN if item.InComingDataCount > 0          else TextColour.FAIL    , rf_c2 = TextColour.ENDC                          \
                                                , bt_c1 = TextColour.OKGREEN if item.BatteryMeasurementPercent > 20 else TextColour.FAIL    , bt_c2 = TextColour.ENDC)
            if item.Prox1_SeatHasSensor == True:
                itemCount += 1

                debugLog += "{tc0}{0:2}-{tc1} ID:{id_c1}{1:3}{id_c2}, Sensor Resolation:{re_c1}{2:4}{re_c2}, Sensor Cable:{se_c1}{3}{se_c2}, Seat Belt:{be_c1}{4}{be_c2}, Calibration:{ca_c1}{5}{ca_c2}, Count:{co_c1}{6:4}{co_c2} --> RF Received Data Count:{rf_c1}{7:6}{rf_c2}, Battery:{bt_c1}%{8:3}{bt_c2}\n\r"     \
                            .format(itemCount, binascii.hexlify(item.ID), item.Prox1_CurrentResolation, bool(item.Prox1_IsSeatActive), bool(item.Prox1_IsSeatHasBelt), bool(not item.Prox1_Calibrate), item.Prox1_Count, item.InComingDataCount, item.BatteryMeasurementPercent   \
                                                , tc0   = TextColour.BOLD + TextColour.OKCYAN                                               , tc1   = TextColour.ENDC                          \
                                                , id_c1 = TextColour.OKBLUE                                                                 , id_c2 = TextColour.ENDC                          \
                                                , re_c1 = TextColour.OKGREEN if item.Prox1_IsSeatHasPassanger       else TextColour.WARNING , re_c2 = TextColour.ENDC                          \
                                                , se_c1 = TextColour.OKGREEN if item.Prox1_IsSeatActive             else TextColour.FAIL    , se_c2 = TextColour.ENDC                          \
                                                , be_c1 = TextColour.OKGREEN if item.Prox1_IsSeatHasBelt            else TextColour.WARNING , be_c2 = TextColour.ENDC                          \
                                                , ca_c1 = TextColour.OKGREEN if not item.Prox1_Calibrate            else TextColour.FAIL    , ca_c2 = TextColour.ENDC                          \
                                                , co_c1 = TextColour.HEADER                                                                 , co_c2 = TextColour.ENDC                          \
                                                , rf_c1 = TextColour.OKGREEN if item.InComingDataCount > 0          else TextColour.FAIL    , rf_c2 = TextColour.ENDC                          \
                                                , bt_c1 = TextColour.OKGREEN if item.BatteryMeasurementPercent > 20 else TextColour.FAIL    , bt_c2 = TextColour.ENDC)
        print(debugLog)
        return ""

    def DefineSensorObject(self, fullData=[]):
        self.SensorList
        checkFlag = True
        for data in fullData:
            if self.CheckCRC(data) == True:
                if self.SensorList:
                    for item in self.SensorList:
                        if item.ID == data[:3]:
                            checkFlag = False
                            break
                if checkFlag is True:
                    print(fullData)
                    if (((data[3] >> 0) & 0x01) == 1) and (data[6] | (data[5] << 8)) > (data[8] | (data[7] << 8)):
                        if ((data[4] >> 0) & 0x01) == 1:
                            self.CreateSensorObject(data[:3], True, True, [3, 5, Proximity.Default.Threshold], True, [4, 7, Proximity.Default.Threshold])
                        else:
                            self.CreateSensorObject(data[:3], True, True, [3, 5, Proximity.Default.ThresholdSingle], False, [4, 7, Proximity.Default.Threshold])
                    elif (((data[4] >> 0) & 0x01) == 1) and (data[8] | (data[7] << 8)) > (data[6] | (data[5] << 8)):
                        if ((data[3] >> 0) & 0x01) == 1:
                            self.CreateSensorObject(data[:3], True, True, [4, 7, Proximity.Default.Threshold],  True, [3, 5, Proximity.Default.Threshold])
                        else:
                            self.CreateSensorObject(data[:3], True, True, [4, 7, Proximity.Default.ThresholdSingle], False, [3, 5, Proximity.Default.Threshold])

    def CreateSensorObject(self, ID=bytearray(3), IsSensorHasID=False, Prox1Active=False, Prox1Config=bytearray(5), Prox2Active=False, Prox2Config=bytearray(5)):
        self.SensorList.append(Sensor(ID, IsSensorHasID, Prox1Active, Prox1Config, Prox2Active, Prox2Config))

        for b in ID:
            self.dbRaw += str(b) + ","
        self.dbRaw += "*"
        self.dbRaw += str(IsSensorHasID)
        self.dbRaw += "*"
        self.dbRaw += str(Prox1Active)
        self.dbRaw += "*"
        for b in Prox1Config:
            self.dbRaw += str(int(b)) + ","
        self.dbRaw += "*"
        self.dbRaw += str(Prox2Active)
        self.dbRaw += "*"
        for b in Prox2Config:
            self.dbRaw += str(int(b)) + ","
        self.dbRaw += "\n"

        replay = 1
        if Prox1Active == True and Prox2Active == True:
            replay = 2
        peripheral.buzzerObject(replay=replay, onTime=25)

        print(self.dbRaw)

    def CheckCRC(self, data=bytearray(RF_DATA_SIZE)):
        crc = 0xDB
        for i in range(len(data) - 1):
            crc ^= data[i]
        #print("\n\rCRC:{}, C:{}, Status: {}\n\r{}".format(crc, data[len(data) - 1], bool(crc == data[len(data) - 1]), data))

        return bool(crc == data[len(data) - 1])

    def ClearAllData(self):
        self.SensorList.clear()
        self.dbRaw = ""
        try:
            os.remove("SensorDB.db")
        except OSError as err:
            print("OS error: {0}".format(err))
        except ValueError:
            print("Could not remove file. ---SensorDB.db")
        except:
            print("Unexpected error!")
            raise
