
MAX_SEAT_NUMBER = 33

class DataBase():
    class SeatConfig:
        MaxNumber = MAX_SEAT_NUMBER
        CurrentNumber = 33
    class Sensor:
        Threshold = 31
        PositiveTolerance = 25
        NegativeTolerance = 5
        ID = [bytearray(10)] * MAX_SEAT_NUMBER

    def __init__(self):
        super().__init__()
     