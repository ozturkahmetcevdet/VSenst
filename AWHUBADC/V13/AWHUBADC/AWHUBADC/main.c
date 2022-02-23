#include <atmel_start.h>
#include <avr/interrupt.h>
#include <avr/sleep.h>
#include <stdio.h>
#include <util/delay.h>
#include <avr/io.h>
#include <QTouchADC.h>
#include <SX1243.h>
#include <rstctrl.h>

#define B_STYLE (1)

#if B_STYLE == (1)
uint8_t Const_In_PSD1 = 0, 
		Const_In_PSD2 = 0;
#endif

//ATtiny817
/********************************************************************************************************************/
/* 2600mAh Battery life time for current regulation ~4,9 years @512ms - @1024 - @2048  periods, SampleCount:32>>0  */
/********************************************************************************************************************/

//Others:
//2600mAh Battery life time for current regulation ~4,9 years @512ms - @1024 - @2048  periods, SampleCount:32>>0
//2600mAh Battery life time for full active ~4,6 years @1024ms period, SampleCount:32>>0
//2600mAh Battery life time for full active ~2,3 years @512ms  period, SampleCount:32>>0
//2600mAh Battery life time for full active ~3,8 years @1024ms period, SampleCount:64>>0
//2600mAh Battery life time for full active ~1,9 years @512ms  period, SampleCount:64>>0

uint16_t loopCycle = 0;
#define SAMPLE_COUNT		 64   // 2^SAMPLE_CONSTANT
#define SAMPLE_DIVIDER		 0    // SAMPLE_CONSTANT >> 1
#define SAMPLE_MULTIPLIER	 1    // SAMPLE_CONSTANT >> 1
#define TRANSMIT_COUNT		 16
#define DATA_CHANGE_CONSTANT 10
#define DATA_REFRESH_TIME	 300  // second / 2 = 10 minutes
#define SENSOR_ACTIVITY_DEBONCE 5//10 - 10dk 345 count
#define SENSE_CALIBRATION_COUNT 12
#define DEFAULT_SENSE_CALIBRATION_THRESHOLD 100
#define MAX_SENSE_CALIBRATION_THRESHOLD 160
#define MAX_CONTINUES_CALIBRATION_THRESHOLD 60
#define MAX_CONTINUES_CALIBRATION_THRESHOLD_COUNTER_LIMIT 1
#define MIN_CONTINUES_CALIBRATION_THRESHOLD 20
#define MIN_CONTINUES_CALIBRATION_THRESHOLD_COUNTER_LIMIT 1

uint8_t payloadBuffer[27] = {
	0xAA, 0xAA,										//Preamble						-->    2 byte
	0x1E, 0xAA, 0X55, 0XE1,							//Sync Word						-->    4 byte
	0x00, 0x00,										//MCU UID						-->    2 byte
    0x00, 0x00,										//Config I/O - Battery etc..	-->    2 byte
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,	//px1 packet					-->  2*4 byte
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,	//px2 packet					-->  2*4 byte
	0x00											//CRC							-->    1 byte
};													//Total							-->   30 byte
const uint8_t payloadBufferStartByte = 6;
bool payloadReady = false;
uint8_t payloadCounter = 0;
uint8_t payloadCounterUNCHANGE = 0;

uint8_t seatFlagStatus;

uint8_t repeatDataCounter = TRANSMIT_COUNT;
bool isDataChanged = false;
uint16_t dataRefreshCounter = DATA_REFRESH_TIME;
uint8_t startupDelay = 10;

typedef struct QTOUCHADC_REFERANCE_FILTER
{
	bool Activity;
	bool Calibrate;
	bool SenseCalibrate;
	uint8_t ActivityCounter;
	uint8_t SenseCalibrateCounter;
	uint8_t SenseCalibrateFaultCounter;
	uint8_t Counter;
	uint8_t CounterLimit;
	uint8_t ContinuesMinReferance;
	uint8_t ContinuesMinReferanceCounter;
	bool ContinuesMinReferanceCounterLock;
	uint8_t ContinuesMaxReferance;
	uint8_t ContinuesMaxReferanceCounter;
	bool ContinuesMaxReferanceCounterLock;
	uint8_t AlphaDivider;
	uint8_t AlphaMultiplier;
	uint16_t LoopCycle;
	uint16_t LoopCycleMin;
	uint32_t PeakValue;
	uint32_t BaseLine;
	uint32_t RawValue;
	uint32_t LastRawValue;
	uint32_t MaxRawValue;
	uint32_t RawAdc;
	int32_t NegativeThreshold;
	int32_t FilterValue;
	int32_t CurrentValue;
	int32_t CurrentMaxValue; 
}QTOUCHADC_REFERANCE_FILTER;

QTOUCHADC_REFERANCE_FILTER QTOUCHADC_REFERANCE_FILTER_P[2] = {{.Activity = true, .LoopCycle = SAMPLE_COUNT, .AlphaDivider = 2, .AlphaMultiplier = 3, .CounterLimit = 6, .FilterValue = 10, .NegativeThreshold = -30, .Calibrate = true, .SenseCalibrate = true, .MaxRawValue = 0},
															  {.Activity = true, .LoopCycle = SAMPLE_COUNT, .AlphaDivider = 2, .AlphaMultiplier = 3, .CounterLimit = 6, .FilterValue = 10, .NegativeThreshold = -30, .Calibrate = true, .SenseCalibrate = true, .MaxRawValue = 0}};
//ATtiny817

//////////////////////////////////////////////////////////////////////////
// 1 means 1uAh
// Full battery capacity is 2700mAH - 2700000uAh
// Formula: (current capacity / full capacity) * 100; 
//////////////////////////////////////////////////////////////////////////
#define BAT_SLEEP_CONSTANT		80				// 30u(A/sn) @1024ms
#define BAT_ADC_CONSTANT		57				// 20u(A/sn) @1024ms
#define BAT_TRANSMIT_CONSTANT   16				// 21u(A/sn) @1024ms
#define BAT_FULL_CAPACITY		9360000000		// uAs
#define BAT_CALCULATE_REFRESH_CONSTANT 86400	// ~24 hour

uint64_t BatteryLevelCounter = BAT_FULL_CAPACITY;
uint32_t BatteryLevelCalculateCounter = BAT_CALCULATE_REFRESH_CONSTANT + 1;
uint8_t batVar = 0;


#define GET_PERIODIC_TIMER_VALUE(x) (x + 0x07) << 3 //@ 0x08 --> 512ms start address
enum TimeSequence
{
	T_256  = 0,
	T_2048 = 3
};

uint8_t sleepTimeSequence = T_2048;

void ConfigPIT(uint8_t timeSequence)
{
	RTC.PITCTRLA = timeSequence 
	| 1 << RTC_PITEN_bp;
	RTC.PITINTFLAGS = RTC_PI_bm;
}

int main(void)
{
	atmel_start_init();
	
	batVar = FLASH_0_read_eeprom_byte(0);
	batVar = batVar > 6 ? 7 : batVar;
	BatteryLevelCounter = ((uint64_t)((float)BatteryLevelCounter * (float)batVar)) >> 3;
	
	DATA_set_level(false);
	
	payloadBuffer[payloadBufferStartByte + 0] = SIGROW_SERNUM8;
	payloadBuffer[payloadBufferStartByte + 1] = SIGROW_SERNUM9;
	SX1243Init(&payloadBuffer[0], sizeof(payloadBuffer), payloadBufferStartByte);
	
	while(true) 
	{
		#if B_STYLE == (0)
		BatteryLevelCounter -= ((QTOUCHADC_REFERANCE_FILTER_P[0].LoopCycle + QTOUCHADC_REFERANCE_FILTER_P[1].LoopCycle) >> (sleepTimeSequence + 1));
		#endif
		
		if (BatteryLevelCalculateCounter > BAT_CALCULATE_REFRESH_CONSTANT)
		{
			double var = (double)BatteryLevelCounter / (double)BAT_FULL_CAPACITY;
			batVar = (uint8_t)(var * 9.0f);
			batVar = batVar > 6 ? 7 : batVar;
			FLASH_0_write_eeprom_byte(0, batVar);
			BatteryLevelCalculateCounter = 0;
			RSTCTRL_clear_reset_cause();
		}
		BatteryLevelCalculateCounter++;
		
		SB1_set_pull_mode(PORT_PULL_UP);
		SB2_set_pull_mode(PORT_PULL_UP);
		PSD1_set_pull_mode(PORT_PULL_UP);
		PSD2_set_pull_mode(PORT_PULL_UP);
		
		SB1_set_dir(PORT_DIR_IN);
		SB2_set_dir(PORT_DIR_IN);
		PSD1_set_dir(PORT_DIR_IN);
		PSD2_set_dir(PORT_DIR_IN);
		
		uint8_t In_SB1  = !SB1_get_level();
		uint8_t In_SB2  = !SB2_get_level();
		uint8_t	In_PSD1 = !PSD1_get_level();
		uint8_t In_PSD2 = !PSD2_get_level();
		
		#if B_STYLE == (1)
		uint8_t IOFilterCounter = 100;
		while(IOFilterCounter--)
		{
			In_SB1  += !SB1_get_level();
			In_SB2  += !SB2_get_level();
			In_PSD1 += !PSD1_get_level();
			In_PSD2 += !PSD2_get_level();
		}
		In_SB1 = In_SB1 > 75;
		In_SB2 = In_SB2 > 75;
		In_PSD1 = In_PSD1 > 75;
		In_PSD2 = In_PSD2 > 75;
		#endif
		
		if(!In_PSD1)
		{
			QTOUCHADC_REFERANCE_FILTER_P[0].ActivityCounter++;
			if(QTOUCHADC_REFERANCE_FILTER_P[0].ActivityCounter >= SENSOR_ACTIVITY_DEBONCE)
			{
				QTOUCHADC_REFERANCE_FILTER_P[0].Activity = false;
				QTOUCHADC_REFERANCE_FILTER_P[0].CurrentValue = 0;
				QTOUCHADC_REFERANCE_FILTER_P[0].Calibrate = false;
			}
		}
		else if(QTOUCHADC_REFERANCE_FILTER_P[0].ActivityCounter || !QTOUCHADC_REFERANCE_FILTER_P[0].Activity)
		{
			QTOUCHADC_REFERANCE_FILTER_P[0].ActivityCounter = 0;
			QTOUCHADC_REFERANCE_FILTER_P[0].Activity = true;
			QTOUCHADC_REFERANCE_FILTER_P[0].Calibrate = QTOUCHADC_REFERANCE_FILTER_P[1].Calibrate = true;
			//QTOUCHADC_REFERANCE_FILTER_P[0].SenseCalibrate = QTOUCHADC_REFERANCE_FILTER_P[1].SenseCalibrate = true;
		}
		
		if(!In_PSD2)
		{
			QTOUCHADC_REFERANCE_FILTER_P[1].ActivityCounter++;
			if(QTOUCHADC_REFERANCE_FILTER_P[1].ActivityCounter >= SENSOR_ACTIVITY_DEBONCE)
			{
				QTOUCHADC_REFERANCE_FILTER_P[1].Activity = false;
				QTOUCHADC_REFERANCE_FILTER_P[1].CurrentValue = 0;
				QTOUCHADC_REFERANCE_FILTER_P[1].Calibrate = false;
			}
		}
		else if(QTOUCHADC_REFERANCE_FILTER_P[1].ActivityCounter || !QTOUCHADC_REFERANCE_FILTER_P[1].Activity)
		{
			QTOUCHADC_REFERANCE_FILTER_P[1].ActivityCounter = 0;
			QTOUCHADC_REFERANCE_FILTER_P[1].Activity = true;
			QTOUCHADC_REFERANCE_FILTER_P[0].Calibrate = QTOUCHADC_REFERANCE_FILTER_P[1].Calibrate = true;
			//QTOUCHADC_REFERANCE_FILTER_P[0].SenseCalibrate = QTOUCHADC_REFERANCE_FILTER_P[1].SenseCalibrate = true;
		}
		//ATtiny817
		
		#if B_STYLE == (1)
		Const_In_PSD1 |= In_PSD1;
		Const_In_PSD2 |= In_PSD2;
		#endif
		
		SB1_set_pull_mode(PORT_PULL_OFF);
		SB2_set_pull_mode(PORT_PULL_OFF);
		PSD1_set_pull_mode(PORT_PULL_OFF);
		PSD2_set_pull_mode(PORT_PULL_OFF);
		
		SB1_set_level(false);
		SB2_set_level(false);
		PSD1_set_level(false);
		PSD2_set_level(false);
		
		SB1_set_dir(PORT_DIR_OUT);
		SB2_set_dir(PORT_DIR_OUT);
		PSD1_set_dir(PORT_DIR_OUT);
		PSD2_set_dir(PORT_DIR_OUT);
		
		#if B_STYLE == (0)
		QTOUCH_GetSensorValue(0, true);
		
		for(uint8_t j = 0; j < 2; j++)
		{
			if(!QTOUCHADC_REFERANCE_FILTER_P[j].Activity)
				continue;
			
			loopCycle = QTOUCHADC_REFERANCE_FILTER_P[j].LoopCycle;
			QTOUCHADC_REFERANCE_FILTER_P[j].RawAdc = 0;
			while(--loopCycle)
			{
				QTOUCHADC_REFERANCE_FILTER_P[j].RawAdc += QTOUCH_GetSensorValue(j, false) - QTOUCH_GetSensorValue(j, true);
				_delay_loop_1(3);
			}
			
			QTOUCHADC_REFERANCE_FILTER_P[j].RawValue  = (QTOUCHADC_REFERANCE_FILTER_P[j].RawValue  >> QTOUCHADC_REFERANCE_FILTER_P[j].AlphaDivider) * QTOUCHADC_REFERANCE_FILTER_P[j].AlphaMultiplier +
														((QTOUCHADC_REFERANCE_FILTER_P[j].RawAdc << SAMPLE_MULTIPLIER) >> (SAMPLE_DIVIDER + QTOUCHADC_REFERANCE_FILTER_P[j].AlphaDivider));
			
			QTOUCHADC_REFERANCE_FILTER_P[j].CurrentValue = QTOUCHADC_REFERANCE_FILTER_P[j].RawValue - QTOUCHADC_REFERANCE_FILTER_P[j].BaseLine;
			QTOUCHADC_REFERANCE_FILTER_P[j].CurrentMaxValue = QTOUCHADC_REFERANCE_FILTER_P[j].CurrentMaxValue < QTOUCHADC_REFERANCE_FILTER_P[j].CurrentValue ? QTOUCHADC_REFERANCE_FILTER_P[j].CurrentValue : QTOUCHADC_REFERANCE_FILTER_P[j].CurrentMaxValue;
			
			if(QTOUCHADC_REFERANCE_FILTER_P[j].CurrentValue < QTOUCHADC_REFERANCE_FILTER_P[j].FilterValue)
			{
				QTOUCHADC_REFERANCE_FILTER_P[j].ContinuesMaxReferanceCounterLock = false;
			}
			else if(QTOUCHADC_REFERANCE_FILTER_P[j].CurrentValue > MAX_CONTINUES_CALIBRATION_THRESHOLD)
			{				
				QTOUCHADC_REFERANCE_FILTER_P[j].ContinuesMinReferanceCounterLock = false;
			}
			
			if(QTOUCHADC_REFERANCE_FILTER_P[j].CurrentValue < (int32_t)(QTOUCHADC_REFERANCE_FILTER_P[j].CurrentMaxValue * 0.6f) && QTOUCHADC_REFERANCE_FILTER_P[j].CurrentValue > 0)
			{
				QTOUCHADC_REFERANCE_FILTER_P[j].BaseLine = QTOUCHADC_REFERANCE_FILTER_P[j].RawValue;
				QTOUCHADC_REFERANCE_FILTER_P[j].CurrentValue = QTOUCHADC_REFERANCE_FILTER_P[j].CurrentMaxValue = 0;
			}
			//ATtiny817
			else if(QTOUCHADC_REFERANCE_FILTER_P[j].CurrentValue < QTOUCHADC_REFERANCE_FILTER_P[j].NegativeThreshold)
			{
				QTOUCHADC_REFERANCE_FILTER_P[j].BaseLine = QTOUCHADC_REFERANCE_FILTER_P[j].RawValue;
				QTOUCHADC_REFERANCE_FILTER_P[j].Counter = 0;
				QTOUCHADC_REFERANCE_FILTER_P[j].CurrentValue = 0;
			}
			else if(!QTOUCHADC_REFERANCE_FILTER_P[j].Calibrate)
			{					
				QTOUCHADC_REFERANCE_FILTER_P[j].PeakValue = (QTOUCHADC_REFERANCE_FILTER_P[j].PeakValue < QTOUCHADC_REFERANCE_FILTER_P[j].CurrentValue) && (QTOUCHADC_REFERANCE_FILTER_P[j].CurrentValue > 0) ? QTOUCHADC_REFERANCE_FILTER_P[j].CurrentValue : QTOUCHADC_REFERANCE_FILTER_P[j].PeakValue;
				QTOUCHADC_REFERANCE_FILTER_P[j].Counter += QTOUCHADC_REFERANCE_FILTER_P[j].Counter < QTOUCHADC_REFERANCE_FILTER_P[j].CounterLimit ? 1 : -QTOUCHADC_REFERANCE_FILTER_P[j].Counter;
				QTOUCHADC_REFERANCE_FILTER_P[j].ContinuesMaxReferance = QTOUCHADC_REFERANCE_FILTER_P[j].PeakValue;
				QTOUCHADC_REFERANCE_FILTER_P[j].ContinuesMinReferance = QTOUCHADC_REFERANCE_FILTER_P[j].ContinuesMinReferance > QTOUCHADC_REFERANCE_FILTER_P[j].CurrentValue ? QTOUCHADC_REFERANCE_FILTER_P[j].CurrentValue : QTOUCHADC_REFERANCE_FILTER_P[j].ContinuesMinReferance;
				
				if(QTOUCHADC_REFERANCE_FILTER_P[j].CounterLimit == 0)
				{
					if(QTOUCHADC_REFERANCE_FILTER_P[j].ContinuesMaxReferance <= MAX_CONTINUES_CALIBRATION_THRESHOLD && !QTOUCHADC_REFERANCE_FILTER_P[j].ContinuesMaxReferanceCounterLock)
					{
						QTOUCHADC_REFERANCE_FILTER_P[j].ContinuesMaxReferanceCounter++;
						QTOUCHADC_REFERANCE_FILTER_P[j].ContinuesMaxReferanceCounterLock = true;
					}
					else if(QTOUCHADC_REFERANCE_FILTER_P[j].ContinuesMaxReferance >= DEFAULT_SENSE_CALIBRATION_THRESHOLD)
					{
						QTOUCHADC_REFERANCE_FILTER_P[j].ContinuesMaxReferanceCounter = 0;
					}
					
					if(QTOUCHADC_REFERANCE_FILTER_P[j].ContinuesMinReferance >= MIN_CONTINUES_CALIBRATION_THRESHOLD && !QTOUCHADC_REFERANCE_FILTER_P[j].ContinuesMinReferanceCounterLock)
					{
						QTOUCHADC_REFERANCE_FILTER_P[j].ContinuesMinReferanceCounter++;
						QTOUCHADC_REFERANCE_FILTER_P[j].ContinuesMinReferanceCounterLock = true;
					}
					else if(QTOUCHADC_REFERANCE_FILTER_P[j].ContinuesMinReferance < QTOUCHADC_REFERANCE_FILTER_P[j].FilterValue)
					{
						QTOUCHADC_REFERANCE_FILTER_P[j].ContinuesMinReferanceCounter = 0;
					}
				}
				
				if(QTOUCHADC_REFERANCE_FILTER_P[j].ContinuesMaxReferanceCounter > MAX_CONTINUES_CALIBRATION_THRESHOLD_COUNTER_LIMIT)
				{
					QTOUCHADC_REFERANCE_FILTER_P[j].LoopCycle += 1;
					QTOUCHADC_REFERANCE_FILTER_P[j].ContinuesMaxReferanceCounter = 0;
					QTOUCHADC_REFERANCE_FILTER_P[j].ContinuesMinReferanceCounter = 0;
				}
				if(QTOUCHADC_REFERANCE_FILTER_P[j].ContinuesMinReferanceCounter > MIN_CONTINUES_CALIBRATION_THRESHOLD_COUNTER_LIMIT)
				{
					QTOUCHADC_REFERANCE_FILTER_P[j].LoopCycle -= 1;
					QTOUCHADC_REFERANCE_FILTER_P[j].ContinuesMaxReferanceCounter = 0;
					QTOUCHADC_REFERANCE_FILTER_P[j].ContinuesMinReferanceCounter = 0;
				}
				
				//if (QTOUCHADC_REFERANCE_FILTER_P[j].Counter == 0 && QTOUCHADC_REFERANCE_FILTER_P[j].PeakValue < QTOUCHADC_REFERANCE_FILTER_P[j].FilterValue)
				//{
					//QTOUCHADC_REFERANCE_FILTER_P[j].BaseLine = QTOUCHADC_REFERANCE_FILTER_P[j].RawValue + QTOUCHADC_REFERANCE_FILTER_P[j].FilterValue;
					//QTOUCHADC_REFERANCE_FILTER_P[j].CurrentValue = 0;
				//}
				//else if(QTOUCHADC_REFERANCE_FILTER_P[j].Counter == 0 && !QTOUCHADC_REFERANCE_FILTER_P[j].SenseCalibrate && QTOUCHADC_REFERANCE_FILTER_P[j].PeakValue > (MAX_SENSE_CALIBRATION_THRESHOLD * 10))
				//{
					//QTOUCHADC_REFERANCE_FILTER_P[j].SenseCalibrate = true;
				//}
				if (QTOUCHADC_REFERANCE_FILTER_P[j].SenseCalibrate && QTOUCHADC_REFERANCE_FILTER_P[j].CurrentValue > DEFAULT_SENSE_CALIBRATION_THRESHOLD)
				{
					if(QTOUCHADC_REFERANCE_FILTER_P[j].PeakValue > DEFAULT_SENSE_CALIBRATION_THRESHOLD || QTOUCHADC_REFERANCE_FILTER_P[j].MaxRawValue != 0)
					{
						QTOUCHADC_REFERANCE_FILTER_P[j].SenseCalibrateFaultCounter = 0;
						if(QTOUCHADC_REFERANCE_FILTER_P[j].MaxRawValue < QTOUCHADC_REFERANCE_FILTER_P[j].PeakValue)
						{
							QTOUCHADC_REFERANCE_FILTER_P[j].MaxRawValue = QTOUCHADC_REFERANCE_FILTER_P[j].PeakValue;
							QTOUCHADC_REFERANCE_FILTER_P[j].SenseCalibrateCounter = SENSE_CALIBRATION_COUNT;
						}
						else if(QTOUCHADC_REFERANCE_FILTER_P[j].SenseCalibrateCounter)
						{
							QTOUCHADC_REFERANCE_FILTER_P[j].SenseCalibrateCounter--;
							if(!QTOUCHADC_REFERANCE_FILTER_P[j].SenseCalibrateCounter)
							{
								float temp = QTOUCHADC_REFERANCE_FILTER_P[j].LoopCycle;
								int16_t nTemp = QTOUCHADC_REFERANCE_FILTER_P[j].MaxRawValue;
								uint16_t expC = 0;
								
								while(nTemp > 0)
								{
									nTemp -= DEFAULT_SENSE_CALIBRATION_THRESHOLD;
									expC++;
								}
								
								QTOUCHADC_REFERANCE_FILTER_P[0].LoopCycle		= QTOUCHADC_REFERANCE_FILTER_P[1].LoopCycle = (uint16_t)((temp * (float)DEFAULT_SENSE_CALIBRATION_THRESHOLD) / (QTOUCHADC_REFERANCE_FILTER_P[j].MaxRawValue)) + (expC >> 1);
								QTOUCHADC_REFERANCE_FILTER_P[0].SenseCalibrate	= QTOUCHADC_REFERANCE_FILTER_P[1].SenseCalibrate = false;
								QTOUCHADC_REFERANCE_FILTER_P[0].MaxRawValue		= QTOUCHADC_REFERANCE_FILTER_P[1].MaxRawValue = 0;
								QTOUCHADC_REFERANCE_FILTER_P[0].Calibrate		= QTOUCHADC_REFERANCE_FILTER_P[1].Calibrate = true;
								if(QTOUCHADC_REFERANCE_FILTER_P[j].LoopCycle < QTOUCHADC_REFERANCE_FILTER_P[j].LoopCycleMin)
								{
									QTOUCHADC_REFERANCE_FILTER_P[j].LoopCycle = QTOUCHADC_REFERANCE_FILTER_P[j].LoopCycleMin;
								}
								if(QTOUCHADC_REFERANCE_FILTER_P[j].LoopCycleMin == 0x00)
								{
									QTOUCHADC_REFERANCE_FILTER_P[j].LoopCycleMin = (uint16_t)(QTOUCHADC_REFERANCE_FILTER_P[j].LoopCycle *0.8f);
								}
							}
						}
					}
					else if (QTOUCHADC_REFERANCE_FILTER_P[j].PeakValue < DEFAULT_SENSE_CALIBRATION_THRESHOLD && QTOUCHADC_REFERANCE_FILTER_P[j].PeakValue != 0)
					{
						QTOUCHADC_REFERANCE_FILTER_P[j].SenseCalibrateFaultCounter++;
						if(QTOUCHADC_REFERANCE_FILTER_P[j].SenseCalibrateFaultCounter > 9)
						{
							QTOUCHADC_REFERANCE_FILTER_P[j].SenseCalibrateFaultCounter = 0;
							QTOUCHADC_REFERANCE_FILTER_P[j].LoopCycle += 5;
						}
					}
				}
				else if(QTOUCHADC_REFERANCE_FILTER_P[j].SenseCalibrate)
				{
					QTOUCHADC_REFERANCE_FILTER_P[j].MaxRawValue = 0;
					QTOUCHADC_REFERANCE_FILTER_P[j].SenseCalibrateCounter = SENSE_CALIBRATION_COUNT;
				}
				QTOUCHADC_REFERANCE_FILTER_P[j].PeakValue = QTOUCHADC_REFERANCE_FILTER_P[j].ContinuesMaxReferance = QTOUCHADC_REFERANCE_FILTER_P[j].ContinuesMinReferance = QTOUCHADC_REFERANCE_FILTER_P[j].Counter == 0 ? 0 : QTOUCHADC_REFERANCE_FILTER_P[j].PeakValue;
			}
			else
			{
				QTOUCHADC_REFERANCE_FILTER_P[j].BaseLine = QTOUCHADC_REFERANCE_FILTER_P[j].CurrentValue >= QTOUCHADC_REFERANCE_FILTER_P[j].NegativeThreshold ? QTOUCHADC_REFERANCE_FILTER_P[j].RawValue : QTOUCHADC_REFERANCE_FILTER_P[j].BaseLine;
				QTOUCHADC_REFERANCE_FILTER_P[j].Counter += (QTOUCHADC_REFERANCE_FILTER_P[j].CurrentValue <= 0 && QTOUCHADC_REFERANCE_FILTER_P[j].CurrentValue >= QTOUCHADC_REFERANCE_FILTER_P[j].NegativeThreshold) ? 1 : -QTOUCHADC_REFERANCE_FILTER_P[j].Counter;
				QTOUCHADC_REFERANCE_FILTER_P[j].Calibrate = QTOUCHADC_REFERANCE_FILTER_P[j].Counter > (QTOUCHADC_REFERANCE_FILTER_P[j].CounterLimit >> 1) ? false : QTOUCHADC_REFERANCE_FILTER_P[j].Calibrate;
				QTOUCHADC_REFERANCE_FILTER_P[j].Counter = QTOUCHADC_REFERANCE_FILTER_P[j].Calibrate == false ? 0 : QTOUCHADC_REFERANCE_FILTER_P[j].Counter;
			}
			QTOUCHADC_REFERANCE_FILTER_P[j].CurrentValue = QTOUCHADC_REFERANCE_FILTER_P[j].CurrentValue < 0 ? 0 : QTOUCHADC_REFERANCE_FILTER_P[j].CurrentValue;//QTOUCHADC_REFERANCE_FILTER_P[j].LoopCycle;//
			
			if(QTOUCHADC_REFERANCE_FILTER_P[j].LastRawValue > DATA_CHANGE_CONSTANT)
			{
				isDataChanged |= QTOUCHADC_REFERANCE_FILTER_P[j].RawValue > (QTOUCHADC_REFERANCE_FILTER_P[j].LastRawValue + DATA_CHANGE_CONSTANT) || QTOUCHADC_REFERANCE_FILTER_P[j].RawValue < (QTOUCHADC_REFERANCE_FILTER_P[j].LastRawValue - DATA_CHANGE_CONSTANT);
			}
			QTOUCHADC_REFERANCE_FILTER_P[j].LastRawValue = QTOUCHADC_REFERANCE_FILTER_P[j].RawValue;
		}
		#else
		QTOUCHADC_REFERANCE_FILTER_P[0].CurrentValue = In_PSD1 * 200 * Const_In_PSD1;
		isDataChanged |= QTOUCHADC_REFERANCE_FILTER_P[0].RawValue != QTOUCHADC_REFERANCE_FILTER_P[0].CurrentValue;
		QTOUCHADC_REFERANCE_FILTER_P[0].RawValue = QTOUCHADC_REFERANCE_FILTER_P[0].CurrentValue;
		
		QTOUCHADC_REFERANCE_FILTER_P[1].CurrentValue = In_PSD2 * 200 * Const_In_PSD2;
		isDataChanged |= QTOUCHADC_REFERANCE_FILTER_P[1].RawValue != QTOUCHADC_REFERANCE_FILTER_P[1].CurrentValue;
		QTOUCHADC_REFERANCE_FILTER_P[1].RawValue = QTOUCHADC_REFERANCE_FILTER_P[1].CurrentValue;
		#endif
		//ATtiny817
		//isDataChanged = true;
		
		#if B_STYLE == (0)
		isDataChanged |= (payloadBuffer[payloadBufferStartByte + 2] != (seatFlagStatus = (((RSTCTRL.RSTFR > 0) << 7) & 0x80) | ((batVar << 4) & 0x70) | ((((In_SB2 << 3) & 0x08) | ((In_SB1 << 2) & 0x04) | ((In_PSD2       << 1) & 0x02) | ((In_PSD1       << 0) & 0x01)) & 0x0F)));
		isDataChanged |= (payloadBuffer[payloadBufferStartByte + 3] != QTOUCHADC_REFERANCE_FILTER_P[0].LoopCycle);
		isDataChanged = QTOUCHADC_REFERANCE_FILTER_P[0].Calibrate || QTOUCHADC_REFERANCE_FILTER_P[1].Calibrate ? false : isDataChanged;	
		#else
		isDataChanged |= (payloadBuffer[payloadBufferStartByte + 2] != (seatFlagStatus = (((RSTCTRL.RSTFR > 0) << 7) & 0x80) | ((batVar << 4) & 0x70) | ((((In_SB2 << 3) & 0x08) | ((In_SB1 << 2) & 0x04) | ((Const_In_PSD2 << 1) & 0x02) | ((Const_In_PSD1 << 0) & 0x01)) & 0x0F)));
		#endif
			
		repeatDataCounter = (isDataChanged && (repeatDataCounter <= (TRANSMIT_COUNT >> 1))) || (dataRefreshCounter == 0) ? TRANSMIT_COUNT : repeatDataCounter;
		dataRefreshCounter -= (dataRefreshCounter > 0) && (repeatDataCounter == 0) ? 1 : DATA_REFRESH_TIME;
		isDataChanged = false;		
		
		if(repeatDataCounter && payloadReady == false)
		{
			if (payloadCounterUNCHANGE > 2)
			{
				payloadBuffer[payloadBufferStartByte +  4 + payloadCounter] = (uint8_t)((QTOUCHADC_REFERANCE_FILTER_P[0].CurrentValue >> 8) & 0x00FF);
				payloadBuffer[payloadBufferStartByte +  5 + payloadCounter] = (uint8_t)((QTOUCHADC_REFERANCE_FILTER_P[0].CurrentValue >> 0) & 0x00FF);
				payloadBuffer[payloadBufferStartByte + 12 + payloadCounter] = (uint8_t)((QTOUCHADC_REFERANCE_FILTER_P[1].CurrentValue >> 8) & 0x00FF);
				payloadBuffer[payloadBufferStartByte + 13 + payloadCounter] = (uint8_t)((QTOUCHADC_REFERANCE_FILTER_P[1].CurrentValue >> 0) & 0x00FF);
				
				payloadCounter += payloadCounter < 6 ? 2 : -payloadCounter;
				payloadReady = 	payloadCounter == 0 ? true : payloadReady;
			}
			payloadCounterUNCHANGE += payloadCounterUNCHANGE < 6 ? 1 : -payloadCounterUNCHANGE;
		}
		
		if(startupDelay == 0 && payloadReady)
		{
			payloadBuffer[payloadBufferStartByte +  2] = seatFlagStatus;
			payloadBuffer[payloadBufferStartByte +  3] = QTOUCHADC_REFERANCE_FILTER_P[0].LoopCycle;
			payloadBuffer[payloadBufferStartByte + 20] = SX1243CRC8(&payloadBuffer[payloadBufferStartByte + 2]);
			
			bool transmitterStatus = SX1243Process() == SX_OK;
			repeatDataCounter -= transmitterStatus ? 1 : -1;
			payloadReady = transmitterStatus ? false : payloadReady;
			BatteryLevelCounter -= (BAT_TRANSMIT_CONSTANT >> sleepTimeSequence);
		}
		
		if(startupDelay == 0)
		{
			set_sleep_mode(SLEEP_MODE_PWR_DOWN);
			cli();
			sleepTimeSequence = repeatDataCounter >= 0 ? T_256 : T_2048;
			ConfigPIT(GET_PERIODIC_TIMER_VALUE(sleepTimeSequence));
			
			sleep_enable();
			sei();
			sleep_cpu();
			sleep_disable();
			cli();
			BatteryLevelCounter -= (BAT_SLEEP_CONSTANT >> sleepTimeSequence);
		}
		
		CBT_set_dir(PORT_DIR_IN);
		if(CBT_get_level() == false)
		{
			uint8_t timeOut = 100;
			while(CBT_get_level() == false && --timeOut)
			{
				_delay_ms(50);
				DATA_toggle_level();
			}
			if(timeOut < 1)
			{
				FLASH_0_write_eeprom_byte(0, 100);
				while (NVMCTRL.STATUS & NVMCTRL_EEBUSY_bm);
				_delay_ms(5);
			}
			RSTCTRL_reset();
		}
		CBT_set_dir(PORT_DIR_OFF);
		
		startupDelay -= startupDelay > 0;
	}
}

//ATtiny817
/********************************************************************************************************************/
/* 2600mAh Battery life time for current regulation ~4,9 years @512ms - @1024 - @2048  periods, SampleCount:32>>0  */
/********************************************************************************************************************/

//Others:
//2600mAh Battery life time for current regulation ~4,9 years @512ms - @1024 - @2048  periods, SampleCount:32>>0
//2600mAh Battery life time for full active ~4,6 years @1024ms period, SampleCount:32>>0
//2600mAh Battery life time for full active ~2,3 years @512ms  period, SampleCount:32>>0
//2600mAh Battery life time for full active ~3,8 years @1024ms period, SampleCount:64>>0
//2600mAh Battery life time for full active ~1,9 years @512ms  period, SampleCount:64>>0