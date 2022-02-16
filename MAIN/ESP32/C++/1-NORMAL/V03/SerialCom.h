#include "esp32-hal.h"
#include "ArduinoJson.h"

StaticJsonDocument<22000> doc;

void SerialInit()
{
  Serial.setRxBufferSize(8192);
  Serial.begin(2000000);//921600
  while(!Serial);
}
