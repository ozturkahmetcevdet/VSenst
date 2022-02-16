/*
 * QTouchADC.c
 *
 * Created: 27.07.2021 08:14:38
 *  Author: AHMET CEVDET ÖZTÜRK
 */ 

#include <QTouchADC.h>
#include <atmel_start.h>

#include <util/delay.h>

int32_t QTOUCH_GetSensorValue(uint8_t touchPin, bool dir)
{
	int32_t var = 0;
	
	switch (touchPin)
	{
		case 0:
			/*!
			* Set PARTNER pin state for charging or discharging ADC sample capacitance.
			* If dir == true sample capacitance charged else discharged.
			*/
			PARTNER_set_level(dir);
			PARTNER_set_dir(PORT_DIR_OUT);
			ADC0.MUXPOS = ADC_MUXPOS_AIN10_gc;
			
			/*!
			* Set SENSOR pin state for charging or discharging proximity sensor pad.
			* If dir == true proximity sensor pad charged else discharged.
			*/
			SX_set_level(!dir);
			SX_set_dir(PORT_DIR_OUT);
			_delay_us(CHARGE_DELAY);
			
			/*!
			* Set SENSOR pin to ADC input and complete conversion.
			*/
			SX_set_dir(PORT_DIR_IN);
			var = ADC_0_get_conversion(ADC_MUXPOS_AIN6_gc);
			ADC0.MUXPOS = ADC_MUXPOS_AIN10_gc;
			
			/*!
			* Set unsued pin states output high for impedance control
			*/
			PARTNER_set_level(true);
			SX_set_level(true);
			SX_set_dir(PORT_DIR_OUT);
			
			return var;
		break;
		
		case 1:
			/*!
			* Set PARTNER pin state for charging or discharging ADC sample capacitance.
			* If dir == true sample capacitance charged else discharged.
			*/
			PARTNER_set_level(dir);
			PARTNER_set_dir(PORT_DIR_OUT);
			ADC0.MUXPOS = ADC_MUXPOS_AIN10_gc;
			
			/*!
			* Set SENSOR pin state for charging or discharging proximity sensor pad.
			* If dir == true proximity sensor pad charged else discharged.
			*/
			SY_set_level(!dir);
			SY_set_dir(PORT_DIR_OUT);
			_delay_us(CHARGE_DELAY);
			
			/*!
			* Set SENSOR pin to ADC input and complete conversion.
			*/
			SY_set_dir(PORT_DIR_IN);
			var = ADC_0_get_conversion(ADC_MUXPOS_AIN11_gc);
			ADC0.MUXPOS = ADC_MUXPOS_AIN10_gc;			
			
			/*!
			* Set unsued pin states output high for impedance control
			*/
			PARTNER_set_level(true);
			SY_set_level(true);
			SY_set_dir(PORT_DIR_OUT);
			
			return var;
		break;
		
		default:
		/*
		* Do nothing! 
		*/
		break;
	}
	
	return var;
}
//ATtiny817
