import gc
from micropython import const
import binascii


OPEN_SCENE_SHOW_TIME        = const(2500)
CLOSING_TIME                = const(10000)
CLOSE_SCENE_SHOW_TIME       = const(1000)
PXHUB_ESTIMATED_LIFETIME    = const(1675) #day

class T:
    D = const( 40)
    N = const(-30)
    S = const( 10)
    
class key:
    class px:
        number              = 0
        calibrationStatus   = 1
        seatStatus          = 2
        seatPolarity        = 3
        cableStatus         = 4
        beltStatus          = 5
        beltPolarity        = 6
        baseLine            = 7
        currentValue        = 8
        currentThreshold    = 9
        beltCount           = 10
        seatCount           = 11
        cableErrorCount     = 12
        calibrationCount    = 13
    class hub:
        idNumber            = 0
        px1                 = 1
        px2                 = 2
        createTime          = 3
        dataCount           = 4
        resetCount          = 5
        battery             = 6
        lifeTime            = 7
        doubleSeat          = 8
        crcErrorCount       = 9
        rssi                = 10


class Px():
    def __init__(self, seatNumber=int, calibrationStatus=bool, seatBeltPolarity=bool, baseLine=int, seatBeltCount=int, seatCount=int, cableErrorCount=int, calibrationCount=int) -> None:
        self.features = list()
        self.features.append(seatNumber)                #key.px.number
        self.features.append(int(calibrationStatus))    #key.px.calibrationStatus
        self.features.append(0)                         #key.px.seatStatus
        self.features.append(int(baseLine > 0))         #key.px.seatPolarity
        self.features.append(1)                         #key.px.cableStatus
        self.features.append(0)                         #key.px.beltStatus
        self.features.append(int(seatBeltPolarity))     #key.px.beltPolarity
        self.features.append(baseLine)                  #key.px.baseLine
        self.features.append(baseLine)                  #key.px.currentValue
        self.features.append(T.D)                       #key.px.currentThreshold
        self.features.append(seatBeltCount)             #key.px.beltCount
        self.features.append(seatCount)                 #key.px.seatCount
        self.features.append(cableErrorCount)           #key.px.cableErrorCount
        self.features.append(calibrationCount)          #key.px.calibrationCount
        #have to be in order

        self.peakValue = 0
        self.referanceCounter = 0
        self.referanceCounterLimit = const(3)
    
    def Calibration(self, calb, val):
        self.features[key.px.currentValue] = val - self.features[key.px.baseLine]

        #calb |= (val < 30000)
        
        if self.features[key.px.seatStatus] == 0 or calb:
            if calb:
                self.features[key.px.calibrationCount] += 1 if self.features[key.px.calibrationStatus] == 0 else 0
                self.features[key.px.calibrationStatus] = 1

            if self.features[key.px.currentValue] < T.N:
                self.features[key.px.baseLine] = val
                self.referanceCounter = 0
                self.features[key.px.currentValue] = 0
            elif self.features[key.px.calibrationStatus] == 0:
                self.peakValue = self.features[key.px.currentValue] if self.peakValue < self.features[key.px.currentValue] else self.peakValue
                self.referanceCounter += 1 if self.referanceCounter < self.referanceCounterLimit else -self.referanceCounter
                if self.referanceCounter > (self.referanceCounterLimit >> 2) and self.peakValue < T.S:
                    self.features[key.px.baseLine] = val + T.S
                    self.features[key.px.currentValue] = 0
                if self.referanceCounter == 0 and self.peakValue < T.D:
                    self.features[key.px.baseLine] = val + self.peakValue
                    self.features[key.px.currentValue] = 0
                self.peakValue = 0 if self.referanceCounter == 0 else self.peakValue
            else:
                self.features[key.px.baseLine] = val if self.features[key.px.currentValue] >= (T.N >> 2) else self.features[key.px.baseLine]
                self.referanceCounter += 1 if self.features[key.px.currentValue] <= 0 and self.features[key.px.currentValue] >= T.N else -self.referanceCounter
                self.features[key.px.calibrationStatus] = 0 if self.referanceCounter > (self.referanceCounterLimit >> 1) else self.features[key.px.calibrationStatus]
                self.referanceCounter = 0 if self.features[key.px.calibrationStatus] == 0 else self.referanceCounter
        self.features[key.px.currentValue] = 0 if self.features[key.px.currentValue] < 0 or self.features[key.px.calibrationStatus] else self.features[key.px.currentValue]

    def Update(self, actv, belt, cabl): 
        if self.features[key.px.beltPolarity] != belt:
            self.features[key.px.beltCount] += 1 if self.features[key.px.beltStatus] == 0 else 0
            self.features[key.px.beltStatus] = 1
        else:
            self.features[key.px.beltStatus] = 0

        if actv == 0:
            self.features[key.px.seatStatus] = 0
            return None

        if cabl:
            self.features[key.px.cableErrorCount] += 1 if self.features[key.px.cableStatus] == 0 else 0
            self.features[key.px.cableStatus] = 1

            if self.features[key.px.currentValue] >= self.features[key.px.currentThreshold]:
                self.features[key.px.seatCount] += 1 if self.features[key.px.seatStatus] == 0 else 0
                self.features[key.px.seatStatus] = 1
            else:
                self.features[key.px.seatStatus] = 0
        else:
            self.features[key.px.cableStatus] = 0
            self.features[key.px.seatStatus] = 0


class PxHub():
    def __init__(self, data=None, sNo=int, json=dict(), dateTime=None) -> None:
        self.px1 = None
        self.px2 = None        
        self.features = list()

        self.resetCounterStatus = 0
        self.calibrationRequest = 0

        if json != dict():
            self.SetupFromJson(json=json)
        elif data != None:
            self.SetupFromRFData(data=data, sNo=sNo, dateTime=dateTime)
        else:
            pass #errorhandler

    def SetupFromRFData(self, data=None, sNo=int, dateTime=None):
        doubleSeat = int(((data[2] >> 0) & 0x01) & ((data[2] >> 1) & 0x01))
        px1sNo = px2sNo = sNo
        direction = (int((data[3] << 8) | data[4]) - int((data[11] << 8) | data[12])) >= (int((data[9] << 8) | data[10]) - int((data[17] << 8) | data[18]))

        if doubleSeat:
            if direction:
                px2sNo += 1
            else:
                px1sNo +=1 

        self.features.append(data[:2])
        if bool((data[2] >> 0) & 0x01):
            self.px1 = Px(seatNumber=px1sNo, calibrationStatus=True, seatBeltPolarity=bool((data[2] >> 2) & 0x01), baseLine=int((data[9] << 8) | data[10]), seatBeltCount=0, seatCount=0, cableErrorCount=0, calibrationCount=0)
            self.features.append(self.px1.features)
            sNo += 1
        else:
            self.features.append([])
        if bool((data[2] >> 1) & 0x01):
            self.px2 = Px(seatNumber=px2sNo, calibrationStatus=True, seatBeltPolarity=bool((data[2] >> 3) & 0x01), baseLine=int((data[17] << 8) | data[18]), seatBeltCount=0, seatCount=0, cableErrorCount=0, calibrationCount=0)
            self.features.append(self.px2.features)
        else:
            self.features.append([])

        self.features.append(dateTime)
        self.features.append(0)
        self.features.append(0)
        self.features.append(int((((data[2] >> 4) & 0x07) * 100) // 7))
        self.features.append(int(PXHUB_ESTIMATED_LIFETIME // self.features[key.hub.battery]) if self.features[key.hub.battery] != 0 else PXHUB_ESTIMATED_LIFETIME) #day
        self.features.append(doubleSeat)
        self.features.append(0)
        self.features.append(-int(data[21] // 2))
        #have to be in order

    def SetupFromJson(self, json=dict()):  

        self.features.append(str(json[key.hub.idNumber]).encode())
        if json[key.hub.px1] != []:
            self.px1 = Px(seatNumber=json[key.hub.px1][key.px.number], calibrationStatus=json[key.hub.px1][key.px.calibrationStatus], seatBeltPolarity=json[key.hub.px1][key.px.beltPolarity], baseLine=json[key.hub.px1][key.px.baseLine], seatBeltCount=json[key.hub.px1][key.px.beltCount], seatCount=json[key.hub.px1][key.px.seatCount], cableErrorCount=json[key.hub.px1][key.px.cableErrorCount], calibrationCount=json[key.hub.px1][key.px.calibrationCount])
            self.features.append(self.px1.features)
        else:
            self.features.append([])
        if json[key.hub.px2] != []:
            self.px2 = Px(seatNumber=json[key.hub.px2][key.px.number], calibrationStatus=json[key.hub.px2][key.px.calibrationStatus], seatBeltPolarity=json[key.hub.px2][key.px.beltPolarity], baseLine=json[key.hub.px2][key.px.baseLine], seatBeltCount=json[key.hub.px2][key.px.beltCount], seatCount=json[key.hub.px2][key.px.seatCount], cableErrorCount=json[key.hub.px2][key.px.cableErrorCount], calibrationCount=json[key.hub.px2][key.px.calibrationCount])
            self.features.append(self.px2.features)
        else:
            self.features.append([])

        self.features.append(json[key.hub.createTime])
        self.features.append(json[key.hub.dataCount])
        self.features.append(json[key.hub.resetCount])
        self.features.append(json[key.hub.battery])
        self.features.append(json[key.hub.lifeTime])
        self.features.append(json[key.hub.doubleSeat])
        self.features.append(json[key.hub.crcErrorCount])
        self.features.append(json[key.hub.rssi])

    def Process(self, data=None):
        if data == None:
            return None
        if data[:2] != self.features[key.hub.idNumber]:
            return None

        if bool(data[20] & 0x01):
            for x in range(4):
                if self.px1:
                    self.px1.Calibration(calb=self.calibrationRequest, val=int((data[ 3 + (x << 1)] << 8) | data[ 4 + (x << 1)]))
                if self.px2:
                    self.px2.Calibration(calb=self.calibrationRequest, val=int((data[11 + (x << 1)] << 8) | data[12 + (x << 1)]))

            self.Calibration()

            if self.px1:
                self.px1.Update(actv=not self.px1.features[key.px.calibrationStatus], belt=(data[2] >> 2) & 0x01, cabl=(data[2] >> 0) & 0x01)
            if self.px2:
                self.px2.Update(actv=not self.px2.features[key.px.calibrationStatus], belt=(data[2] >> 3) & 0x01, cabl=(data[2] >> 1) & 0x01)


            self.features[key.hub.dataCount] += 1
            self.features[key.hub.resetCount] += 1 if self.resetCounterStatus == False and bool((data[3] >> 7) & 0x01) else 0
            self.resetCounterStatus = bool((data[2] >> 7) & 0x01)
            self.features[key.hub.battery] = int((((data[2] >> 4) & 0x07)  * 100) // 7)
            self.features[key.hub.lifeTime] = int((PXHUB_ESTIMATED_LIFETIME * 100) // self.features[key.hub.battery]) if self.features[key.hub.battery] != 0 else self.features[key.hub.lifeTime]#day
            self.features[key.hub.rssi] = -int(data[21] // 2)
            self.calibrationRequest = False
        else:
            self.features[key.hub.crcErrorCount] += 1
            self.features[key.hub.rssi] = -(data[21] // 2)

        return True

    def Calibration(self):
        if self.features[key.hub.doubleSeat]:
            if self.px1.features[key.px.currentValue] > self.px2.features[key.px.currentValue] and self.px1.features[key.px.currentValue] > T.D:
                calc = int(self.px1.features[key.px.currentValue] * 0.4)
                self.px1.features[key.px.currentThreshold] = calc if self.px1.features[key.px.currentThreshold] < calc else self.px1.features[key.px.currentThreshold]
                self.px2.features[key.px.currentThreshold] = int(self.px1.features[key.px.currentThreshold] * 2)

            elif self.px2.features[key.px.currentValue] > self.px1.features[key.px.currentValue] and self.px2.features[key.px.currentValue] > T.D:
                calc = int(self.px2.features[key.px.currentValue] * 0.4)
                self.px2.features[key.px.currentThreshold] = calc if self.px2.features[key.px.currentThreshold] < calc else self.px2.features[key.px.currentThreshold]
                self.px1.features[key.px.currentThreshold] = int(self.px2.features[key.px.currentThreshold] * 2)

            self.px1.features[key.px.currentThreshold] = T.D if self.px1.features[key.px.currentThreshold] < T.D else self.px1.features[key.px.currentThreshold]
            self.px2.features[key.px.currentThreshold] = T.D if self.px2.features[key.px.currentThreshold] < T.D else self.px2.features[key.px.currentThreshold]

            if (self.px1.features[key.px.currentThreshold] != T.D and self.px1.features[key.px.currentValue] < self.px1.features[key.px.currentThreshold]) and \
               (self.px2.features[key.px.currentThreshold] != T.D and self.px2.features[key.px.currentValue] < self.px2.features[key.px.currentThreshold]):
                self.px1.features[key.px.baseLine] += self.px1.features[key.px.currentValue]
                self.px1.features[key.px.currentValue] = 0
                self.px2.features[key.px.baseLine] += self.px2.features[key.px.currentValue]
                self.px2.features[key.px.currentValue] = 0

            if (self.px1.features[key.px.currentValue] < T.D) and \
               (self.px2.features[key.px.currentValue] < T.D):
                self.px1.features[key.px.currentThreshold] = self.px2.features[key.px.currentThreshold] = T.D
        else:
            pxInstance = self.px1 if self.px1 else self.px2
            if pxInstance.features[key.px.currentValue] > T.D:
                calc = int(pxInstance.features[key.px.currentValue] * 0.4)
                pxInstance.features[key.px.currentThreshold] = calc if pxInstance.features[key.px.currentThreshold] < calc else pxInstance.features[key.px.currentThreshold]

            pxInstance.features[key.px.currentThreshold] = T.D if pxInstance.features[key.px.currentThreshold] < T.D else pxInstance.features[key.px.currentThreshold]

            if pxInstance.features[key.px.currentThreshold] != T.D and pxInstance.features[key.px.currentValue] < pxInstance.features[key.px.currentThreshold]:
                pxInstance.features[key.px.baseLine] += pxInstance.features[key.px.currentValue]
                pxInstance.features[key.px.currentValue] = 0

            if pxInstance.features[key.px.currentValue] < T.D:
                pxInstance.features[key.px.currentThreshold] = T.D

    def GetPassangerCount(self):
        c = 0
        if self.px1:
            c += self.px1.features[key.px.seatStatus]
        if self.px2:
            c += self.px2.features[key.px.seatStatus]
        return c