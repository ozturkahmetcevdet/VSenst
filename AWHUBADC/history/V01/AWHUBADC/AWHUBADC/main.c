#include <atmel_start.h>
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

int32_t adcMax = 0;
int32_t adc1 = 0, adc2 = 0;
int32_t refMax = 0;
int32_t ref1 = 0, ref2 = 0; 
int16_t refP1 = 0, refP2 = 0;

int main(void)
{
	/* Initializes MCU, drivers and middleware */
	atmel_start_init();
	
	uint8_t startupDelay = 100;
	
	while (startupDelay--)
	{
		DATA_toggle_level();
		_delay_ms(20);
	}
	
	payloadBuffer[payloadBufferStartByte + 0] = SIGROW_SERNUM7;
	payloadBuffer[payloadBufferStartByte + 1] = SIGROW_SERNUM8;
	payloadBuffer[payloadBufferStartByte + 2] = SIGROW_SERNUM9;
	SX1243Init(&payloadBuffer[0], sizeof(payloadBuffer), payloadBufferStartByte);
	
	TOUCH_GetSensorValue(0, false);
	TOUCH_GetSensorValue(0, true);
	TOUCH_GetSensorValue(1, false);
	TOUCH_GetSensorValue(1, true);
	
	for (uint8_t i = 0; i < 212; i++)
	{
		ref1 = TOUCH_GetSensorValue(0, false);
		ref2 = TOUCH_GetSensorValue(0, true);
		refMax = i == 0 ? ref1 - ref2 : (refMax < (ref1 - ref2) ? (ref1 - ref2) : refMax);
	}
	
	refP1 = (uint16_t)refMax;
	refMax = ref1 = ref2 = 0;
	
	for (uint8_t i = 0; i < 212; i++)
	{
		ref1 = TOUCH_GetSensorValue(1, false);
		ref2 = TOUCH_GetSensorValue(1, true);
		refMax = i == 0 ? ref1 - ref2 : (refMax < (ref1 - ref2) ? (ref1 - ref2) : refMax);
	}
	
	refP2 = (uint16_t)refMax;
	refMax = ref1 = ref2 = 0;

	/* Replace with your application code */
	while (1) {
		for (uint8_t i = 0; i < 212; i++)
		{
			adc1 = TOUCH_GetSensorValue(0, false);
			adc2 = TOUCH_GetSensorValue(0, true);
			adcMax = i == 0 ? adc1 - adc2 : (adcMax < (adc1 - adc2) ? (adc1 - adc2) : adcMax);
		}
		
		prox1CurrentValue = ((uint16_t)adcMax - refP1);
		adcMax = adc1 = adc2 = 0;
		prox1CurrentValue = prox1CurrentValue < 0 ? 0 : prox1CurrentValue;
		prox1CounterBase[1] = (uint8_t)((prox1CurrentValue >> 8) & 0x00FF);
		prox1CounterBase[0] = (uint8_t)((prox1CurrentValue >> 0) & 0x00FF);
		
		for (uint8_t i = 0; i < 212; i++)
		{
			adc1 = TOUCH_GetSensorValue(1, false);
			adc2 = TOUCH_GetSensorValue(1, true);
			adcMax = i == 0 ? adc1 - adc2 : (adcMax < (adc1 - adc2) ? (adc1 - adc2) : adcMax);
		}
		
		prox2CurrentValue = ((uint16_t)adcMax - refP2);
		adcMax = adc1 = adc2 = 0;
		prox2CurrentValue = prox2CurrentValue < 0 ? 0 : prox2CurrentValue;
		prox2CounterBase[1] = (uint8_t)((prox2CurrentValue >> 8) & 0x00FF);
		prox2CounterBase[0] = (uint8_t)((prox2CurrentValue >> 0) & 0x00FF);
		
		
		
		seatFlagStatus[0] = /*batteryLevelMSB |*/ 0 << 2 | 0 << 1 | 1;
		seatFlagStatus[1] = /*batteryLevelMSB |*/ 0 << 2 | 0 << 1 | 1;
		
		payloadBuffer[payloadBufferStartByte + 3] = seatFlagStatus[0];
		payloadBuffer[payloadBufferStartByte + 4] = seatFlagStatus[1];
		payloadBuffer[payloadBufferStartByte + 5] = prox1CounterBase[1];
		payloadBuffer[payloadBufferStartByte + 6] = prox1CounterBase[0];
		payloadBuffer[payloadBufferStartByte + 7] = prox2CounterBase[1];
		payloadBuffer[payloadBufferStartByte + 8] = prox2CounterBase[0];
		payloadBuffer[payloadBufferStartByte + 9] = SX1243CRC8(&payloadBuffer[payloadBufferStartByte + 3]);
		
		SX1243Process();
		
		//printf("adc1: %4d, adc2: %4d\r",adc1, adc2);
		printf("P1: %4d, P2: %4d\r",prox1CurrentValue, prox2CurrentValue);
		_delay_ms(1000);
		
		if(CBT_get_level() == false)
		{
			RSTCTRL_reset();
		}
	}
}

//ATtiny817