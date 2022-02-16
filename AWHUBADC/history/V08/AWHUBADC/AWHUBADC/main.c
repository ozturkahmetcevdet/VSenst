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

#define SAMPLE_COUNT		 48   // 2^SAMPLE_CONSTANT
#define SAMPLE_DIVIDER		 0    // SAMPLE_CONSTANT >> 1
#define SAMPLE_MULTIPLIER	 1    // SAMPLE_CONSTANT >> 1
#define TRANSMIT_COUNT		 41
#define DATA_CHANGE_CONSTANT 15
#define DATA_REFRESH_TIME	 300  // second / 2 = 10 minutes

uint8_t payloadBuffer[42] = {
	0xAA, 0xAA,																						//Preamble						-->  2 byte
	0x1E, 0xAA, 0X55, 0XE1,																			//Sync Word						-->  4 byte
	0x00, 0x00,																						//MCU UID						-->  2 byte
    0x00,																							//Config I/O - Battery etc..	-->  1 byte
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,	//px1 packet					--> 16 byte
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,	//px2 packet					--> 16 byte
	0x00																							//CRC							-->  1 byte
};																									//Total							--> 42 byte
const uint8_t payloadBufferStartByte = 6;


uint8_t proxCounterBase[2] = {0};
uint8_t seatFlagStatus;

uint8_t repeatDataCounter = 11;
bool isDataChanged = false;
uint16_t dataRefreshCounter = DATA_REFRESH_TIME;
uint8_t startupDelay = 100;
uint8_t basicValueTiming = 4;

typedef struct  
{
	uint32_t RawValue;
	uint32_t LastRawValue;
	uint32_t BasicValue;
	uint32_t RawAdc;
	uint16_t LoopCycle;
	uint8_t AlphaDivider;
	uint8_t AlphaMultiplier;
}QTOUCHADC_REFERANCE_FILTER;

QTOUCHADC_REFERANCE_FILTER QTOUCHADC_REFERANCE_FILTER_P[2] = {{.AlphaDivider = 2, .AlphaMultiplier = 3, .BasicValue = 0},
															  {.AlphaDivider = 2, .AlphaMultiplier = 3, .BasicValue = 0}};
//ATtiny817																 
int32_t QTOUCH_LastDiff = 0;
int32_t QTOUCH_NewDiff = 0;

//////////////////////////////////////////////////////////////////////////
// 1 means 1uAh
// Full battery capacity is 2700mAH - 2700000uAh
// Formula: (current capacity / full capacity) * 100; 
//////////////////////////////////////////////////////////////////////////
#define BAT_SLEEP_CONSTANT		120				// 30u(A/sn) @1024ms
#define BAT_ADC_CONSTANT		60				// 15u(A/sn) @1024ms
#define BAT_TRANSMIT_CONSTANT   77				// 20u(A/sn) @1024ms
#define BAT_FULL_CAPACITY		9360000000		// uAs
#define BAT_CALCULATE_REFRESH_CONSTANT 86400	// ~24 hour

uint64_t BatteryLevelCounter = BAT_FULL_CAPACITY;
uint32_t BatteryLevelCalculateCounter = BAT_CALCULATE_REFRESH_CONSTANT + 1;
uint8_t batVar = 0;


#define GET_PERIODIC_TIMER_VALUE(x) (x + 0x07) << 3 //@ 0x08 --> 512ms start address
enum{
	T_256  = 0,
	T_512  = 1,
	T_1024 = 2,
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
	batVar = batVar > 4 ? 4 : batVar;
	BatteryLevelCounter = ((uint64_t)((float)BatteryLevelCounter * (float)batVar)) >> 2;
	
	DATA_set_level(false);
	
	payloadBuffer[payloadBufferStartByte + 0] = SIGROW_SERNUM8;
	payloadBuffer[payloadBufferStartByte + 1] = SIGROW_SERNUM9;
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
		uint8_t	In_PSD1 = true;//!PSD1_get_level();
		uint8_t In_PSD2 = true;//!PSD2_get_level();
		
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
		
		QTOUCH_LastDiff = (int32_t)QTOUCHADC_REFERANCE_FILTER_P[0].LastRawValue - (int32_t)QTOUCHADC_REFERANCE_FILTER_P[1].LastRawValue;
		for(uint8_t j = 0; j < 2; j++)
		{
			QTOUCHADC_REFERANCE_FILTER_P[j].LoopCycle = SAMPLE_COUNT;
			QTOUCHADC_REFERANCE_FILTER_P[j].RawAdc = 0;
			while(--QTOUCHADC_REFERANCE_FILTER_P[j].LoopCycle)
			{
				QTOUCHADC_REFERANCE_FILTER_P[j].RawAdc += QTOUCH_GetSensorValue(j, false) - QTOUCH_GetSensorValue(j, true);
			}
			
			QTOUCHADC_REFERANCE_FILTER_P[j].RawValue  = (QTOUCHADC_REFERANCE_FILTER_P[j].RawValue  >> QTOUCHADC_REFERANCE_FILTER_P[j].AlphaDivider) * QTOUCHADC_REFERANCE_FILTER_P[j].AlphaMultiplier + 
														((QTOUCHADC_REFERANCE_FILTER_P[j].RawAdc << (SAMPLE_MULTIPLIER))    >> (SAMPLE_DIVIDER + QTOUCHADC_REFERANCE_FILTER_P[j].AlphaDivider));
			isDataChanged |= QTOUCHADC_REFERANCE_FILTER_P[j].RawValue > (QTOUCHADC_REFERANCE_FILTER_P[j].LastRawValue + DATA_CHANGE_CONSTANT) || QTOUCHADC_REFERANCE_FILTER_P[j].RawValue < (QTOUCHADC_REFERANCE_FILTER_P[j].LastRawValue - DATA_CHANGE_CONSTANT);
			QTOUCHADC_REFERANCE_FILTER_P[j].LastRawValue = QTOUCHADC_REFERANCE_FILTER_P[j].RawValue;
			
			if(basicValueTiming == 1)
			{
				QTOUCHADC_REFERANCE_FILTER_P[j].BasicValue = QTOUCHADC_REFERANCE_FILTER_P[j].RawValue - 92;
			}
		}
		QTOUCH_NewDiff = (int32_t)QTOUCHADC_REFERANCE_FILTER_P[0].LastRawValue - (int32_t)QTOUCHADC_REFERANCE_FILTER_P[1].LastRawValue;
		//ATtiny817
		
		int16_t prox1 = QTOUCHADC_REFERANCE_FILTER_P[0].RawValue - QTOUCHADC_REFERANCE_FILTER_P[0].BasicValue;
		int16_t prox2 = QTOUCHADC_REFERANCE_FILTER_P[1].RawValue - QTOUCHADC_REFERANCE_FILTER_P[1].BasicValue;
		
		prox1 = prox1 < 0 ? 0 : prox1;
		prox2 = prox2 < 0 ? 0 : prox2;
		
		proxCounterBase[0] = (uint8_t)((prox1 & 0x03FC) >> 2);
		proxCounterBase[1] = (uint8_t)((prox2 & 0x03FC) >> 2);
			
		
		if (BatteryLevelCalculateCounter > BAT_CALCULATE_REFRESH_CONSTANT)
		{
			batVar = (uint8_t)((uint64_t)(BatteryLevelCounter << 2) / (uint64_t)BAT_FULL_CAPACITY);
			FLASH_0_write_eeprom_byte(0, batVar);
			BatteryLevelCalculateCounter = 0;
			RSTCTRL_clear_reset_cause();
		}
		BatteryLevelCalculateCounter++;
		
		isDataChanged |= ((payloadBuffer[payloadBufferStartByte + 2] & 0xBF) != (seatFlagStatus = ((((RSTCTRL.RSTFR > 0) << 7) & 0x80) | ((batVar << 4) & 0x30) | ((In_SB2 << 3 | In_SB1 << 2 | In_PSD2 << 1 | In_PSD1 << 0) & 0x0F)) & 0xBF));
		seatFlagStatus |= (((bool)(QTOUCH_LastDiff > QTOUCH_NewDiff) << 6) & 0x40);
		
		repeatDataCounter = (isDataChanged && (repeatDataCounter <= (TRANSMIT_COUNT >> 1))) || (dataRefreshCounter == 0) ? TRANSMIT_COUNT : repeatDataCounter;
		dataRefreshCounter -= (dataRefreshCounter > 0) && (repeatDataCounter == 0) ? 1 : DATA_REFRESH_TIME;
		isDataChanged = false;
		
		if(repeatDataCounter && startupDelay == 0)
		{
			payloadBuffer[payloadBufferStartByte + 2] = seatFlagStatus;
			payloadBuffer[payloadBufferStartByte + 3] = proxCounterBase[0];
			payloadBuffer[payloadBufferStartByte + 4] = proxCounterBase[1];
			payloadBuffer[payloadBufferStartByte + 5] = SX1243CRC8(&payloadBuffer[payloadBufferStartByte + 2]);
			
			repeatDataCounter -= SX1243Process() == SX_OK ? 1 : -1;
			BatteryLevelCounter -= (BAT_TRANSMIT_CONSTANT >> sleepTimeSequence);
		}
		
		if(startupDelay == 0)
		{
			set_sleep_mode(SLEEP_MODE_PWR_DOWN);
			cli();
			sleepTimeSequence = (repeatDataCounter >= (TRANSMIT_COUNT >> 1)) ? ((repeatDataCounter % 2) ? T_256 : T_512) : (repeatDataCounter > 0) ? T_1024 : T_2048;
			ConfigPIT(GET_PERIODIC_TIMER_VALUE(sleepTimeSequence));
			
			sleep_enable();
			sei();
			sleep_cpu();
			sleep_disable();
			cli();
			BatteryLevelCounter -= (BAT_SLEEP_CONSTANT >> sleepTimeSequence);
			basicValueTiming -= basicValueTiming > 0 ? 1 : 0;
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