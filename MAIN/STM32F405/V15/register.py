import os
import peripheral
import time
import binascii


OPEN_SCENE_SHOW_TIME = 0#2500
CLOSING_TIME = 10000
CLOSE_SCENE_SHOW_TIME = 1000
MAX_SEAT_NUMBER = 33

InComingDataSize = 10

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
        Threshold = 100
        PositiveTolerance = 10
        NegativeTolerance = 25
        constVal = 1
        divider = 10
        multiple = 1
        thresholdDivider = 2


class Sensor():
    FullData = bytearray(InComingDataSize)

    def __init__(self, ID=bytearray(3), IsSensorHasID=False, Prox1Active=False, Prox1Config=bytearray(5), Prox2Active=False, Prox2Config=bytearray(5)):
        super().__init__()
        self.ID = ID
        self.IsSensorHasID = IsSensorHasID

        self.Prox1_ConfigAddressInArray = 3
        self.Prox1_ResolationAddressInArray = 5
        self.Prox1_Threshold = Proximity.Default.Threshold
        self.Prox1_PositiveTolerance = Proximity.Default.PositiveTolerance
        self.Prox1_NegativeTolerance = Proximity.Default.NegativeTolerance
        self.Prox1_CurrentResolation = 0
        self.Prox1_SeatHasSensor = Prox1Active
        self.Prox1_IsSeatActive = False
        self.Prox1_IsSeatHasPassanger = False
        self.Prox1_IsSeatHasBelt = False

        self.Prox2_ConfigAddressInArray = 4
        self.Prox2_ResolationAddressInArray = 7
        self.Prox2_Threshold = Proximity.Default.Threshold
        self.Prox2_PositiveTolerance = Proximity.Default.PositiveTolerance
        self.Prox2_NegativeTolerance = Proximity.Default.NegativeTolerance
        self.Prox2_CurrentResolation = 0
        self.Prox2_SeatHasSensor = Prox2Active
        self.Prox2_IsSeatActive = False
        self.Prox2_IsSeatHasPassanger = False
        self.Prox2_IsSeatHasBelt = False

        self.SeatCount = 0

        self.BatteryMeasurement = 0
        self.BatteryMeasurementPercent = 0

        self.InComingDataCount = 0

        if Prox1Active == True:
            self.Prox1_ConfigAddressInArray = Prox1Config[0]
            self.Prox1_ResolationAddressInArray = Prox1Config[1]
            self.Prox1_Threshold = Prox1Config[2]
            self.Prox1_PositiveTolerance = Prox1Config[3]
            self.Prox1_NegativeTolerance = Prox1Config[4]
            self.Prox1_IsSeatActive = True
            self.SeatCount += 1
        if Prox2Active == True:
            self.Prox2_ConfigAddressInArray = Prox2Config[0]
            self.Prox2_ResolationAddressInArray = Prox2Config[1]
            self.Prox2_Threshold = Prox2Config[2]
            self.Prox2_PositiveTolerance = Prox2Config[3]
            self.Prox2_NegativeTolerance = Prox2Config[4]
            self.Prox2_IsSeatActive = True
            self.SeatCount += 1

    def DataIn(self, data=bytearray(InComingDataSize)):
        if data[:3] != self.ID:
            return False

        self.InComingDataCount += 1
        ref1Res = data[self.Prox1_ResolationAddressInArray + 1] | (data[self.Prox1_ResolationAddressInArray] << 8)
        ref2Res = data[self.Prox2_ResolationAddressInArray + 1] | (data[self.Prox2_ResolationAddressInArray] << 8)
        

        self.Prox1_IsSeatActive = (data[self.Prox1_ConfigAddressInArray] & 0x01) == 1
        self.Prox2_IsSeatActive = (data[self.Prox2_ConfigAddressInArray] & 0x01) == 1

        Prox1ResolationCurrentValue = 0 if ref1Res > 8191 else ref1Res
        Prox2ResolationCurrentValue = 0 if ref2Res > 8191 else ref2Res

        Prox1ResolationCurrentValue = 0 if self.Prox1_IsSeatActive == False else Prox1ResolationCurrentValue
        Prox2ResolationCurrentValue = 0 if self.Prox2_IsSeatActive == False else Prox2ResolationCurrentValue
        
        self.BatteryMeasurement = (data[3] & 0xF0 | (data[4] & 0xF0) >> 4) + 9
        self.BatteryMeasurementPercent = round(((self.BatteryMeasurement * 2.5 / 255 * 2) - 2.0) / 1.2 * 10) * 10
        self.BatteryMeasurementPercent = 100 if self.BatteryMeasurementPercent > 100 else self.BatteryMeasurementPercent
        self.BatteryMeasurementPercent = 0 if self.BatteryMeasurementPercent < 0 else self.BatteryMeasurementPercent

        self.Calibration(Prox1ResolationCurrentValue, Prox2ResolationCurrentValue)

        if self.Prox1_SeatHasSensor == True:
            if self.Prox1_IsSeatActive == True:
                self.Prox1_CurrentResolation = Prox1ResolationCurrentValue

                if self.Prox1_CurrentResolation > self.Prox1_Threshold:
                    self.Prox1_IsSeatHasPassanger = True
                elif self.Prox1_CurrentResolation < self.Prox1_Threshold:
                    self.Prox1_IsSeatHasPassanger = False

                self.Prox1_IsSeatHasBelt = True if ((data[self.Prox1_ConfigAddressInArray] >> 1) & 0x01) == 1 else False
            else:
                self.Prox1_CurrentResolation = 0
                self.Prox1_IsSeatHasPassanger = False
            

        if self.Prox2_SeatHasSensor == True:
            if self.Prox2_IsSeatActive == True:
                self.Prox2_CurrentResolation = Prox2ResolationCurrentValue

                if self.Prox2_CurrentResolation > self.Prox2_Threshold:
                    self.Prox2_IsSeatHasPassanger = True
                elif self.Prox2_CurrentResolation < self.Prox2_Threshold:
                    self.Prox2_IsSeatHasPassanger = False

                self.Prox2_IsSeatHasBelt = True if ((data[self.Prox2_ConfigAddressInArray] >> 1) & 0x01) == 1 else False
            else:
                self.Prox2_CurrentResolation = 0
                self.Prox2_IsSeatHasPassanger = False

        return True

    def Calibration(self, p1Res=0, p2Res=0):
        if self.SeatCount == 2: 
            if p1Res > p2Res and p1Res > Proximity.Default.Threshold:
                self.Prox1_Threshold = p1Res * 0.8
                self.Prox2_Threshold = self.Prox1_Threshold
                
            elif p2Res > p1Res and p2Res > Proximity.Default.Threshold:
                self.Prox2_Threshold = p2Res * 0.8
                self.Prox1_Threshold = self.Prox2_Threshold
                
            elif p1Res == 0 and p2Res == 0:
                self.Prox1_Threshold = Proximity.Default.Threshold
                self.Prox2_Threshold = Proximity.Default.Threshold
        elif self.SeatCount == 1:
            self.Prox1_Threshold = Proximity.Default.Threshold / 4



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
        except OSError:
            pass

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
                        if item.Prox1_SeatHasSensor == True:
                            itemCount += 1
                            debugLog += "{tc0}{0:2}-{tc1} ID:{id_c1}{1:3}{id_c2}, Sensor Resulation:{re_c1}{2:4}{re_c2}, Sensor Cable:{se_c1}{3:1}{se_c2}, Seat Belt:{be_c1}{4:1}{be_c2} --> RF Received Data Count:{rf_c1}{5:6}{rf_c2}\n\r"     \
                                        .format(itemCount, binascii.hexlify(item.ID), item.Prox1_CurrentResolation, item.Prox1_IsSeatActive, item.Prox1_IsSeatHasBelt, item.InComingDataCount                             \
                                                         , tc0   = TextColour.BOLD + TextColour.OKCYAN                                         , tc1   = TextColour.ENDC                          \
                                                         , id_c1 = TextColour.OKBLUE                                                           , id_c2 = TextColour.ENDC                          \
                                                         , re_c1 = TextColour.OKGREEN if item.Prox1_IsSeatHasPassanger else TextColour.WARNING , re_c2 = TextColour.ENDC                          \
                                                         , se_c1 = TextColour.OKGREEN if item.Prox1_IsSeatActive       else TextColour.FAIL    , se_c2 = TextColour.ENDC                          \
                                                         , be_c1 = TextColour.OKGREEN if item.Prox1_IsSeatHasBelt      else TextColour.WARNING , be_c2 = TextColour.ENDC                          \
                                                         , rf_c1 = TextColour.OKGREEN if item.InComingDataCount > 0    else TextColour.FAIL    , rf_c2 = TextColour.ENDC)
                        if item.Prox2_SeatHasSensor == True:
                            itemCount += 1
                            debugLog += "{tc0}{0:2}-{tc1} ID:{id_c1}{1:3}{id_c2}, Sensor Resulation:{re_c1}{2:4}{re_c2}, Sensor Cable:{se_c1}{3:1}{se_c2}, Seat Belt:{be_c1}{4:1}{be_c2} --> RF Received Data Count:{rf_c1}{5:6}{rf_c2}\n\r"     \
                                        .format(itemCount, binascii.hexlify(item.ID), item.Prox2_CurrentResolation, item.Prox2_IsSeatActive, item.Prox2_IsSeatHasBelt, item.InComingDataCount                             \
                                                         , tc0   = TextColour.BOLD + TextColour.OKCYAN                                         , tc1   = TextColour.ENDC                          \
                                                         , id_c1 = TextColour.OKBLUE                                                           , id_c2 = TextColour.ENDC                          \
                                                         , re_c1 = TextColour.OKGREEN if item.Prox2_IsSeatHasPassanger else TextColour.WARNING , re_c2 = TextColour.ENDC                          \
                                                         , se_c1 = TextColour.OKGREEN if item.Prox2_IsSeatActive       else TextColour.FAIL    , se_c2 = TextColour.ENDC                          \
                                                         , be_c1 = TextColour.OKGREEN if item.Prox2_IsSeatHasBelt      else TextColour.WARNING , be_c2 = TextColour.ENDC                          \
                                                         , rf_c1 = TextColour.OKGREEN if item.InComingDataCount > 0    else TextColour.FAIL    , rf_c2 = TextColour.ENDC)
                        continue
        print(debugLog)

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
                            self.CreateSensorObject(data[:3], True, True, [3, 5, Proximity.Default.Threshold, Proximity.Default.PositiveTolerance, Proximity.Default.NegativeTolerance], True, [4, 7, Proximity.Default.Threshold, Proximity.Default.PositiveTolerance, Proximity.Default.NegativeTolerance])
                        else:
                            self.CreateSensorObject(data[:3], True, True, [3, 5, Proximity.Default.Threshold, Proximity.Default.PositiveTolerance, Proximity.Default.NegativeTolerance], False, [4, 7, Proximity.Default.Threshold, Proximity.Default.PositiveTolerance, Proximity.Default.NegativeTolerance])
                    elif (((data[4] >> 0) & 0x01) == 1) and (data[8] | (data[7] << 8)) > (data[6] | (data[5] << 8)):
                        if ((data[3] >> 0) & 0x01) == 1:
                            self.CreateSensorObject(data[:3], True, True, [4, 7, Proximity.Default.Threshold, Proximity.Default.PositiveTolerance, Proximity.Default.NegativeTolerance], True, [3, 5, Proximity.Default.Threshold, Proximity.Default.PositiveTolerance, Proximity.Default.NegativeTolerance])
                        else:
                            self.CreateSensorObject(data[:3], True, True, [4, 7, Proximity.Default.Threshold, Proximity.Default.PositiveTolerance, Proximity.Default.NegativeTolerance], False, [3, 5, Proximity.Default.Threshold, Proximity.Default.PositiveTolerance, Proximity.Default.NegativeTolerance])

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
            self.dbRaw += str(b) + ","
        self.dbRaw += "*"
        self.dbRaw += str(Prox2Active)
        self.dbRaw += "*"
        for b in Prox2Config:
            self.dbRaw += str(b) + ","
        self.dbRaw += "\n"

        replay = 1
        if Prox1Active == True and Prox2Active == True:
            replay = 2
        peripheral.buzzerObject(replay=replay, onTime=25)

        print(self.dbRaw)

    def CheckCRC(self, data=bytearray(InComingDataSize)):
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
        except OSError:
            pass
