#include <atmel_start.h>
#include <avr/sleep.h>
#include <stdio.h>
#include <util/delay.h>
#include <avr/io.h>
#include <tiny_qtouch_adc.h>
#include <SX1243.h>
#include <rstctrl.h>

uint8_t payloadBuffer[16] = {
	0xAA, 0xAA,
	0x1E, 0xAA, 0x55, 0xE1,
	0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00
};
const uint8_t payloadBufferStartByte = 6;


uint8_t prox1CounterBase[2] = {0};
uint8_t prox2CounterBase[2] = {0};
uint8_t seatFlagStatus[2];

uint8_t repeatDataCounter = 20;
bool isDataChanged = false;

#define SAMPLE_CONSTANT 6 // this for information
#define SAMPLE_COUNT 64   // 2^SAMPLE_CONSTANT
#define SAMPLE_DIVIDER 1  // SAMPLE_CONSTANT >> 1

typedef struct  
{
	bool Enable;
	uint8_t Counter;
	int32_t CurrentValue;
	int32_t MaxValue;
	int32_t PeakValue;
	uint8_t CounterLimit;
	int16_t FilterValue;
	int16_t EdgeValue;
	int32_t ADCReferance;
	int32_t NegativeThreshold;
	bool Calibrate;
	int32_t RawValue;
	int32_t RawAdc;
	uint16_t LoopCycle;
	uint8_t AlphaDivider;
	uint8_t AlphaMultiplier;
}QTOUCHADC_REFERANCE_FILTER;

QTOUCHADC_REFERANCE_FILTER QTOUCHADC_REFERANCE_FILTER_P[2] = {{.Enable = true, .Counter = 0, .CurrentValue = 0, .MaxValue = 0, .PeakValue = 0, .CounterLimit = 1, .FilterValue = 10, .EdgeValue = 50, .ADCReferance = 0, .NegativeThreshold = -10, .Calibrate = true, .AlphaDivider = 2, .AlphaMultiplier = 3},
															  {.Enable = true, .Counter = 0, .CurrentValue = 0, .MaxValue = 0, .PeakValue = 0, .CounterLimit = 1, .FilterValue = 10, .EdgeValue = 50, .ADCReferance = 0, .NegativeThreshold = -10, .Calibrate = true, .AlphaDivider = 2, .AlphaMultiplier = 3}};

//////////////////////////////////////////////////////////////////////////
// 1 means 5uAh
// Full battery capacity is 2700mAH - 2700000uAh
// Formula: (current capacity / full capacity) * 100; 
//////////////////////////////////////////////////////////////////////////
#define BAT_SLEEP_CONSTANT		55				// 30nAsn
#define BAT_ADC_CONSTANT		3				//  5uAsn
#define BAT_TRANSMIT_CONSTANT   7				// 10uAsn
#define BAT_FULL_CAPACITY		2600000000		// nAh
#define BAT_CALCULATE_REFRESH_CONSTANT 86400	// 24 hour

uint64_t BatteryLevelCounter = BAT_FULL_CAPACITY;
uint32_t BatteryLevelCalculateCounter = BAT_CALCULATE_REFRESH_CONSTANT + 1;
uint8_t batVar = 0;

int main(void)
{
	/* Initializes MCU, drivers and middleware */
	atmel_start_init();
	
	batVar = FLASH_0_read_eeprom_byte(0);
	BatteryLevelCounter *= batVar > 100 ? 1 : (((float)batVar) / 100.0f);  
	
	DATA_set_level(false);
	CBT_set_isc(PORT_ISC_BOTHEDGES_gc);
	
	bool sensorState = false;
	uint8_t timeOut = 10;
	uint8_t debounce = 5;
	while(--timeOut)
	{
		if(/*!PSD1_get_level() && !PSD2_get_level()*/true)
		{
			sensorState = debounce == 0;
			debounce -= debounce > 0;
		}
		else
			debounce = 5;
	}
	QTOUCHADC_REFERANCE_FILTER_P[0].FilterValue		  *= sensorState ? 2 : 1;
	QTOUCHADC_REFERANCE_FILTER_P[0].NegativeThreshold *= sensorState ? 2 : 1;
	QTOUCHADC_REFERANCE_FILTER_P[0].EdgeValue		  *= sensorState ? 2 : 1;
	QTOUCHADC_REFERANCE_FILTER_P[1].FilterValue		  *= sensorState ? 2 : 1;
	QTOUCHADC_REFERANCE_FILTER_P[1].NegativeThreshold *= sensorState ? 2 : 1;
	QTOUCHADC_REFERANCE_FILTER_P[1].EdgeValue		  *= sensorState ? 2 : 1;
	
	
	payloadBuffer[payloadBufferStartByte + 0] = SIGROW_SERNUM7;
	payloadBuffer[payloadBufferStartByte + 1] = SIGROW_SERNUM8;
	payloadBuffer[payloadBufferStartByte + 2] = SIGROW_SERNUM9;
	SX1243Init(&payloadBuffer[0], sizeof(payloadBuffer), payloadBufferStartByte);
	
	

	/* Replace with your application code */
	while (1) 
	{
		BatteryLevelCounter -= BAT_ADC_CONSTANT;
		
		SB1_set_pull_mode(PORT_PULL_UP);
		SB2_set_pull_mode(PORT_PULL_UP);
		PSD1_set_pull_mode(PORT_PULL_UP);
		PSD2_set_pull_mode(PORT_PULL_UP);
		
		uint8_t In_SB1  = !SB1_get_level();
		uint8_t In_SB2  = !SB2_get_level();
		uint8_t	In_PSD1 = true;//!PSD1_get_level();
		uint8_t In_PSD2 = true;//!PSD2_get_level();
		
		SB1_set_pull_mode(PORT_PULL_OFF);
		SB2_set_pull_mode(PORT_PULL_OFF);
		PSD1_set_pull_mode(PORT_PULL_OFF);
		PSD2_set_pull_mode(PORT_PULL_OFF);
		
		//ADC ENABLE
		ADC_0_enable();
		TOUCH_GetSensorValue(0, false);
		
		/*************************************************************************************************/
		/* KALKMA ANINDA OLUÞAN GEÇÝKME ÝÇÝN IRR FILTRE DEÐERLERÝ OTOMATÝK GÜNCELLENEN YAZILIM YAPILACAK */
		/*************************************************************************************************/
		
		for(uint8_t j = 0; j < 2; j++)
		{
			QTOUCHADC_REFERANCE_FILTER_P[j].LoopCycle = SAMPLE_COUNT;
			QTOUCHADC_REFERANCE_FILTER_P[j].RawAdc = 0;
			while(--QTOUCHADC_REFERANCE_FILTER_P[j].LoopCycle)
			{
				QTOUCHADC_REFERANCE_FILTER_P[j].RawAdc += TOUCH_GetSensorValue(j, false) - TOUCH_GetSensorValue(j, true);
			}
			QTOUCHADC_REFERANCE_FILTER_P[j].RawValue  = (QTOUCHADC_REFERANCE_FILTER_P[j].RawValue  >> QTOUCHADC_REFERANCE_FILTER_P[j].AlphaDivider) * QTOUCHADC_REFERANCE_FILTER_P[j].AlphaMultiplier + 
														(QTOUCHADC_REFERANCE_FILTER_P[j].RawAdc    >> (SAMPLE_DIVIDER + QTOUCHADC_REFERANCE_FILTER_P[j].AlphaDivider));

			if(QTOUCHADC_REFERANCE_FILTER_P[j].Enable)
			{
				QTOUCHADC_REFERANCE_FILTER_P[j].CurrentValue = QTOUCHADC_REFERANCE_FILTER_P[j].RawValue - QTOUCHADC_REFERANCE_FILTER_P[j].ADCReferance;
				
				/*if(QTOUCHADC_REFERANCE_FILTER_P[j].CurrentValue >= QTOUCHADC_REFERANCE_FILTER_P[j].EdgeValue)
				{
					QTOUCHADC_REFERANCE_FILTER_P[j].ADCReferance = QTOUCHADC_REFERANCE_FILTER_P[j].RawValue - QTOUCHADC_REFERANCE_FILTER_P[j].EdgeValue;
					QTOUCHADC_REFERANCE_FILTER_P[j].Counter = 0;
					QTOUCHADC_REFERANCE_FILTER_P[j].CurrentValue = QTOUCHADC_REFERANCE_FILTER_P[j].RawValue - QTOUCHADC_REFERANCE_FILTER_P[j].ADCReferance;
					QTOUCHADC_REFERANCE_FILTER_P[j].CurrentValue = QTOUCHADC_REFERANCE_FILTER_P[j].CurrentValue < 0 ? 0 : QTOUCHADC_REFERANCE_FILTER_P[j].CurrentValue;
					
					QTOUCHADC_REFERANCE_FILTER_P[j == 0 ? 1 : 0].ADCReferance += (QTOUCHADC_REFERANCE_FILTER_P[j].EdgeValue >> 1);
					QTOUCHADC_REFERANCE_FILTER_P[j == 0 ? 1 : 0].Counter = 0;
					QTOUCHADC_REFERANCE_FILTER_P[j == 0 ? 1 : 0].CurrentValue = QTOUCHADC_REFERANCE_FILTER_P[j == 0 ? 1 : 0].RawValue - QTOUCHADC_REFERANCE_FILTER_P[j == 0 ? 1 : 0].ADCReferance;
					QTOUCHADC_REFERANCE_FILTER_P[j == 0 ? 1 : 0].CurrentValue = QTOUCHADC_REFERANCE_FILTER_P[j == 0 ? 1 : 0].CurrentValue < 0 ? 0 : QTOUCHADC_REFERANCE_FILTER_P[j == 0 ? 1 : 0].CurrentValue;
				}*/
				if(QTOUCHADC_REFERANCE_FILTER_P[j].CurrentValue < QTOUCHADC_REFERANCE_FILTER_P[j].NegativeThreshold)
				{
					QTOUCHADC_REFERANCE_FILTER_P[j].ADCReferance = QTOUCHADC_REFERANCE_FILTER_P[j].RawValue;
					QTOUCHADC_REFERANCE_FILTER_P[j].Counter = 0;
					QTOUCHADC_REFERANCE_FILTER_P[j].CurrentValue = 0;
				}
				else if(!QTOUCHADC_REFERANCE_FILTER_P[j].Calibrate)
				{					
					QTOUCHADC_REFERANCE_FILTER_P[j].PeakValue = QTOUCHADC_REFERANCE_FILTER_P[j].PeakValue < QTOUCHADC_REFERANCE_FILTER_P[j].CurrentValue ? QTOUCHADC_REFERANCE_FILTER_P[j].CurrentValue : QTOUCHADC_REFERANCE_FILTER_P[j].PeakValue;
					QTOUCHADC_REFERANCE_FILTER_P[j].Counter += QTOUCHADC_REFERANCE_FILTER_P[j].Counter < QTOUCHADC_REFERANCE_FILTER_P[j].CounterLimit ? 1 : -QTOUCHADC_REFERANCE_FILTER_P[j].Counter;
					if (QTOUCHADC_REFERANCE_FILTER_P[j].Counter == 0 && QTOUCHADC_REFERANCE_FILTER_P[j].PeakValue < QTOUCHADC_REFERANCE_FILTER_P[j].FilterValue)
					{
						QTOUCHADC_REFERANCE_FILTER_P[j].ADCReferance = QTOUCHADC_REFERANCE_FILTER_P[j].RawValue + QTOUCHADC_REFERANCE_FILTER_P[j].FilterValue;
						QTOUCHADC_REFERANCE_FILTER_P[j].CurrentValue = 0;
					}
					QTOUCHADC_REFERANCE_FILTER_P[j].PeakValue = QTOUCHADC_REFERANCE_FILTER_P[j].Counter == 0 ? 0 : QTOUCHADC_REFERANCE_FILTER_P[j].PeakValue;
				}
				else
				{
					QTOUCHADC_REFERANCE_FILTER_P[j].ADCReferance = QTOUCHADC_REFERANCE_FILTER_P[j].CurrentValue >= QTOUCHADC_REFERANCE_FILTER_P[j].NegativeThreshold ? QTOUCHADC_REFERANCE_FILTER_P[j].RawValue : QTOUCHADC_REFERANCE_FILTER_P[j].ADCReferance;
					QTOUCHADC_REFERANCE_FILTER_P[j].Counter += (QTOUCHADC_REFERANCE_FILTER_P[j].CurrentValue <= 0 && QTOUCHADC_REFERANCE_FILTER_P[j].CurrentValue >= QTOUCHADC_REFERANCE_FILTER_P[j].NegativeThreshold) ? 1 : -QTOUCHADC_REFERANCE_FILTER_P[j].Counter;
					QTOUCHADC_REFERANCE_FILTER_P[j].Calibrate = QTOUCHADC_REFERANCE_FILTER_P[j].Counter > (QTOUCHADC_REFERANCE_FILTER_P[j].CounterLimit << 3) ? false : QTOUCHADC_REFERANCE_FILTER_P[j].Calibrate;
					QTOUCHADC_REFERANCE_FILTER_P[j].Counter = QTOUCHADC_REFERANCE_FILTER_P[j].Calibrate == false ? 0 : QTOUCHADC_REFERANCE_FILTER_P[j].Counter;
				}
			}
			QTOUCHADC_REFERANCE_FILTER_P[j].CurrentValue = QTOUCHADC_REFERANCE_FILTER_P[j].CurrentValue < 0 ? 0 : QTOUCHADC_REFERANCE_FILTER_P[j].CurrentValue;
		}
		//ADC DISABLE
		ADC_0_disable();
		
		if(!QTOUCHADC_REFERANCE_FILTER_P[0].Calibrate && !QTOUCHADC_REFERANCE_FILTER_P[1].Calibrate)
		{
			prox1CounterBase[1] = (uint8_t)((QTOUCHADC_REFERANCE_FILTER_P[0].CurrentValue >> 8) & 0x00FF);
			prox1CounterBase[0] = (uint8_t)((QTOUCHADC_REFERANCE_FILTER_P[0].CurrentValue >> 0) & 0x00FF);
			prox2CounterBase[1] = (uint8_t)((QTOUCHADC_REFERANCE_FILTER_P[1].CurrentValue >> 8) & 0x00FF);
			prox2CounterBase[0] = (uint8_t)((QTOUCHADC_REFERANCE_FILTER_P[1].CurrentValue >> 0) & 0x00FF);
			
		
			if (BatteryLevelCalculateCounter > BAT_CALCULATE_REFRESH_CONSTANT)
			{
				batVar = (uint8_t)((uint64_t)(BatteryLevelCounter * 100) / (uint64_t)BAT_FULL_CAPACITY);
				FLASH_0_write_eeprom_byte(0, batVar);
				BatteryLevelCalculateCounter = 0;
			}
			BatteryLevelCalculateCounter++;
		
			seatFlagStatus[0] = ((batVar << 0) & 0xF0) | 0 << 2 | In_SB1 << 1 | In_PSD1;
			seatFlagStatus[1] = ((batVar << 4) & 0xF0) | 0 << 2 | In_SB2 << 1 | In_PSD2;
		
			isDataChanged = (seatFlagStatus[0]	 != payloadBuffer[payloadBufferStartByte + 3])				||	\
							(seatFlagStatus[1]	 != payloadBuffer[payloadBufferStartByte + 4])				||	\
							(prox1CounterBase[1] != payloadBuffer[payloadBufferStartByte + 5])				||	\
							(prox1CounterBase[0] < (int16_t)payloadBuffer[payloadBufferStartByte + 6] - 5)	||	\
							(prox1CounterBase[0] > (int16_t)payloadBuffer[payloadBufferStartByte + 6] + 5)	||	\
							(prox2CounterBase[1] != payloadBuffer[payloadBufferStartByte + 7])				||	\
							(prox2CounterBase[0] < (int16_t)payloadBuffer[payloadBufferStartByte + 8] - 5)	||	\
							(prox2CounterBase[0] > (int16_t)payloadBuffer[payloadBufferStartByte + 8] + 5);
		
			repeatDataCounter = isDataChanged ? 10 : repeatDataCounter;
		
			if(repeatDataCounter)
			{
				payloadBuffer[payloadBufferStartByte + 3] = seatFlagStatus[0];
				payloadBuffer[payloadBufferStartByte + 4] = seatFlagStatus[1];
				payloadBuffer[payloadBufferStartByte + 5] = prox1CounterBase[1];
				payloadBuffer[payloadBufferStartByte + 6] = prox1CounterBase[0];
				payloadBuffer[payloadBufferStartByte + 7] = prox2CounterBase[1];
				payloadBuffer[payloadBufferStartByte + 8] = prox2CounterBase[0];
				payloadBuffer[payloadBufferStartByte + 9] = SX1243CRC8(&payloadBuffer[payloadBufferStartByte + 3]);
			
				if(SX1243Process() != SX_OK)
				{
					repeatDataCounter++;
				}
				else
					repeatDataCounter--;
				BatteryLevelCounter -= BAT_TRANSMIT_CONSTANT;
			}
		
			//printf("adc1: %4d, adc2: %4d\r",adc1, adc2);
			//printf("P1: %4d, P2: %4d\r",prox1CurrentValue, prox2CurrentValue);
		
			//_delay_ms(5);
		
			set_sleep_mode(SLEEP_MODE_PWR_DOWN);
			cli();
		
			sleep_enable();
			sei();
			sleep_cpu();
			sleep_disable();
			cli();
			BatteryLevelCounter -= BAT_SLEEP_CONSTANT;
		}
		
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
	}
}

//ATtiny817
//2600mAh Battery life time 3,7 years