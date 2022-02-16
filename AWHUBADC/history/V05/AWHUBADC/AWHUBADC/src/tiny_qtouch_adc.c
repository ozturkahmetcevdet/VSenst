/*
 * tiny_qtouch_adc.c
 *
 * Created: 27.07.2021 08:14:38
 *  Author: ahmet
 */ 

#include <tiny_qtouch_adc.h>
#include <atmel_start.h>

#include <util/delay.h>

int32_t TOUCH_GetSensorValue(uint8_t touchPin, bool dir)
{
	int32_t var = 0;
	SHIELD_set_level(false);
	
	switch (touchPin)
	{
		case 0:
			PARTNER_set_level(dir);
			PARTNER_set_dir(PORT_DIR_OUT);
			ADC0.MUXPOS = ADC_MUXPOS_AIN10_gc;
			
			SX_set_level(!dir);
			SX_set_dir(PORT_DIR_OUT);
			_delay_us(CHARGE_DELAY);
			
			SX_set_dir(PORT_DIR_IN);
			//SX_set_isc(PORT_ISC_INPUT_DISABLE_gc);
			//SX_set_pull_mode(PORT_PULL_OFF);
			
			//ADC0.MUXPOS = ADC_MUXPOS_AIN6_gc;			
			//_delay_us(TRANSFER_DELAY);
			
			var = ADC_0_get_conversion(ADC_MUXPOS_AIN6_gc);
			ADC0.MUXPOS = ADC_MUXPOS_AIN10_gc;
			
			PARTNER_set_level(true);
			//PARTNER_set_dir(PORT_DIR_IN);
			//PARTNER_set_isc(PORT_ISC_INPUT_DISABLE_gc);
			//PARTNER_set_pull_mode(PORT_PULL_OFF);
			SX_set_level(true);
			SX_set_dir(PORT_DIR_OUT);
			
			return var;
		break;
		
		case 1:
			PARTNER_set_level(dir);
			PARTNER_set_dir(PORT_DIR_OUT);
			ADC0.MUXPOS = ADC_MUXPOS_AIN10_gc;
		
			SY_set_level(!dir);
			SY_set_dir(PORT_DIR_OUT);
			_delay_us(CHARGE_DELAY);
		
			SY_set_dir(PORT_DIR_IN);
			//SY_set_isc(PORT_ISC_INPUT_DISABLE_gc);
			//SY_set_pull_mode(PORT_PULL_OFF);
		
			//ADC0.MUXPOS = ADC_MUXPOS_AIN11_gc;
			//_delay_us(TRANSFER_DELAY);
		
			var = ADC_0_get_conversion(ADC_MUXPOS_AIN11_gc);
			ADC0.MUXPOS = ADC_MUXPOS_AIN10_gc;
		
			PARTNER_set_level(true);
			//PARTNER_set_dir(PORT_DIR_IN);
			//PARTNER_set_isc(PORT_ISC_INPUT_DISABLE_gc);
			//PARTNER_set_pull_mode(PORT_PULL_OFF);
			SY_set_level(true);
			SY_set_dir(PORT_DIR_OUT);
			
			return var;
		break;
		
		default:
		break;
	}
	
	return var;
}

//ATtiny817
