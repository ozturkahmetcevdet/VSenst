#include <atmel_start.h>
#include <avr/interrupt.h>
#include <avr/sleep.h>
#include <stdio.h>
#include <util/delay.h>
#include <avr/io.h>
#include <QTouchADC.h>
#include <SX1243.h>
#include <rstctrl.h>

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

#define SAMPLE_COUNT		 64   // 2^SAMPLE_CONSTANT
#define SAMPLE_DIVIDER		 0    // SAMPLE_CONSTANT >> 1
#define SAMPLE_MULTIPLIER	 1    // SAMPLE_CONSTANT >> 1
#define TRANSMIT_COUNT		 41
#define DATA_CHANGE_CONSTANT 15
#define DATA_REFRESH_TIME	 300  // second / 2 = 10 minutes

uint8_t payloadBuffer[16] = {
	0xAA, 0xAA,
	0x1E, 0xAA, 0x55, 0xE1,
	0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00
};
const uint8_t payloadBufferStartByte = 6;


uint8_t prox1CounterBase[2] = {0};
uint8_t prox2CounterBase[2] = {0};
uint8_t seatFlagStatus[2];

uint8_t repeatDataCounter = 41;
bool isDataChanged = false;
uint16_t dataRefreshCounter = DATA_REFRESH_TIME;
uint8_t startupDelay = 10;

typedef struct  
{
	int32_t RawValue;
	int32_t LastRawValue;
	int32_t RawAdc;
	uint16_t LoopCycle;
	uint8_t AlphaDivider;
	uint8_t AlphaMultiplier;
}QTOUCHADC_REFERANCE_FILTER;

QTOUCHADC_REFERANCE_FILTER QTOUCHADC_REFERANCE_FILTER_P[2] = {{.AlphaDivider = 2, .AlphaMultiplier = 3},
															  {.AlphaDivider = 2, .AlphaMultiplier = 3}};

//////////////////////////////////////////////////////////////////////////
// 1 means 1uAh
// Full battery capacity is 2700mAH - 2700000uAh
// Formula: (current capacity / full capacity) * 100; 
//////////////////////////////////////////////////////////////////////////
#define BAT_SLEEP_CONSTANT		60				// 30u(A/sn) @1024ms
#define BAT_ADC_CONSTANT		30				// 15u(A/sn) @1024ms
#define BAT_TRANSMIT_CONSTANT   40				// 20u(A/sn) @1024ms
#define BAT_FULL_CAPACITY		2600000			// nAh
#define BAT_CALCULATE_REFRESH_CONSTANT 86400	// ~24 hour

uint64_t BatteryLevelCounter = BAT_FULL_CAPACITY;
uint32_t BatteryLevelCalculateCounter = BAT_CALCULATE_REFRESH_CONSTANT + 1;
uint8_t batVar = 0;


#define GET_PERIODIC_TIMER_VALUE(x) (x + 0x07) << 3 //@ 0x08 --> 512ms start address
enum{
	T_512,
	T_1024,
	T_2048
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
	PORTA_set_port_dir(0xFF, PORT_DIR_OFF);
	PORTB_set_port_dir(0xFF, PORT_DIR_OFF);
	PORTC_set_port_dir(0xFF, PORT_DIR_OFF);
	atmel_start_init();
	
	
	
	batVar = FLASH_0_read_eeprom_byte(0);
	BatteryLevelCounter *= batVar > 100 ? 1 : (((float)batVar) / 100.0f);  
	
	DATA_set_level(false);
	
	payloadBuffer[payloadBufferStartByte + 0] = SIGROW_SERNUM7;
	payloadBuffer[payloadBufferStartByte + 1] = SIGROW_SERNUM8;
	payloadBuffer[payloadBufferStartByte + 2] = SIGROW_SERNUM9;
	SX1243Init(&payloadBuffer[0], sizeof(payloadBuffer), payloadBufferStartByte);
	
	while(true) 
	{
		BatteryLevelCounter -= (BAT_ADC_CONSTANT >> sleepTimeSequence);
		
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
		
		QTOUCH_GetSensorValue(0, false);
		
		
		for(uint8_t j = 0; j < 2; j++)
		{
			QTOUCHADC_REFERANCE_FILTER_P[j].LoopCycle = SAMPLE_COUNT;
			QTOUCHADC_REFERANCE_FILTER_P[j].RawAdc = 0;
			while(--QTOUCHADC_REFERANCE_FILTER_P[j].LoopCycle)
			{
				QTOUCHADC_REFERANCE_FILTER_P[j].RawAdc += QTOUCH_GetSensorValue(j, false) - QTOUCH_GetSensorValue(j, true);
			}
			
			/*if(QTOUCHADC_REFERANCE_FILTER_P[j].RawAdc < QTOUCHADC_REFERANCE_FILTER_P[j].RawValue - 100)
			{
				QTOUCHADC_REFERANCE_FILTER_P[j].AlphaDivider = 1;
				QTOUCHADC_REFERANCE_FILTER_P[j].AlphaMultiplier = 1;
			}
			else
			{
				QTOUCHADC_REFERANCE_FILTER_P[j].AlphaDivider = 2;
				QTOUCHADC_REFERANCE_FILTER_P[j].AlphaMultiplier = 3;
			}*/
			
			QTOUCHADC_REFERANCE_FILTER_P[j].RawValue  = (QTOUCHADC_REFERANCE_FILTER_P[j].RawValue  >> QTOUCHADC_REFERANCE_FILTER_P[j].AlphaDivider) * QTOUCHADC_REFERANCE_FILTER_P[j].AlphaMultiplier + 
														((QTOUCHADC_REFERANCE_FILTER_P[j].RawAdc << (SAMPLE_MULTIPLIER))    >> (SAMPLE_DIVIDER + QTOUCHADC_REFERANCE_FILTER_P[j].AlphaDivider));
			isDataChanged |= QTOUCHADC_REFERANCE_FILTER_P[j].RawValue > (QTOUCHADC_REFERANCE_FILTER_P[j].LastRawValue + DATA_CHANGE_CONSTANT) || QTOUCHADC_REFERANCE_FILTER_P[j].RawValue < (QTOUCHADC_REFERANCE_FILTER_P[j].LastRawValue - DATA_CHANGE_CONSTANT);
			QTOUCHADC_REFERANCE_FILTER_P[j].LastRawValue = QTOUCHADC_REFERANCE_FILTER_P[j].RawValue;
		}
		//ATtiny817
		
		prox1CounterBase[1] = (uint8_t)((QTOUCHADC_REFERANCE_FILTER_P[0].RawValue >> 8) & 0x00FF);
		prox1CounterBase[0] = (uint8_t)((QTOUCHADC_REFERANCE_FILTER_P[0].RawValue >> 0) & 0x00FF);
		prox2CounterBase[1] = (uint8_t)((QTOUCHADC_REFERANCE_FILTER_P[1].RawValue >> 8) & 0x00FF);
		prox2CounterBase[0] = (uint8_t)((QTOUCHADC_REFERANCE_FILTER_P[1].RawValue >> 0) & 0x00FF);
			
		
		if (BatteryLevelCalculateCounter > BAT_CALCULATE_REFRESH_CONSTANT)
		{
			batVar = (uint8_t)((uint64_t)(BatteryLevelCounter * 100) / (uint64_t)BAT_FULL_CAPACITY);
			FLASH_0_write_eeprom_byte(0, batVar);
			BatteryLevelCalculateCounter = 0;
		}
		BatteryLevelCalculateCounter++;
		
		seatFlagStatus[0] = ((batVar << 0) & 0xF0) | 0 << 2 | In_SB1 << 1 | In_PSD1;
		seatFlagStatus[1] = ((batVar << 4) & 0xF0) | 0 << 2 | In_SB2 << 1 | In_PSD2;
		
		isDataChanged |= (seatFlagStatus[0]	!= payloadBuffer[payloadBufferStartByte + 3]) || (seatFlagStatus[1] != payloadBuffer[payloadBufferStartByte + 4]);
		
		repeatDataCounter = (isDataChanged && (repeatDataCounter <= (TRANSMIT_COUNT >> 2))) || (dataRefreshCounter == 0) ? TRANSMIT_COUNT : repeatDataCounter;
		dataRefreshCounter -= (dataRefreshCounter > 0) && (repeatDataCounter == 0) ? 1 : DATA_REFRESH_TIME;
		isDataChanged = false;
		
		if(repeatDataCounter && startupDelay == 0)
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
			BatteryLevelCounter -= (BAT_TRANSMIT_CONSTANT >> sleepTimeSequence);
		}
		
		set_sleep_mode(SLEEP_MODE_PWR_DOWN);
		cli();
		sleepTimeSequence = (repeatDataCounter >= (TRANSMIT_COUNT >> 1)) ? T_512 : (repeatDataCounter > 0) ? T_1024 : T_2048;
		ConfigPIT(GET_PERIODIC_TIMER_VALUE(sleepTimeSequence));
		
		sleep_enable();
		sei();
		sleep_cpu();
		sleep_disable();
		cli();
		BatteryLevelCounter -= (BAT_SLEEP_CONSTANT >> sleepTimeSequence);
		
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
		
		startupDelay -= startupDelay > 0 ? 1 : 0;
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