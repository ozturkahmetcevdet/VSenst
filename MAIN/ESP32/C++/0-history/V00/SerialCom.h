#include "esp32-hal.h"

char *m_buffer;
String stringCommand;

/*portMUX_TYPE mux = portMUX_INITIALIZER_UNLOCKED;
volatile bool m_Int = false; 
int rxPin = 3;

void IRAM_ATTR handleInterrupt() 
{
  portENTER_CRITICAL_ISR(&mux);
  m_Int = true;
  portEXIT_CRITICAL_ISR(&mux);
}*/

void SerialInit()
{
  Serial.begin(2000000);
  while(!Serial);
  
  m_buffer = (char*)malloc(14);
  memset(m_buffer, 0x00, 14);
  
  //pinMode(rxPin, INPUT_PULLUP);
  //attachInterrupt(digitalPinToInterrupt(rxPin), handleInterrupt, FALLING);
}
