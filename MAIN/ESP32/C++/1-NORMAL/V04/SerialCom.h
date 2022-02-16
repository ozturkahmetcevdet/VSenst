#include "esp32-hal.h"
#include "ArduinoJson.h"

StaticJsonDocument<20480> jsonBuffer, doc;

void SerialInit()
{
  Serial.setRxBufferSize(16384);
  Serial.begin(2000000);//921600
  while(!Serial);
}
