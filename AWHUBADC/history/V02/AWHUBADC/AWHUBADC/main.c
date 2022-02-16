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


int16_t prox1CurrentValue, prox2CurrentValue;
uint8_t prox1CounterBase[2] = {0};
uint8_t prox2CounterBase[2] = {0};
uint8_t seatFlagStatus[2];

int32_t adc1 = 0, adc2 = 0;
int32_t ref1 = 0, ref2 = 0; 
int16_t refP1 = 0, refP2 = 0;
int32_t rawTotal;
int16_t rawAdc[2][4];
uint8_t rawAdcCount = 0;

uint8_t whileLoopCycle = 0;

bool isDataChanged = false;
uint8_t repeatDataCounter = 0;

//////////////////////////////////////////////////////////////////////////
// 1 means 5uAh
// Full battery capacity is 2700mAH - 2700000uAh
// Formula: (current capacity / full capacity) * 100; 
//////////////////////////////////////////////////////////////////////////
#define BAT_SLEEP_CONSTANT		30	// 30uAh
#define BAT_ADC_CONSTANT		10	//  5uAh
#define BAT_TRANSMIT_CONSTANT   20	// 10uAh
#define BAT_FULL_CAPACITY		2600000.0f
#define BAT_CALCULATE_REFRESH_CONSTANT 50000

uint64_t BatteryLevelCounter = BAT_FULL_CAPACITY;
uint32_t BatteryLevelCalculateCounter = BAT_CALCULATE_REFRESH_CONSTANT + 1;
uint8_t batVar = 0;

int main(void)
{
	/* Initializes MCU, drivers and middleware */
	atmel_start_init();
	
	uint8_t startupDelay = 200;
	
	while (startupDelay--)
	{
		DATA_toggle_level();
		_delay_ms(20);
	}
	DATA_set_level(true);
	
	batVar = FLASH_0_read_eeprom_byte(0);
	BatteryLevelCounter *= batVar > 100 ? 1 : (((float)batVar + 1) / 100.0f);  
	
	TOUCH_GetSensorValue(0, false);
	
	
	
	for (uint8_t j = 0; j < 10; j++)
	{
		whileLoopCycle = 32;
		while(whileLoopCycle--)
		{
			ref1 += TOUCH_GetSensorValue(0, false);
			ref2 += TOUCH_GetSensorValue(0, true);
		}
		ref1 >>= 2;
		ref2 >>= 2;
		
		refP1 = refP1 < (int16_t)(ref1 - ref2) ? (int16_t)(ref1 - ref2) : refP1;
		ref1 = ref2 = 0;
		
		whileLoopCycle = 32;
		while(whileLoopCycle--)
		{
			ref1 += TOUCH_GetSensorValue(1, false);
			ref2 += TOUCH_GetSensorValue(1, true);
		}
		ref1 >>= 2;
		ref2 >>= 2;
		
		refP2 = refP2 < (int16_t)(ref1 - ref2) ? (int16_t)(ref1 - ref2) : refP2;
		ref1 = ref2 = 0;
	}
	DATA_set_level(false);
	
	CBT_set_isc(PORT_ISC_BOTHEDGES_gc);
	
	
	payloadBuffer[payloadBufferStartByte + 0] = SIGROW_SERNUM7;
	payloadBuffer[payloadBufferStartByte + 1] = SIGROW_SERNUM8;
	payloadBuffer[payloadBufferStartByte + 2] = SIGROW_SERNUM9;
	SX1243Init(&payloadBuffer[0], sizeof(payloadBuffer), payloadBufferStartByte);

	/* Replace with your application code */
	while (1) {
		BatteryLevelCounter -= BAT_ADC_CONSTANT;
		
		SB1_set_pull_mode(PORT_PULL_UP);
		SB2_set_pull_mode(PORT_PULL_UP);
		PSD1_set_pull_mode(PORT_PULL_UP);
		PSD2_set_pull_mode(PORT_PULL_UP);
		
		uint8_t In_SB1  = !SB1_get_level();
		uint8_t In_SB2  = !SB2_get_level();
		uint8_t	In_PSD1 = !PSD1_get_level();
		uint8_t In_PSD2 = !PSD2_get_level();
		
		SB1_set_pull_mode(PORT_PULL_OFF);
		SB2_set_pull_mode(PORT_PULL_OFF);
		PSD1_set_pull_mode(PORT_PULL_OFF);
		PSD2_set_pull_mode(PORT_PULL_OFF);
		
		//ADC ENABLE
		ADC_0_enable();	
		TOUCH_GetSensorValue(0, false);
		
		//if(In_PSD1)
		{
			whileLoopCycle = 32;
			while(whileLoopCycle--)
			{
				adc1 += TOUCH_GetSensorValue(0, false);
				adc2 += TOUCH_GetSensorValue(0, true);
			}
			adc1 >>= 2;
			adc2 >>= 2;
		
			rawAdc[0][rawAdcCount] = ((int16_t)(adc1 - adc2) - refP1);
			if(rawAdc[0][rawAdcCount] < -12)
			{
				refP1 = (int16_t)(adc1 - adc2);
			}
		
			for (uint8_t j = 0; j < 2; j++)
			{
				rawTotal += rawAdc[0][j];
			}
			prox1CurrentValue = (int16_t)(rawTotal >> 1);
			rawTotal = 0;
			adc1 = adc2 = 0;
			prox1CurrentValue = prox1CurrentValue < 0 ? 0 : prox1CurrentValue;
			prox1CounterBase[1] = (uint8_t)((prox1CurrentValue >> 8) & 0x00FF);
			prox1CounterBase[0] = (uint8_t)((prox1CurrentValue >> 0) & 0x00FF);
		}
		
		//if(In_PSD2)
		{
			whileLoopCycle = 32;
			while(whileLoopCycle--)
			{
				adc1 += TOUCH_GetSensorValue(1, false);
				adc2 += TOUCH_GetSensorValue(1, true);
			}
			adc1 >>= 2;
			adc2 >>= 2;
	
			rawAdc[1][rawAdcCount] = ((int16_t)(adc1 - adc2) - refP2);
			if(rawAdc[1][rawAdcCount] < -12)
			{
				refP2 = (int16_t)(adc1 - adc2);
			}
	
			for (uint8_t j = 0; j < 2; j++)
			{
				rawTotal += rawAdc[1][j];
			}
			prox2CurrentValue = (int16_t)(rawTotal >> 1);
			rawTotal = 0;
			adc1 = adc2 = 0;
			prox2CurrentValue = prox2CurrentValue < 0 ? 0 : prox2CurrentValue;
			prox2CounterBase[1] = (uint8_t)((prox2CurrentValue >> 8) & 0x00FF);
			prox2CounterBase[0] = (uint8_t)((prox2CurrentValue >> 0) & 0x00FF);
		}
		//ADC DISABLE
		ADC_0_disable();
		
		rawAdcCount += rawAdcCount < 1 ? 1 : -rawAdcCount;
		
		if (BatteryLevelCalculateCounter > BAT_CALCULATE_REFRESH_CONSTANT)
		{
			batVar = (uint8_t)((((float)BatteryLevelCounter) / BAT_FULL_CAPACITY) * 100.0f);
			FLASH_0_write_eeprom_byte(0, batVar);
			BatteryLevelCalculateCounter = 0;
		}
		BatteryLevelCalculateCounter++;
		
		seatFlagStatus[0] = ((batVar << 0) & 0xF0) | 0 << 2 | In_SB1 << 1 | In_PSD1;
		seatFlagStatus[1] = ((batVar << 4) & 0xF0) | 0 << 2 | In_SB2 << 1 | In_PSD2;
		
		isDataChanged = (seatFlagStatus[0]	 != payloadBuffer[payloadBufferStartByte + 3]) ||	\
						(seatFlagStatus[1]	 != payloadBuffer[payloadBufferStartByte + 4]) ||	\
						(prox1CounterBase[1] != payloadBuffer[payloadBufferStartByte + 5]) ||	\
						(prox1CounterBase[0] != payloadBuffer[payloadBufferStartByte + 6]) ||	\
						(prox2CounterBase[1] != payloadBuffer[payloadBufferStartByte + 7]) ||	\
						(prox2CounterBase[0] != payloadBuffer[payloadBufferStartByte + 8]);
		
		repeatDataCounter = isDataChanged ? 20 : repeatDataCounter;
		
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
		
		if(CBT_get_level() == false)
		{
			RSTCTRL_reset();
		}
	}
}

//ATtiny817
//2600mAh Battery life time 6,71 years