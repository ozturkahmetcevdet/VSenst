/*
 * SX1243.h
 *
 * Created: 03.10.2019 13:08:13
 *  Author: AHMET CEVDET ÖZTÜRK
 */ 

#ifndef __SX1243_H__
#define __SX1243_H__


typedef unsigned char   U8;
typedef unsigned short  U16;
typedef unsigned long   U32;
typedef signed char     S8;
typedef signed short    S16;
typedef signed long     S32;
typedef float          	F24;
typedef double          F32;



#define _NOP() do { __asm__ __volatile__ ("nop"); } while (0)



/*!
 * This is the crytal frequency of the sx1243. THIS SHOULD BE CHANGED DEPENDING ON YOUR IMPLEMENTATION
 */
#define XTAL_FREQ                                   26000000
/*!
 * This is the center frequency for the transmission. THIS SHOULD BE CHANGED DEPENDING ON YOUR SYSTEM
 */
#define RF_FREQUENCY                                915000000
/*!
 * This is the frequency deviation. THIS SHOULD BE CHANGED DEPENDING ON YOUR SYSTEM
 */
#define RF_FREQUENCY_DEVIATION                      203125//809326//203125//125000//203125
/*!
 * SX1243 internal frequency step
 */
#define FREQ_STEP                                   (double)((double)XTAL_FREQ / DIVIDER)

/*!
 * SX1243 internal divider set depending of the frequency band
 */
#if (RF_FREQUENCY > 850000000)
    #define DIVIDER                                 8192    // 2^13
#else
    #define DIVIDER                                 16384   // 2^14
#endif

/*!
 * FRF is caclulated based on the transmission frequency and the internal frequency step
 */
#define FRF                                         (U32)((double)RF_FREQUENCY / FREQ_STEP)
/*!
 * FDEV is caclulated based on the frequency deviation and the internal frequency step
 */
#define FDEV                                        ((U16)((double)RF_FREQUENCY_DEVIATION / FREQ_STEP) << 5)


/*!
 * SX1243 ready to transmit timeout value = 10us * TRANSMITTER_READY_TIMEOUT
 */
#define TRANSMITTER_READY_TIMEOUT					220


/*!
 * Functions return codes definition
 */
#define SX_OK           (U8) 0x00
#define SX_ERROR        (U8) 0x01
#define SX_BUSY         (U8) 0x02
#define SX_EMPTY        (U8) 0x03
#define SX_DONE         (U8) 0x04
#define SX_TIMEOUT      (U8) 0x05
#define SX_UNSUPPORTED  (U8) 0x06
#define SX_WAIT         (U8) 0x07
#define SX_CLOSE        (U8) 0x08
#define SX_ACK          (U8) 0x09
#define SX_NACK         (U8) 0x0A
#define SX_YES          (U8) 0x0B
#define SX_NO           (U8) 0x0C




/*
 * SX1243 instructions
 */
#define INSTRUCTION_CONFIG                          0
#define INSTRUCTION_FREQUENCY                       1
#define INSTRUCTION_STATUS                          2
#define INSTRUCTION_BIST                            3
#define INSTRUCTION_TEST                            4
#define INSTRUCTION_RECOVERY                        5


/*!
 * sx1243 instructions operations
 */
#define INST_WRITE_CFG                              0x000000
#define INST_WRITE_FREQ                             0x180000
#define INST_WRITE_TEST                             0x211000
#define INST_READ_CFG                               0x330000
#define INST_READ_FREQ                              0x440000
#define INST_READ_STAT                              0x550000
#define INST_READ_BIST                              0x660000
#define INST_READ_TEST                              0x77F800
#define INST_RECOVERY                               0xFFFFFF


/*!
 * SX1243 Parameters
 */
#define	MODE_AUTOMATIC                              0x0000
#define MODE_FORCED                                 0x8000

#define MODULATION_FSK                              0x0000
#define MODULATION_OOK                              0x4000

#define BAND_0                                      0x0000
#define BAND_1                                      0x2000

#define POWER_0DBM                                  0x0000
#define POWER_10DBM                                 0x0010

#define TIMEOFF_2MS                                 0x0000
#define TIMEOFF_20MS                                0x0008

#define RESERVED                                    0x0004

#define ENABLE                                      1
#define DISABLE                                     0





typedef struct sTxParam
{
    U32 Freq;                       // Center frequency
    U16 Reserved;                   // Reserved
    U16 OffTimer;                   // Time between automatic sleep mode
    U16 RfPower;                    // RF Power
    U16 FDev;                       // Frequency deviation
    U16 Band;                       // Modualtion Band
    U16 Modulation;                 // Modulation type
    U16 Mode;                       // Transmission mode
    U8 BufferSize;                  // Size of the payload in Byte
    U8 *buffer;                     // Payload
	U16 Config;
	U8 CRC8Base;
}tTxParam;

U8 fastBuf[208];
U16 fastBufSize;


U8 SX1243Init(U8 *PayloadBuffer, U8 size, U8 DataStartByte);
void SX1243Reset(void);
U8 SX1243SetTxPacketBuffer(U8 *buffer, U8 size);
void Sx1243ConvertBuffer(U8 startAddress);
U8 SX1243CRC8(U8 *buffer);
U8 SX1243Process();

#endif //__SX1243_H__
