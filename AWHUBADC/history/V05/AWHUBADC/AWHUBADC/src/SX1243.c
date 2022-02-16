#include <driver_init.h>
#include <SX1243.h>
#include <clock_config.h>
#include <util/delay.h>
#include <sx1243.h>

/*!
* Radio packet to be transmitted
*/
//#pragma udata
tTxParam TxParam;

extern const uint8_t payloadBufferStartByte;

/*
* Send data through the SPI
*
* To ease the porting on MCU not necessary equipped with standard SPI interface,
* the SPI is organized around toggling GPIOs
*
* \param[IN] outData Data to send on SPI
*
* \retval None
*/
void SpiOut(U8 outData )
{
	U8 bitMask = 0x80;
	while (bitMask > 0)
	{
		CTRL_set_level(0);
		DATA_set_level( outData & bitMask );
		bitMask >>= 1;
		CTRL_set_level(1);
	}
	CTRL_set_level(0);
}


U8 SX1243Write(U8 instruction, U32 data)
{
	switch(instruction)
	{
		case INSTRUCTION_CONFIG: // Config
		SpiOut(INST_WRITE_CFG);
		break;
		case INSTRUCTION_FREQUENCY: // Freq
		SpiOut((INST_WRITE_FREQ | (data & 0x070000)) >> 16);
		break;
		default:
		return SX_ERROR;
	}
	
	SpiOut((data >> 8) & 0xFF);
	SpiOut(data & 0xFF);
	DATA_set_level(0);
	return SX_OK;
}

U8 SX1243Init(U8 *PayloadBuffer, U8 size, U8 DataStartByte)
{
	SX1243Reset();

	TxParam.Mode       = MODE_AUTOMATIC;
	TxParam.Modulation = MODULATION_FSK;
	TxParam.Band       = BAND_1;
	TxParam.FDev       = FDEV;
	TxParam.RfPower    = POWER_0DBM;
	TxParam.OffTimer   = TIMEOFF_2MS;
	TxParam.Reserved   = RESERVED;
	TxParam.Freq	   = FRF;
	TxParam.Config	   = TxParam.Mode			| 
						 TxParam.Modulation		| 
						 TxParam.Band			| 
						 TxParam.FDev			| 
						 TxParam.RfPower		| 
						 TxParam.OffTimer		| 
						 TxParam.Reserved;
	TxParam.CRC8Base   = 0xDB ^ 
						 PayloadBuffer[DataStartByte + 0] ^ 
						 PayloadBuffer[DataStartByte + 1] ^ 
						 PayloadBuffer[DataStartByte + 2];
	SX1243SetTxPacketBuffer(PayloadBuffer, size);
	return SX_OK;
}

void SX1243Reset(void)
{
	NRESET_set_level(0);
	_delay_ms(10);
	NRESET_set_level(1);
}

U8 SX1243SetTxPacketBuffer(U8 *PayloadBuffer, U8 size)
{
	TxParam.buffer = PayloadBuffer;
	TxParam.BufferSize = size;
	fastBufSize = sizeof(fastBuf);
	Sx1243ConvertBuffer(0);
	return SX_OK;
}

void Sx1243ConvertBuffer(U8 startAddress)
{	
	for (U16 j = startAddress; j < TxParam.BufferSize; j++)
	{
		fastBuf[j * 8 + 0] = TxParam.buffer[j] & 0x80;
		fastBuf[j * 8 + 1] = TxParam.buffer[j] & 0x40;
		fastBuf[j * 8 + 2] = TxParam.buffer[j] & 0x20;
		fastBuf[j * 8 + 3] = TxParam.buffer[j] & 0x10;
		fastBuf[j * 8 + 4] = TxParam.buffer[j] & 0x08;
		fastBuf[j * 8 + 5] = TxParam.buffer[j] & 0x04;
		fastBuf[j * 8 + 6] = TxParam.buffer[j] & 0x02;
		fastBuf[j * 8 + 7] = TxParam.buffer[j] & 0x01;
	}
}

U8 SX1243CRC8(U8 *buffer)
{
	return (uint8_t)(TxParam.CRC8Base ^ 
					 buffer[0]		  ^ 
					 buffer[1]		  ^ 
					 buffer[2]		  ^ 
					 buffer[3]		  ^ 
					 buffer[4]		  ^ 
					 buffer[5]);
}

U8 SX1243Process(void)
{
	U8 state = SX_OK;
	U16 j = 0;

	TxParam.Config |= 0x8000;
	SX1243Write(INSTRUCTION_CONFIG, TxParam.Config);
	SX1243Write(INSTRUCTION_FREQUENCY, TxParam.Freq);
	TxParam.Config &= 0x7FFF;

	Sx1243ConvertBuffer(payloadBufferStartByte + 3);
	while(TX_READY_get_level() == 0 && j < TRANSMITTER_READY_TIMEOUT)
	{
		_delay_us(10);
		j++;
	}
	
	
	if (j < TRANSMITTER_READY_TIMEOUT)
	{
		j = 0;
		//FLASH_set_level(1);
		
		while (j < fastBufSize)
		{
			DATA_set_level(fastBuf[j]);
			_delay_us(6.4);
			if (!fastBuf[j])
			{
				_NOP();
				_NOP();
			}
			j++;
		}
		
		//FLASH_set_level(0);
	}
	else
	{
		SX1243Reset();
		return SX_ERROR;
	}
	
	SX1243Write(INSTRUCTION_CONFIG, TxParam.Config);
		
	return state;
}