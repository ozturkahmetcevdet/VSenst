import gc
from micropython import const
from SX1239 import RF_COMING_DATA_SIZE


OPEN_SCENE_SHOW_TIME        = const(2500)
CLOSING_TIME                = const(10000)
CLOSE_SCENE_SHOW_TIME       = const(1000)
MAX_SEAT_NUMBER             = const(33)
PXHUB_ESTIMATED_LIFETIME    = const(1788) #day

RF_DATA_SIZE                = RF_COMING_DATA_SIZE

class Threshold:
    class SingleSeat:
        default = const(30)
        negative = const(-30)
        safe = const(10)
    class DoubleSeat:
        default = const(60)
        negative = const(-60)
        safe = const(20)

class Px():
    def __init__(self, seatNumber=int, seatBeltPolarity=bool, baseLine=int, seatBeltCount=int, passangerCount=int, cableErrorCount=int, calibrationCount=int, coorX=int, coorY=int, sizeOfPicture=int, safeValue=int, threshold=int, negativeThreshold=int) -> None:
        self.features = {                   \
            'number': seatNumber,           \
            'calbSt': int(True),            \
            'seatSt': int(False),           \
            'cablSt': int(False),           \
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
            'sizePc': sizeOfPicture         \
        }

        self.currentBeltValue = False
        self.currentProximityCableValue = False
        self.currentProximityValue = 0
        self.currentCalibrationValue = False

        self.referanceCounter = 0
        self.referanceCounterLimit = 4
    
    def Proceed(self, beltValue=bool, cableValue=bool, value=int, calibrationValue=bool):
        if self.features['active'] == False:
            return None

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
    def __init__(self, data=bytearray(RF_COMING_DATA_SIZE), lastSeatNumber=int, json=dict, coorJson=dict, dateTime=None) -> None:
        self.px1 = None
        self.px2 = None        
        
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
        }

        if json:
            self.SetupFromJson(json=json, coorJson=coorJson)
        elif data:
            self.SetupFromRFData(data=data, lastSeatNumber=lastSeatNumber, coorJson=coorJson, dateTime=dateTime)
        else:
            pass #errorhandler

    def SetupFromRFData(self, data=bytearray(RF_COMING_DATA_SIZE), lastSeatNumber=int, coorJson=dict, dateTime=None):   
        self.features['pHubID'] = data[0:3]
        doubleSeat = bool((data[3] >> 0) and 0x01) and bool((data[3] >> 1) and 0x01)

        if bool((data[3] >> 0) and 0x01):
            self.px1 = Px(seatNumber=lastSeatNumber+1, seatBeltPolarity=bool((data[3] >> 2) and 0x01), baseLine=int(((data[4] << 8) and 0xFF00) or data[5]), seatBeltCount=0, passangerCount=0, cableErrorCount=0, calibrationCount=0, coorX=coorJson[lastSeatNumber+1]['coordX'], coorY=coorJson[lastSeatNumber+1]['coordY'], sizeOfPicture=coorJson[lastSeatNumber+1]['sizePc'], safeValue=(Threshold.SingleSeat.safe if doubleSeat else Threshold.DoubleSeat.safe), threshold=(Threshold.SingleSeat.default if doubleSeat else Threshold.DoubleSeat.default), negativeThreshold=(Threshold.SingleSeat.negative if doubleSeat else Threshold.DoubleSeat.negative))
            self.features['proxS1'] = self.px1.features
        if bool((data[3] >> 1) and 0x01):
            self.px2 = Px(seatNumber=lastSeatNumber+2, seatBeltPolarity=bool((data[3] >> 3) and 0x01), baseLine=int(((data[6] << 8) and 0xFF00) or data[7]), seatBeltCount=0, passangerCount=0, cableErrorCount=0, calibrationCount=0, coorX=coorJson[lastSeatNumber+2]['coordX'], coorY=coorJson[lastSeatNumber+2]['coordY'], sizeOfPicture=coorJson[lastSeatNumber+2]['sizePc'], safeValue=(Threshold.SingleSeat.safe if doubleSeat else Threshold.DoubleSeat.safe), threshold=(Threshold.SingleSeat.default if doubleSeat else Threshold.DoubleSeat.default), negativeThreshold=(Threshold.SingleSeat.negative if doubleSeat else Threshold.DoubleSeat.negative))
            self.features['proxS2'] = self.px2.features

        self.features['crTime'] = dateTime
        self.features['cuTime'] = dateTime
        self.features['dataCo'] = 0
        self.features['rsetCo'] = 0
        self.features['batLvl'] = (data[3] >> 4) and 0x07
        self.features['esLife'] = int(PXHUB_ESTIMATED_LIFETIME // self.features['batLvl']) #day

    def SetupFromJson(self, json=dict, coorJson=dict, dateTime=None):   
        self.features['pHubID'] = json['pHubID']
        doubleSeat = json['proxS1'] and json['proxS2']

        if json['proxS1']:
            self.px1 = Px(seatNumber=json['proxS1']['number'], seatBeltPolarity=json['proxS1']['beltPo'], baseLine=json['proxS1']['baLine'], seatBeltCount=json['proxS1']['beltCo'], passangerCount=json['proxS1']['seatCo'], cableErrorCount=json['proxS1']['cablCo'], calibrationCount=json['proxS1']['calbCo'], coorX=coorJson[json['proxS1']['number']]['coordX'], coorY=coorJson[json['proxS1']['number']]['coordY'], sizeOfPicture=coorJson[json['proxS1']['number']]['sizePc'], safeValue=(Threshold.SingleSeat.safe if doubleSeat else Threshold.DoubleSeat.safe), threshold=(Threshold.SingleSeat.default if doubleSeat else Threshold.DoubleSeat.default), negativeThreshold=(Threshold.SingleSeat.negative if doubleSeat else Threshold.DoubleSeat.negative))
            self.features['proxS1'] = self.px1.features
        if json['proxS2']:
            self.px2 = Px(seatNumber=json['proxS2']['number'], seatBeltPolarity=json['proxS2']['beltPo'], baseLine=json['proxS2']['baLine'], seatBeltCount=json['proxS2']['beltCo'], passangerCount=json['proxS2']['seatCo'], cableErrorCount=json['proxS2']['cablCo'], calibrationCount=json['proxS2']['calbCo'], coorX=coorJson[json['proxS2']['number']]['coordX'], coorY=coorJson[json['proxS2']['number']]['coordY'], sizeOfPicture=coorJson[json['proxS2']['number']]['sizePc'], safeValue=(Threshold.SingleSeat.safe if doubleSeat else Threshold.DoubleSeat.safe), threshold=(Threshold.SingleSeat.default if doubleSeat else Threshold.DoubleSeat.default), negativeThreshold=(Threshold.SingleSeat.negative if doubleSeat else Threshold.DoubleSeat.negative))
            self.features['proxS2'] = self.px2.features

        self.features['crTime'] = json['crTime']
        self.features['cuTime'] = dateTime
        self.features['dataCo'] = json['dataCo']
        self.features['rsetCo'] = json['rsetCo']
        self.features['batLvl'] = json['batLvl']
        self.features['esLife'] = json['esLife']

    def Procees(self, data=bytearray(RF_COMING_DATA_SIZE), dateTime=None):
        if data[0:3] != self.features['pHubID']:
            return None

        self.features['cuTime'] = dateTime

        if self.px1:
            self.px1.Proceed(beltValue=(data[4] >> 2) and 0x01, cableValue=(data[4] >> 0) and 0x01, value=(data[5] << 8) or (data[6] << 0), calibrationValue=True)
        if self.px2:
            self.px2.Proceed(beltValue=(data[4] >> 3) and 0x01, cableValue=(data[4] >> 1) and 0x01, value=(data[7] << 8) or (data[8] << 0), calibrationValue=True)

        self.Calibration()
        self.Update()

    def Calibration(self):
        pass

    def Update(self):
        if self.px1:
            self.px1.Update(not self.px1.features['calbSt'])
        if self.px2:
            self.px2.Update(not self.px2.features['calbSt'])