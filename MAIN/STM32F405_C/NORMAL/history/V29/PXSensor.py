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

class Px():
    def __init__(self, seatNumber=int, calibrationStatus=bool, seatBeltPolarity=bool, baseLine=int, seatBeltCount=int, passangerCount=int, cableErrorCount=int, calibrationCount=int, coorX=int, coorY=int, picWidth=int, picHeight=int, safeValue=int, threshold=int, negativeThreshold=int) -> None:
        self.features = {                   \
            'number': seatNumber,           \
            'calbSt': calibrationStatus,    \
            'seatSt': int(False),           \
            'seatPo': bool(baseLine > 0),   \
            'cablSt': int(True),            \
            'beltSt': int(False),           \
            'beltPo': seatBeltPolarity,     \
            'baLine': baseLine,             \
            'pCuVal': baseLine,             \
            'pLaVal': baseLine,             \
            'pSaVal': safeValue,            \
            'pPeVal': 0,                    \
            'cuThrs': threshold,            \
            'baThrs': threshold,            \
            'neThrs': negativeThreshold,    \
            'beltCo': seatBeltCount,        \
            'seatCo': passangerCount,       \
            'cablCo': cableErrorCount,      \
            'calbCo': calibrationCount,     \
            'coordX': coorX,                \
            'coordY': coorY,                \
            'width_': picWidth,             \
            'height': picHeight,            \
            'coorEr': not coorX or not coorY or not picWidth or not picHeight \
        }

        self.currentBeltValue = False
        self.currentProximityCableValue = False
        self.currentProximityValue = 0
        self.currentCalibrationValue = calibrationStatus

        self.referanceCounter = 0
        self.referanceCounterLimit = 4
    
    def Process(self, beltValue=bool, cableValue=bool, value=int, calibrationValue=bool):
        self.currentBeltValue = beltValue
        self.currentProximityCableValue = cableValue
        self.currentProximityValue = value
        self.currentCalibrationValue = calibrationValue or self.currentProximityValue < (self.features['baLine'] >> 3)

        self.Calibration()
    
    def Calibration(self):
        self.features['pCuVal'] = self.currentProximityValue - self.features['baLine']
        
        if self.currentCalibrationValue:
            self.features['calbCo'] += 1 if self.features['calbSt'] == False else 0
            self.features['calbSt'] = True

        if self.features['pCuVal'] < self.features['neThrs']:
            self.features['baLine'] = self.currentProximityValue
            self.referanceCounter = 0
            self.features['pCuVal'] = 0
        elif self.features['calbSt'] == False:
            self.features['pPeVal'] = self.features['pCuVal'] if self.features['pPeVal'] < self.features['pCuVal'] else self.features['pPeVal']
            self.referanceCounter += 1 if self.referanceCounter < self.referanceCounterLimit else -self.referanceCounter
            if self.referanceCounter > (self.referanceCounterLimit >> 2) and self.features['pPeVal'] < self.features['pSaVal']:
                self.features['baLine'] = self.currentProximityValue + self.features['pSaVal']
                self.features['pCuVal'] = 0
            if self.referanceCounter == 0 and self.features['pPeVal'] < self.features['baThrs']:
                self.features['baLine'] = self.currentProximityValue + self.features['pPeVal']
                self.features['pCuVal'] = 0
            self.features['pPeVal'] = 0 if self.referanceCounter == 0 else self.features['pPeVal']
        else:
            self.features['baLine'] = self.currentProximityValue if self.features['pCuVal'] >= (self.features['neThrs'] >> 2) else self.features['baLine']
            self.referanceCounter += 1 if self.features['pCuVal'] <= 0 and self.features['pCuVal'] >= self.features['neThrs'] else -self.referanceCounter
            self.features['calbSt'] = False if self.referanceCounter > (self.referanceCounterLimit >> 2) else self.features['calbSt']
            self.referanceCounter = 0 if self.features['calbSt'] == False else self.referanceCounter
        self.features['pCuVal'] = 0 if self.features['pCuVal'] < 0 or self.features['calbSt'] else self.features['pCuVal']

    def Update(self, activity=False): 
        if self.features['beltPo'] != self.currentBeltValue:
            self.features['beltCo'] += 1 if self.features['beltSt'] == False else 0
            self.features['beltSt'] = True
        else:
            self.features['beltSt'] = False

        if activity == False:
            self.features['seatSt'] = False
            return None

        if self.currentProximityCableValue:
            self.features['cablCo'] += 1 if self.features['cablSt'] == False else 0
            self.features['cablSt'] = True

            if self.features['pCuVal'] >= self.features['cuThrs']:
                self.features['seatCo'] += 1 if self.features['seatSt'] == False else 0
                self.features['seatSt'] = True
            else:
                self.features['seatSt'] = False
        else:
            self.features['cablSt'] = False
            self.features['seatSt'] = False



class PxHub():
    def __init__(self, data=bytearray(RF_COMING_DATA_SIZE), lastSeatNumber=int, json=dict(), coorJson=dict(), dateTime=None) -> None:
        self.px1 = None
        self.px2 = None        
        self.pxInstance = None
        
        self.features = {   \
            'pHubID': None, \
            'proxS1': None, \
            'proxS2': None, \
            'crTime': None, \
            'cuTime': None, \
            'dataCo': None, \
            'rsetCo': None, \
            'batLvl': None, \
            'esLife': None, \
            'pHubDo': None  \
        }

        self.resetCounterStatus = False
        self.calibrationRequest = False

        if json != dict():
            self.SetupFromJson(json=json, coorJson=coorJson)
        elif data != bytearray(RF_COMING_DATA_SIZE):
            self.SetupFromRFData(data=data, lastSeatNumber=lastSeatNumber, coorJson=coorJson, dateTime=dateTime)
        else:
            pass #errorhandler

    def SetupFromRFData(self, data=bytearray(RF_COMING_DATA_SIZE), lastSeatNumber=int, coorJson=dict(), dateTime=None):   
        self.features['pHubID'] = data[:3]
        doubleSeat = bool((data[3] >> 0) & 0x01) and bool((data[3] >> 1) & 0x01)

        if bool((data[3] >> 0) & 0x01):
            self.px1 = Px(seatNumber=lastSeatNumber, calibrationStatus=True, seatBeltPolarity=bool((data[3] >> 2) & 0x01), baseLine=int(((data[4] << 8) & 0xFF00) | ((data[5] << 0) & 0x00FF)), seatBeltCount=0, passangerCount=0, cableErrorCount=0, calibrationCount=0, coorX=coorJson[str(lastSeatNumber+0)]['coordX'] if coorJson != dict() or coorJson != None else 0, coorY=coorJson[str(lastSeatNumber+0)]['coordY'] if coorJson != dict() or coorJson != None else 0, picWidth=coorJson[str(lastSeatNumber+0)]['width_'] if coorJson != dict() or coorJson != None else 0, picHeight=coorJson[str(lastSeatNumber+0)]['height'] if coorJson != dict() or coorJson != None else 0, safeValue=(Threshold.doubleSeatSafeValue if doubleSeat else Threshold.singleSeatSafeValue), threshold=(Threshold.doubleSeatDefaultValue if doubleSeat else Threshold.singleSeatDefaultValue), negativeThreshold=(Threshold.doubleSeatNegativeValue if doubleSeat else Threshold.singleSeatNegativeValue))
            self.features['proxS1'] = self.px1.features
            lastSeatNumber += 1
        if bool((data[3] >> 1) & 0x01):
            self.px2 = Px(seatNumber=lastSeatNumber, calibrationStatus=True, seatBeltPolarity=bool((data[3] >> 3) & 0x01), baseLine=int(((data[6] << 8) & 0xFF00) | ((data[7] << 0) & 0x00FF)), seatBeltCount=0, passangerCount=0, cableErrorCount=0, calibrationCount=0, coorX=coorJson[str(lastSeatNumber+1)]['coordX'] if coorJson != dict() or coorJson != None else 0, coorY=coorJson[str(lastSeatNumber+1)]['coordY'] if coorJson != dict() or coorJson != None else 0, picWidth=coorJson[str(lastSeatNumber+1)]['width_'] if coorJson != dict() or coorJson != None else 0, picHeight=coorJson[str(lastSeatNumber+1)]['height'] if coorJson != dict() or coorJson != None else 0, safeValue=(Threshold.doubleSeatSafeValue if doubleSeat else Threshold.singleSeatSafeValue), threshold=(Threshold.doubleSeatDefaultValue if doubleSeat else Threshold.singleSeatDefaultValue), negativeThreshold=(Threshold.doubleSeatNegativeValue if doubleSeat else Threshold.singleSeatNegativeValue))
            self.features['proxS2'] = self.px2.features

        if not doubleSeat:
            self.pxInstance = self.px1 if self.px1 else self.px2

        self.features['crTime'] = dateTime
        self.features['cuTime'] = dateTime
        self.features['dataCo'] = 0
        self.features['rsetCo'] = 0
        self.features['batLvl'] = int((((data[3] >> 4) & 0x07) * 100) // 7)
        self.features['esLife'] = int(PXHUB_ESTIMATED_LIFETIME // self.features['batLvl']) #day
        self.features['pHubDo'] = doubleSeat

    def SetupFromJson(self, json=dict(), coorJson=dict(), dateTime=None):  
        self.features['pHubID'] = str(json['pHubID']).encode()
        doubleSeat = json['proxS1'] and json['proxS2']

        if json['proxS1']:
            self.px1 = Px(seatNumber=json['proxS1']['number'], calibrationStatus=json['proxS1']['calbSt'], seatBeltPolarity=json['proxS1']['beltPo'], baseLine=json['proxS1']['baLine'], seatBeltCount=json['proxS1']['beltCo'], passangerCount=json['proxS1']['seatCo'], cableErrorCount=json['proxS1']['cablCo'], calibrationCount=json['proxS1']['calbCo'], coorX=coorJson[str(json['proxS1']['number'])]['coordX'] if coorJson != dict() else 0, coorY=coorJson[str(json['proxS1']['number'])]['coordY'] if coorJson != dict() else 0, picWidth=coorJson[str(json['proxS1']['number'])]['width_'] if coorJson != dict() else 0, picHeight=coorJson[str(json['proxS1']['number'])]['height'] if coorJson != dict() else 0, safeValue=(Threshold.doubleSeatSafeValue if doubleSeat else Threshold.singleSeatSafeValue), threshold=(Threshold.doubleSeatDefaultValue if doubleSeat else Threshold.singleSeatDefaultValue), negativeThreshold=(Threshold.doubleSeatNegativeValue if doubleSeat else Threshold.singleSeatNegativeValue))
            self.features['proxS1'] = self.px1.features
        if json['proxS2']:
            self.px2 = Px(seatNumber=json['proxS2']['number'], calibrationStatus=json['proxS1']['calbSt'], seatBeltPolarity=json['proxS2']['beltPo'], baseLine=json['proxS2']['baLine'], seatBeltCount=json['proxS2']['beltCo'], passangerCount=json['proxS2']['seatCo'], cableErrorCount=json['proxS2']['cablCo'], calibrationCount=json['proxS2']['calbCo'], coorX=coorJson[str(json['proxS2']['number'])]['coordX'] if coorJson != dict() else 0, coorY=coorJson[str(json['proxS2']['number'])]['coordY'] if coorJson != dict() else 0, picWidth=coorJson[str(json['proxS2']['number'])]['width_'] if coorJson != dict() else 0, picHeight=coorJson[str(json['proxS2']['number'])]['height'] if coorJson != dict() else 0, safeValue=(Threshold.doubleSeatSafeValue if doubleSeat else Threshold.singleSeatSafeValue), threshold=(Threshold.doubleSeatDefaultValue if doubleSeat else Threshold.singleSeatDefaultValue), negativeThreshold=(Threshold.doubleSeatNegativeValue if doubleSeat else Threshold.singleSeatNegativeValue))
            self.features['proxS2'] = self.px2.features

        if not doubleSeat:
            self.pxInstance = self.px1 if self.px1 else self.px2

        self.features['crTime'] = json['crTime']
        self.features['cuTime'] = dateTime
        self.features['dataCo'] = json['dataCo']
        self.features['rsetCo'] = json['rsetCo']
        self.features['batLvl'] = json['batLvl']
        self.features['esLife'] = json['esLife']
        self.features['pHubDo'] = doubleSeat

    def Process(self, data=bytearray(RF_COMING_DATA_SIZE), dateTime=None): 
        if data[:3] != self.features['pHubID']:
            return None

        if self.px1:
            self.px1.Process(beltValue=bool((data[3] >> 2) & 0x01), cableValue=bool((data[3] >> 0) & 0x01), value=int(((data[4] << 8) & 0xFF00) | ((data[5] << 0) & 0x00FF)), calibrationValue=self.calibrationRequest)
        if self.px2:
            self.px2.Process(beltValue=bool((data[3] >> 3) & 0x01), cableValue=bool((data[3] >> 1) & 0x01), value=int(((data[6] << 8) & 0xFF00) | ((data[7] << 0) & 0x00FF)), calibrationValue=self.calibrationRequest)

        self.features['cuTime'] = dateTime
        self.features['dataCo'] += 1
        self.features['rsetCo'] += 1 if self.resetCounterStatus == False and bool((data[3] >> 7) & 0x01) else 0
        self.resetCounterStatus = bool((data[3] >> 7) & 0x01)
        self.features['batLvl'] = int((((data[3] >> 4) & 0x07)  * 100) // 7)
        self.features['esLife'] = int((PXHUB_ESTIMATED_LIFETIME * 100) // self.features['batLvl']) #day
        print(((data[3] >> 4) & 0x07), self.features['batLvl'], self.features['esLife'])

        self.Calibration()
        self.Update()

        self.calibrationRequest = False
        return True

    def Calibration(self):
        if self.features['pHubDo']:
            if self.px1.features['pCuVal'] > self.px2.features['pCuVal'] and self.px1.features['pCuVal'] > self.px1.features['baThrs']:
                calc = int(self.px1.features['pCuVal'] * 0.4)
                self.px1.features['cuThrs'] = calc if self.px1.features['cuThrs'] < calc else self.px1.features['cuThrs']
                self.px2.features['cuThrs'] = int(self.px1.features['cuThrs'] * 2)
                
            elif self.px2.features['pCuVal'] > self.px1.features['pCuVal'] and self.px2.features['pCuVal'] > self.px2.features['baThrs']:
                calc = int(self.px2.features['pCuVal'] * 0.4)
                self.px2.features['cuThrs'] = calc if self.px2.features['cuThrs'] < calc else self.px2.features['cuThrs']
                self.px1.features['cuThrs'] = int(self.px2.features['cuThrs'] * 2)

            self.px1.features['cuThrs'] = self.px1.features['baThrs'] if self.px1.features['cuThrs'] < self.px1.features['baThrs'] else self.px1.features['cuThrs']
            self.px2.features['cuThrs'] = self.px2.features['baThrs'] if self.px2.features['cuThrs'] < self.px2.features['baThrs'] else self.px2.features['cuThrs']

            if (self.px1.features['cuThrs'] != self.px1.features['baThrs'] and self.px1.features['pCuVal'] < self.px1.features['cuThrs']) and \
               (self.px2.features['cuThrs'] != self.px2.features['baThrs'] and self.px2.features['pCuVal'] < self.px2.features['cuThrs']):
                self.px1.features['baLine'] += self.px1.features['pCuVal']
                self.px1.features['pCuVal'] = 0
                self.px2.features['baLine'] += self.px2.features['pCuVal']
                self.px2.features['pCuVal'] = 0
                
            if (self.px1.features['pCuVal'] < self.px1.features['baThrs']) and \
               (self.px2.features['pCuVal'] < self.px2.features['baThrs']):
                self.px1.features['cuThrs'] = self.px1.features['baThrs']
                self.px2.features['cuThrs'] = self.px2.features['baThrs']
        else:
            if self.pxInstance.features['pCuVal'] > self.pxInstance.features['baThrs']:
                calc = int(self.pxInstance.features['pCuVal'] * 0.4)
                self.pxInstance.features['cuThrs'] = calc if self.pxInstance.features['cuThrs'] < calc else self.pxInstance.features['cuThrs']

            self.pxInstance.features['cuThrs'] = self.pxInstance.features['baThrs'] if self.pxInstance.features['cuThrs'] < self.pxInstance.features['baThrs'] else self.pxInstance.features['cuThrs']
                
            if self.pxInstance.features['cuThrs'] != self.pxInstance.features['baThrs'] and self.pxInstance.features['pCuVal'] < self.pxInstance.features['cuThrs']:
                self.pxInstance.features['baLine'] += self.pxInstance.features['pCuVal']
                self.pxInstance.features['pCuVal'] = 0
            
            if self.pxInstance.features['pCuVal'] < self.pxInstance.features['baThrs']:
                self.pxInstance.features['cuThrs'] = self.pxInstance.features['baThrs']

    def Update(self):
        if self.px1:
            self.px1.Update(not self.px1.features['calbSt'])
        if self.px2:
            self.px2.Update(not self.px2.features['calbSt'])