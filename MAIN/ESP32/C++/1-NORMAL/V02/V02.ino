#include "Graphics.h"
#include <soc/rtc.h>

Graphics graphics;

#include "soc/timer_group_struct.h"
#include "soc/timer_group_reg.h"

#include "SerialCom.h"
#include "Task.h"
               
  

void setup(void) {
  //rtc_clk_cpu_freq_set(RTC_CPU_FREQ_240M);
  delay(10);
  SerialInit();
  graphics.Init();
  xTaskCreatePinnedToCore(&TaskSerial  , "SER_task", 1536, NULL, 1, NULL, 0);  
}

void loop()
{
  graphics.Loop(graphics.ImageProcess);
}
