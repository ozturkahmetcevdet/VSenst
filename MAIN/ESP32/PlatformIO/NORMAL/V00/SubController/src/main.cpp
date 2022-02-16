#include <Arduino.h>
#include "Graphics.h"
#include <soc/rtc.h>

Graphics graphics;

#include "soc/timer_group_struct.h"
#include "soc/timer_group_reg.h"

#include "SerialCom.h"
#include "Task.h"
               
  

void setup(void) {
  SerialInit();
  graphics.Init();
  //graphics.Backlight(true);
  //xTaskCreatePinnedToCore(&TaskSerial  , "SER_task", 1536, NULL, 1, NULL, 0);  
}

void loop()
{
  TaskSerial();
  graphics.Loop(graphics.ImageProcess);
}
