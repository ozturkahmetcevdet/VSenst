/*
 * QTouchADC.h
 *
 * Created: 27.07.2021 08:15:52
 *  Author: AHMET CEVDET ÖZTÜRK
 */ 
#ifndef QTOUCHADC_H_INCLUDED
#define QTOUCHADC_H_INCLUDED

#include <compiler.h>
#include <QTouchADC.h>

#ifdef __cplusplus
extern "C" {
#endif

	#define CHARGE_DELAY			3 // time it takes for the capacitor to get charged/discharged in microseconds
	
	int32_t QTOUCH_GetSensorValue(uint8_t touchPin, bool dir);

#ifdef __cplusplus
}
#endif

#endif /* QTOUCHADC_H_INCLUDED */