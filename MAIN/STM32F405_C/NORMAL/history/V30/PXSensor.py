import gc
from micropython import const
from SX1239 import RF_COMING_DATA_SIZE
import binascii


OPEN_SCENE_SHOW_TIME        = const(2500)
CLOSING_TIME                = const(10000)
CLOSE_SCENE_SHOW_TIME       = const(1000)
MAX_SEAT_NUMBER             = const(33)
PXHUB_ESTIMATED_LIFETIME    = const(1788) #day

RF_DATA_SIZE                = RF_COMING_DATA_SIZE

class Threshold:
    singleSeatDefaultValue  = const( 30)
    singleSeatNegativeValue = const(-15)
    singleSeatSafeValue     = const( 10)
    doubleSeatDefaultValue  = const( 60)
    doubleSeatNegativeValue = const(-30)
    doubleSeatSafeValue     = const( 20)
    
class key:
    class px:
        number              = 'a'
        calibrationStatus   = 'b'
        seatStatus          = 'c'
        seatPolarity        = 'd'
        cableStatus         = 'e'
        beltStatus          = 'f'
        beltPolarity        = 'g'
        baseLine            = 'h'
        currentValue        = 'i'
        lastValue           = 'j'
        safeValue           = 'k'
        peakValue           = 'l'
        currentThreshold    = 'm'
        baseThreshold       = 'n'
        negativeThreshold   = 'o'
        beltCount           = 'p'
        seatCount           = 'r'
        cableErrorCount     = 's'
        calibrationCount    = 't'
    class hub:
        idNumber            = '0'
        px1                 = '1'
        px2                 = '2'
        createTime          = '3'
        currentTime         = '4'
        dataCount           = '5'
        resetCount          = '6'
        battery             = '7'
        lifeTime            = '8'
        doubleSeat          = '9'
        crcErrorCount       = 'x'


class Px():

    def __init__(self, seatNumber=int, calibrationStatus=bool, seatBeltPolarity=bool, baseLine=int, seatBeltCount=int, seatCount=int, cableErrorCount=int, calibrationCount=int, safeValue=int, threshold=int, negativeThreshold=int) -> None:
        self.features = {                                       \
            key.px.number: seatNumber,                          \
            key.px.calibrationStatus: int(calibrationStatus),   \
            key.px.seatStatus: int(False),                      \
            key.px.seatPolarity: int(baseLine > 0),             \
            key.px.cableStatus: int(True),                      \
            key.px.beltStatus: int(False),                      \
            key.px.beltPolarity: int(seatBeltPolarity),         \
            key.px.baseLine: baseLine,                          \
            key.px.currentValue: baseLine,                      \
            key.px.lastValue: baseLine,                         \
            key.px.safeValue: safeValue,                        \
            key.px.peakValue: 0,                                \
            key.px.currentThreshold: threshold,                 \
            key.px.baseThreshold: threshold,                    \
            key.px.negativeThreshold: negativeThreshold,        \
            key.px.beltCount: seatBeltCount,                    \
            key.px.seatCount: seatCount,                        \
            key.px.cableErrorCount: cableErrorCount,            \
            key.px.calibrationCount: calibrationCount           \
        }

        self.currentBeltValue = int(False)
        self.currentProximityCableValue = int(False)
        self.currentProximityValue = 0
        self.currentCalibrationValue = calibrationStatus

        self.referanceCounter = 0
        self.referanceCounterLimit = 4
    
    def Process(self, beltValue=bool, cableValue=bool, value=int, calibrationValue=bool):
        self.currentBeltValue = beltValue
        self.currentProximityCableValue = cableValue
        self.currentProximityValue = value
        self.currentCalibrationValue = calibrationValue or self.currentProximityValue < (self.features[key.px.baseLine] >> 3)

        self.Calibration()
    
    def Calibration(self):
        self.features[key.px.currentValue] = self.currentProximityValue - self.features[key.px.baseLine]
        
        if self.currentCalibrationValue:
            self.features[key.px.calibrationCount] += 1 if self.features[key.px.calibrationStatus] == False else 0
            self.features[key.px.calibrationStatus] = int(True)

        if self.features[key.px.currentValue] < self.features[key.px.negativeThreshold]:
            self.features[key.px.baseLine] = self.currentProximityValue
            self.referanceCounter = 0
            self.features[key.px.currentValue] = 0
        elif self.features[key.px.calibrationStatus] == False:
            self.features[key.px.peakValue] = self.features[key.px.currentValue] if self.features[key.px.peakValue] < self.features[key.px.currentValue] else self.features[key.px.peakValue]
            self.referanceCounter += 1 if self.referanceCounter < self.referanceCounterLimit else -self.referanceCounter
            if self.referanceCounter > (self.referanceCounterLimit >> 2) and self.features[key.px.peakValue] < self.features[key.px.safeValue]:
                self.features[key.px.baseLine] = self.currentProximityValue + self.features[key.px.safeValue]
                self.features[key.px.currentValue] = 0
            if self.referanceCounter == 0 and self.features[key.px.peakValue] < self.features[key.px.baseThreshold]:
                self.features[key.px.baseLine] = self.currentProximityValue + self.features[key.px.peakValue]
                self.features[key.px.currentValue] = 0
            self.features[key.px.peakValue] = 0 if self.referanceCounter == 0 else self.features[key.px.peakValue]
        else:
            self.features[key.px.baseLine] = self.currentProximityValue if self.features[key.px.currentValue] >= (self.features[key.px.negativeThreshold] >> 2) else self.features[key.px.baseLine]
            self.referanceCounter += 1 if self.features[key.px.currentValue] <= 0 and self.features[key.px.currentValue] >= self.features[key.px.negativeThreshold] else -self.referanceCounter
            self.features[key.px.calibrationStatus] = int(False) if self.referanceCounter > (self.referanceCounterLimit >> 2) else self.features[key.px.calibrationStatus]
            self.referanceCounter = 0 if self.features[key.px.calibrationStatus] == False else self.referanceCounter
        self.features[key.px.currentValue] = 0 if self.features[key.px.currentValue] < 0 or self.features[key.px.calibrationStatus] else self.features[key.px.currentValue]

    def Update(self, activity=False): 
        if self.features[key.px.beltPolarity] != self.currentBeltValue:
            self.features[key.px.beltCount] += 1 if self.features[key.px.beltStatus] == False else 0
            self.features[key.px.beltStatus] = int(True)
        else:
            self.features[key.px.beltStatus] = int(False)

        if activity == False:
            self.features[key.px.seatStatus] = int(False)
            return None

        if self.currentProximityCableValue:
            self.features[key.px.cableErrorCount] += 1 if self.features[key.px.cableStatus] == False else 0
            self.features[key.px.cableStatus] = int(True)

            if self.features[key.px.currentValue] >= self.features[key.px.currentThreshold]:
                self.features[key.px.seatCount] += 1 if self.features[key.px.seatStatus] == False else 0
                self.features[key.px.seatStatus] = int(True)
            else:
                self.features[key.px.seatStatus] = int(False)
        else:
            self.features[key.px.cableStatus] = int(False)
            self.features[key.px.seatStatus] = int(False)


class PxHub():
    def __init__(self, data=bytearray(RF_COMING_DATA_SIZE), lastSeatNumber=int, json=dict(), dateTime=None) -> None:
        self.px1 = None
        self.px2 = None        
        self.pxInstance = None
        
        self.features = {               \
            key.hub.idNumber: None,     \
            key.hub.px1: None,          \
            key.hub.px2: None,          \
            key.hub.createTime: None,   \
            key.hub.currentTime: None,  \
            key.hub.dataCount: None,    \
            key.hub.resetCount: None,   \
            key.hub.battery: None,      \
            key.hub.lifeTime: None,     \
            key.hub.doubleSeat: None,   \
            key.hub.crcErrorCount: None \
        }

        self.resetCounterStatus = int(False)
        self.calibrationRequest = int(False)

        if json != dict():
            self.SetupFromJson(json=json)
        elif data != bytearray(RF_COMING_DATA_SIZE):
            self.SetupFromRFData(data=data, lastSeatNumber=lastSeatNumber, dateTime=dateTime)
        else:
            pass #errorhandler

    def SetupFromRFData(self, data=bytearray(RF_COMING_DATA_SIZE), lastSeatNumber=int, dateTime=None):   
        self.features[key.hub.idNumber] = data[:3]
        doubleSeat = bool((data[3] >> 0) & 0x01) and bool((data[3] >> 1) & 0x01)

        if bool((data[3] >> 0) & 0x01):
            self.px1 = Px(seatNumber=lastSeatNumber, calibrationStatus=True, seatBeltPolarity=bool((data[3] >> 2) & 0x01), baseLine=int(((data[4] << 8) & 0xFF00) | ((data[5] << 0) & 0x00FF)), seatBeltCount=0, seatCount=0, cableErrorCount=0, calibrationCount=0, safeValue=(Threshold.doubleSeatSafeValue if doubleSeat else Threshold.singleSeatSafeValue), threshold=(Threshold.doubleSeatDefaultValue if doubleSeat else Threshold.singleSeatDefaultValue), negativeThreshold=(Threshold.doubleSeatNegativeValue if doubleSeat else Threshold.singleSeatNegativeValue))
            self.features[key.hub.px1] = self.px1.features
            lastSeatNumber += 1
        if bool((data[3] >> 1) & 0x01):
            self.px2 = Px(seatNumber=lastSeatNumber, calibrationStatus=True, seatBeltPolarity=bool((data[3] >> 3) & 0x01), baseLine=int(((data[6] << 8) & 0xFF00) | ((data[7] << 0) & 0x00FF)), seatBeltCount=0, seatCount=0, cableErrorCount=0, calibrationCount=0, safeValue=(Threshold.doubleSeatSafeValue if doubleSeat else Threshold.singleSeatSafeValue), threshold=(Threshold.doubleSeatDefaultValue if doubleSeat else Threshold.singleSeatDefaultValue), negativeThreshold=(Threshold.doubleSeatNegativeValue if doubleSeat else Threshold.singleSeatNegativeValue))
            self.features[key.hub.px2] = self.px2.features

        if not doubleSeat:
            self.pxInstance = self.px1 if self.px1 else self.px2

        self.features[key.hub.createTime] = dateTime
        self.features[key.hub.currentTime] = dateTime
        self.features[key.hub.dataCount] = 0
        self.features[key.hub.resetCount] = 0
        self.features[key.hub.battery] = int((((data[3] >> 4) & 0x07) * 100) // 7)
        self.features[key.hub.lifeTime] = int(PXHUB_ESTIMATED_LIFETIME // self.features[key.hub.battery]) #day
        self.features[key.hub.doubleSeat] = int(doubleSeat)

    def SetupFromJson(self, json=dict(), dateTime=None):  
        self.features[key.hub.idNumber] = str(json[key.hub.idNumber]).encode()
        doubleSeat = json[key.hub.px1] and json[key.hub.px2]

        if json[key.hub.px1]:
            self.px1 = Px(seatNumber=json[key.hub.px1][key.px.number], calibrationStatus=json[key.hub.px1][key.px.calibrationStatus], seatBeltPolarity=json[key.hub.px1][key.px.beltPolarity], baseLine=json[key.hub.px1][key.px.baseLine], seatBeltCount=json[key.hub.px1][key.px.beltCount], seatCount=json[key.hub.px1][key.px.seatCount], cableErrorCount=json[key.hub.px1][key.px.cableErrorCount], calibrationCount=json[key.hub.px1][key.px.calibrationCount], safeValue=(Threshold.doubleSeatSafeValue if doubleSeat else Threshold.singleSeatSafeValue), threshold=(Threshold.doubleSeatDefaultValue if doubleSeat else Threshold.singleSeatDefaultValue), negativeThreshold=(Threshold.doubleSeatNegativeValue if doubleSeat else Threshold.singleSeatNegativeValue))
            self.features[key.hub.px1] = self.px1.features
        if json[key.hub.px2]:
            self.px2 = Px(seatNumber=json[key.hub.px2][key.px.number], calibrationStatus=json[key.hub.px1][key.px.calibrationStatus], seatBeltPolarity=json[key.hub.px2][key.px.beltPolarity], baseLine=json[key.hub.px2][key.px.baseLine], seatBeltCount=json[key.hub.px2][key.px.beltCount], seatCount=json[key.hub.px2][key.px.seatCount], cableErrorCount=json[key.hub.px2][key.px.cableErrorCount], calibrationCount=json[key.hub.px2][key.px.calibrationCount], safeValue=(Threshold.doubleSeatSafeValue if doubleSeat else Threshold.singleSeatSafeValue), threshold=(Threshold.doubleSeatDefaultValue if doubleSeat else Threshold.singleSeatDefaultValue), negativeThreshold=(Threshold.doubleSeatNegativeValue if doubleSeat else Threshold.singleSeatNegativeValue))
            self.features[key.hub.px2] = self.px2.features

        if not doubleSeat:
            self.pxInstance = self.px1 if self.px1 else self.px2

        self.features[key.hub.createTime] = json[key.hub.createTime]
        self.features[key.hub.currentTime] = dateTime
        self.features[key.hub.dataCount] = json[key.hub.dataCount]
        self.features[key.hub.resetCount] = json[key.hub.resetCount]
        self.features[key.hub.battery] = json[key.hub.battery]
        self.features[key.hub.lifeTime] = json[key.hub.lifeTime]
        self.features[key.hub.doubleSeat] = int(doubleSeat)

    def Process(self, data=bytearray(RF_COMING_DATA_SIZE), dateTime=None): 
        if data[:3] != self.features[key.hub.idNumber]:
            return None

        if self.px1:
            self.px1.Process(beltValue=bool((data[3] >> 2) & 0x01), cableValue=bool((data[3] >> 0) & 0x01), value=int(((data[4] << 8) & 0xFF00) | ((data[5] << 0) & 0x00FF)), calibrationValue=self.calibrationRequest)
        if self.px2:
            self.px2.Process(beltValue=bool((data[3] >> 3) & 0x01), cableValue=bool((data[3] >> 1) & 0x01), value=int(((data[6] << 8) & 0xFF00) | ((data[7] << 0) & 0x00FF)), calibrationValue=self.calibrationRequest)

        self.features[key.hub.currentTime] = dateTime
        self.features[key.hub.dataCount] += 1
        self.features[key.hub.resetCount] += 1 if self.resetCounterStatus == False and bool((data[3] >> 7) & 0x01) else 0
        self.resetCounterStatus = bool((data[3] >> 7) & 0x01)
        self.features[key.hub.battery] = int((((data[3] >> 4) & 0x07)  * 100) // 7)
        self.features[key.hub.lifeTime] = int((PXHUB_ESTIMATED_LIFETIME * 100) // self.features[key.hub.battery]) #day

        self.Calibration()
        self.Update()

        self.calibrationRequest = False
        return True

    def Calibration(self):
        if self.features[key.hub.doubleSeat]:
            if self.px1.features[key.px.currentValue] > self.px2.features[key.px.currentValue] and self.px1.features[key.px.currentValue] > self.px1.features[key.px.baseThreshold]:
                calc = int(self.px1.features[key.px.currentValue] * 0.4)
                self.px1.features[key.px.currentThreshold] = calc if self.px1.features[key.px.currentThreshold] < calc else self.px1.features[key.px.currentThreshold]
                self.px2.features[key.px.currentThreshold] = int(self.px1.features[key.px.currentThreshold] * 2)
                
            elif self.px2.features[key.px.currentValue] > self.px1.features[key.px.currentValue] and self.px2.features[key.px.currentValue] > self.px2.features[key.px.baseThreshold]:
                calc = int(self.px2.features[key.px.currentValue] * 0.4)
                self.px2.features[key.px.currentThreshold] = calc if self.px2.features[key.px.currentThreshold] < calc else self.px2.features[key.px.currentThreshold]
                self.px1.features[key.px.currentThreshold] = int(self.px2.features[key.px.currentThreshold] * 2)

            self.px1.features[key.px.currentThreshold] = self.px1.features[key.px.baseThreshold] if self.px1.features[key.px.currentThreshold] < self.px1.features[key.px.baseThreshold] else self.px1.features[key.px.currentThreshold]
            self.px2.features[key.px.currentThreshold] = self.px2.features[key.px.baseThreshold] if self.px2.features[key.px.currentThreshold] < self.px2.features[key.px.baseThreshold] else self.px2.features[key.px.currentThreshold]

            if (self.px1.features[key.px.currentThreshold] != self.px1.features[key.px.baseThreshold] and self.px1.features[key.px.currentValue] < self.px1.features[key.px.currentThreshold]) and \
               (self.px2.features[key.px.currentThreshold] != self.px2.features[key.px.baseThreshold] and self.px2.features[key.px.currentValue] < self.px2.features[key.px.currentThreshold]):
                self.px1.features[key.px.baseLine] += self.px1.features[key.px.currentValue]
                self.px1.features[key.px.currentValue] = 0
                self.px2.features[key.px.baseLine] += self.px2.features[key.px.currentValue]
                self.px2.features[key.px.currentValue] = 0
                
            if (self.px1.features[key.px.currentValue] < self.px1.features[key.px.baseThreshold]) and \
               (self.px2.features[key.px.currentValue] < self.px2.features[key.px.baseThreshold]):
                self.px1.features[key.px.currentThreshold] = self.px1.features[key.px.baseThreshold]
                self.px2.features[key.px.currentThreshold] = self.px2.features[key.px.baseThreshold]
        else:
            if self.pxInstance.features[key.px.currentValue] > self.pxInstance.features[key.px.baseThreshold]:
                calc = int(self.pxInstance.features[key.px.currentValue] * 0.4)
                self.pxInstance.features[key.px.currentThreshold] = calc if self.pxInstance.features[key.px.currentThreshold] < calc else self.pxInstance.features[key.px.currentThreshold]

            self.pxInstance.features[key.px.currentThreshold] = self.pxInstance.features[key.px.baseThreshold] if self.pxInstance.features[key.px.currentThreshold] < self.pxInstance.features[key.px.baseThreshold] else self.pxInstance.features[key.px.currentThreshold]
                
            if self.pxInstance.features[key.px.currentThreshold] != self.pxInstance.features[key.px.baseThreshold] and self.pxInstance.features[key.px.currentValue] < self.pxInstance.features[key.px.currentThreshold]:
                self.pxInstance.features[key.px.baseLine] += self.pxInstance.features[key.px.currentValue]
                self.pxInstance.features[key.px.currentValue] = 0
            
            if self.pxInstance.features[key.px.currentValue] < self.pxInstance.features[key.px.baseThreshold]:
                self.pxInstance.features[key.px.currentThreshold] = self.pxInstance.features[key.px.baseThreshold]

    def Update(self):
        if self.px1:
            self.px1.Update(not self.px1.features[key.px.calibrationStatus])
        if self.px2:
            self.px2.Update(not self.px2.features[key.px.calibrationStatus])