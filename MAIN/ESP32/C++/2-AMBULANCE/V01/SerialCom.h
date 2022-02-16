#include "esp32-hal.h"

String stringCommand;
char* charArray;

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
  Serial.begin(921600);
  while(!Serial);
  
  charArray = (char*)malloc(14);
  memset(charArray, 0x00, 14);
  
  //pinMode(rxPin, INPUT_PULLUP);
  //attachInterrupt(digitalPinToInterrupt(rxPin), handleInterrupt, FALLING);
}
