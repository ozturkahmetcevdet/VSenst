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

	#define CHARGE_DELAY			2 // time it takes for the capacitor to get charged/discharged in microseconds
	#define TRANSFER_DELAY			10 // time it takes for the capacitors to exchange charge
	#define TOUCH_VALUE_BASELINE	-165 // this is the value my setup measures when the probe is not touched. For your setup this might be different. In order for the LED to fade correctly, you will have to adjust this value
	#define TOUCH_VALUE_SCALE		5 // this is also used for the LED fading. The value should be chosen such that the value measured when the probe is fully touched minus TOUCH_VALUE_BASELINE is scaled to 31, e.g. untouched_val= 333, touched_val= 488, difference= 155, divide by 5 to get 31.


	uint16_t TOUCH_GetSensorValue(uint8_t touchPin, bool dir);

#ifdef __cplusplus
}
#endif

#endif /* TINY_QTOUCH_ADC_H_INCLUDED */