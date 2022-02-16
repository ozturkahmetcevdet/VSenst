/*
 * tiny_qtouch_adc.h
 *
 * Created: 27.07.2021 08:15:52
 *  Author: ahmet
 */ 
#ifndef TINY_QTOUCH_ADC_H_INCLUDED
#define TINY_QTOUCH_ADC_H_INCLUDED

#include <compiler.h>
#include <tiny_qtouch_adc.h>

#ifdef __cplusplus
extern "C" {
#endif

	#define CHARGE_DELAY			3 // time it takes for the capacitor to get charged/discharged in microseconds
	
	int32_t TOUCH_GetSensorValue(uint8_t touchPin, bool dir);

#ifdef __cplusplus
}
#endif

#endif /* TINY_QTOUCH_ADC_H_INCLUDED */