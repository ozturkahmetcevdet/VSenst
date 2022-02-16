import os
import peripheral
import time

OPEN_SCENE_SHOW_TIME = 2500
CLOSING_TIME = 10000
CLOSE_SCENE_SHOW_TIME = 1000
MAX_SEAT_NUMBER = 33

class Proximity:
    class Default:
        Threshold = 40
        PositiveTolerance = 10
        NegativeTolerance = 10
        MaxLineThreshold = 256

class Sensor():
    FullData = bytearray(16)

    Prox1_ConfigAddressInArray = 10
    Prox1_ResolationAddressInArray = 12
    Prox1_Threshold = Proximity.Default.Threshold
    Prox1_PositiveTolerance = Proximity.Default.PositiveTolerance
    Prox1_NegativeTolerance = Proximity.Default.NegativeTolerance
    Prox1_CurrentResolation = 0
    Prox1_IsSeatActive = False
    Prox1_IsSeatHasPassanger = False
    Prox1_IsSeatHasBelt = False

    Prox2_ConfigAddressInArray = 11
    Prox2_ResolationAddressInArray = 14
    Prox2_Threshold = Proximity.Default.Threshold
    Prox2_PositiveTolerance = Proximity.Default.PositiveTolerance
    Prox2_NegativeTolerance = Proximity.Default.NegativeTolerance
    Prox2_CurrentResolation = 0
    Prox2_IsSeatActive = False
    Prox2_IsSeatHasPassanger = False
    Prox2_IsSeatHasBelt = False

    def __init__(self, ID=bytearray(10), IsSensorHasID=False, Prox1Active=False, Prox1Config=bytearray(5), Prox2Active=False, Prox2Config=bytearray(5)):
        super().__init__()
        self.ID = ID
        self.IsSensorHasID = IsSensorHasID
        if Prox1Active is True:
            self.Prox1_ConfigAddressInArray = Prox1Config[0]
            self.Prox1_ResolationAddressInArray = Prox1Config[1]
            self.Prox1_Threshold = Prox1Config[2]
            self.Prox1_PositiveTolerance = Prox1Config[3]
            self.Prox1_NegativeTolerance = Prox1Config[4]
            self.Prox1_IsSeatActive = True
        if Prox2Active is True:
            self.Prox2_ConfigAddressInArray = Prox2Config[0]
            self.Prox2_ResolationAddressInArray = Prox2Config[1]
            self.Prox2_Threshold = Prox2Config[2]
            self.Prox2_PositiveTolerance = Prox2Config[3]
            self.Prox2_NegativeTolerance = Prox2Config[4]
            self.Prox2_IsSeatActive = True

    def DataIn(self, data=bytearray(16)):
        if data[:10] != self.ID:
            print("ID Error")
            return False
        if self.Prox1_IsSeatActive is True:
            if data[self.Prox1_ResolationAddressInArray + 1] | (data[self.Prox1_ResolationAddressInArray] << 8) > Proximity.Default.MaxLineThreshold:
                return
            self.Prox1_CurrentResolation = data[self.Prox1_ResolationAddressInArray + 1] | (data[self.Prox1_ResolationAddressInArray] << 8)
            triggerResolation = self.Prox1_CurrentResolation - (self.Prox1_Threshold + self.Prox1_PositiveTolerance)
            print("p1:" + str(triggerResolation))
            if triggerResolation > 0:
                self.Prox1_IsSeatHasPassanger = True
            else:
                self.Prox1_IsSeatHasPassanger = False
            if ((data[self.Prox1_ConfigAddressInArray] >> 1) & 0x01) == 1:
                self.Prox1_IsSeatHasBelt = True
            else:
                self.Prox1_IsSeatHasBelt = False

        if self.Prox2_IsSeatActive is True:
            if data[self.Prox2_ResolationAddressInArray + 1] | (data[self.Prox2_ResolationAddressInArray] << 8) > Proximity.Default.MaxLineThreshold:
                return
            self.Prox2_CurrentResolation = data[self.Prox2_ResolationAddressInArray + 1] | (data[self.Prox2_ResolationAddressInArray] << 8)
            triggerResolation = self.Prox2_CurrentResolation - (self.Prox2_Threshold + self.Prox2_PositiveTolerance)
            print("p2:" + str(triggerResolation))
            if triggerResolation > 0:
                self.Prox2_IsSeatHasPassanger = True
            else:
                self.Prox2_IsSeatHasPassanger = False
            if ((data[self.Prox2_ConfigAddressInArray] >> 1) & 0x01) == 1:
                self.Prox2_IsSeatHasBelt = True
            else:
                self.Prox2_IsSeatHasBelt = False
        return True

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
        if self.IsDbFileExist is True:
            self.ImportRawDataFromDB()
            self.UnzipRawData()

    def CreateDbFile(self, name="SensorDB.db"):
        try:
            self.file = open(name, "r")
            self.IsDbFileExist = True
        except OSError:
            pass

    def FlushRawDataToDB(self):
        if self.dbRaw is "":
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
        if self.dbRaw is "":
            return
        self.rawList = self.dbRaw.splitlines()
        self.dbRaw = ""
        self.SensorList.clear()
        tList = []

        for item in self.rawList:
            temporaryData = item.split('*')
            for d in temporaryData[0].split(','):
                if d is not "":
                    tList.append(int(d))
            D1 = bytearray(tList)
            tList.clear()
            if temporaryData[1] is "True":
                D2 = True
            else:
                D2 = False
            if temporaryData[2] is "True":
                D3 = True
            else:
                D3 = False
            for d in temporaryData[3].split(','):
                if d is not "":
                    tList.append(int(d))
            D4 = bytearray(tList)
            tList.clear()
            if temporaryData[4] is "True":
                D5 = True
            else:
                D5 = False
            for d in temporaryData[5].split(','):
                if d is not "":
                    tList.append(int(d))
            D6 = bytearray(tList)
            tList.clear()

            self.CreateSensorObject(D1, D2, D3, D4, D5, D6)

    def Process(self, fullData=[]):
        for data in fullData:
            if self.SensorList:
                for item in self.SensorList:
                    item.DataIn(data)

    def DefineSensorObject(self, fullData=[]):
        checkFlag = True
        print(fullData)
        for data in fullData:
            if self.SensorList:
                for item in self.SensorList:
                    if item.ID == data[:10]:
                        checkFlag = False
            if checkFlag is True:
                if (((data[10] >> 0) & 0x01) == 1) and (data[13] | (data[12] << 8)) > (data[15] | (data[14] << 8)):
                    if ((data[11] >> 0) & 0x01) == 1:
                        self.CreateSensorObject(data[:10], True, True, [10, 12, Proximity.Default.Threshold, Proximity.Default.PositiveTolerance, Proximity.Default.NegativeTolerance], True, [11, 14, Proximity.Default.Threshold, Proximity.Default.PositiveTolerance, Proximity.Default.NegativeTolerance])
                    else:
                        self.CreateSensorObject(data[:10], True, True, [10, 12, Proximity.Default.Threshold, Proximity.Default.PositiveTolerance, Proximity.Default.NegativeTolerance], False, [11, 14, Proximity.Default.Threshold, Proximity.Default.PositiveTolerance, Proximity.Default.NegativeTolerance])
                elif (((data[11] >> 0) & 0x01) == 1) and (data[15] | (data[14] << 8)) > (data[13] | (data[12] << 8)):
                    if ((data[10] >> 0) & 0x01) == 1:
                        self.CreateSensorObject(data[:10], True, True, [11, 14, Proximity.Default.Threshold, Proximity.Default.PositiveTolerance, Proximity.Default.NegativeTolerance], True, [10, 12, Proximity.Default.Threshold, Proximity.Default.PositiveTolerance, Proximity.Default.NegativeTolerance])
                    else:
                        self.CreateSensorObject(data[:10], True, True, [11, 14, Proximity.Default.Threshold, Proximity.Default.PositiveTolerance, Proximity.Default.NegativeTolerance], False, [10, 12, Proximity.Default.Threshold, Proximity.Default.PositiveTolerance, Proximity.Default.NegativeTolerance])

    def CreateSensorObject(self, ID=bytearray(10), IsSensorHasID=False, Prox1Active=False, Prox1Config=bytearray(5), Prox2Active=False, Prox2Config=bytearray(5)):
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
        if Prox1Active is True and Prox2Active is True:
            replay = 2
        peripheral.buzzerObject(replay=replay, onTime=25)

        print(self.dbRaw)

    def ClearAllData(self):
        self.SensorList.clear()
        self.dbRaw = ""
        try:
            os.remove("SensorDB.db")
        except OSError:
            pass
