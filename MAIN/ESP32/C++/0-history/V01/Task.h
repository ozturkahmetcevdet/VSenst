void TaskSerial(void *ignore)
{
  while(true)
  {
    TIMERG0.wdt_wprotect= TIMG_WDT_WKEY_VALUE;
    TIMERG0.wdt_feed = 1;
    TIMERG0.wdt_wprotect = 0;
    
    TIMERG1.wdt_wprotect= TIMG_WDT_WKEY_VALUE;
    TIMERG1.wdt_feed = 1;
    TIMERG1.wdt_wprotect = 0;

    if(Serial.available())
    {
      stringCommand = Serial.readStringUntil(0xFF);
      while(Serial.read() == 0xFF);
      Serial.println(stringCommand);
      stringCommand.toCharArray(m_buffer, 14);

      /*portENTER_CRITICAL_ISR(&mux);
      m_Int = false;
      portEXIT_CRITICAL_ISR(&mux);*/
  
      if(m_buffer[0] == 'p')
      {
          graphics.PAGE_CurrentImage = m_buffer[5] == 'F' ? 3 : m_buffer[5] == 'a' ? 4 : m_buffer[5] == '0' ? 2 : m_buffer[5] == 'b' ? 5 :  m_buffer[5] == '1' ? 3 : graphics.PAGE_CurrentImage;
      }
      else if(m_buffer[2] == 'a')
      {
          byte seatNumber = (m_buffer[4] - 48) * (m_buffer[5] == '.' ? 1 : 10) + (m_buffer[5] == '.' ? 0 : (m_buffer[5] - 48)) - 1;

          if(seatNumber < sizeof(graphics.SEAT_CurrentImage))
          {
            String seatNumberString = stringCommand.substring(10 + (seatNumber > 8 ? 1 : 0), 12 + (seatNumber > 8 ? 1 : 0));
            graphics.SEAT_CurrentImage[seatNumber] = seatNumberString == "8"   ? 5  : seatNumberString == "9"  ? 5  : \
                                                     seatNumberString == "10"  ? 4  : seatNumberString == "11" ? 1  : \
                                                     seatNumberString == "12"  ? 2  : seatNumberString == "13" ? 3  : \
                                                     seatNumberString == "14"  ? 3  : seatNumberString == "15" ? 2  : \
                                                     seatNumberString == "16"  ? 5  : graphics.SEAT_CurrentImage[seatNumber];
          }
      }
      else if(m_buffer[1] == 'e')
      {
          graphics.REC_CurrentImage = m_buffer[9] == '0' ? 1 : m_buffer[9] == '1' ? 2 : \
                                      m_buffer[9] == '2' ? 3 : graphics.REC_CurrentImage;           
      }
      else if(m_buffer[0] == 'c')
      {
          byte countNumber = (m_buffer[8] > 47 && m_buffer[8] < 58 ? (m_buffer[8] - 48) : 0) + \
                             (m_buffer[7] > 47 && m_buffer[7] < 58 ? ((m_buffer[7] - 48) * ((m_buffer[8] > 47 && m_buffer[8] < 58) ? 10 : 1)) : 0) + \
                             (m_buffer[6] > 47 && m_buffer[6] < 58 ? ((m_buffer[6] - 48) * ((m_buffer[8] > 47 && m_buffer[8] < 58) && (m_buffer[7] > 47 && m_buffer[7] < 58) ? 100 : ((m_buffer[7] > 47 && m_buffer[7] < 58) ? 10 : 1))) : 0);
          graphics.COUNTER_CurrentImage = countNumber > 83 && countNumber < (sizeof(graphics.SEAT_CurrentImage) + 84) ? countNumber - 84 + 1 : graphics.COUNTER_CurrentImage;
          //Serial.printf("Received Number: %u, Calculated Number: %u\n\r", countNumber, graphics.COUNTER_CurrentImage);
      }
      else if(m_buffer[0] == 'i')
      {
          graphics.IGN_CurrentImage = m_buffer[8] == '2' ? 1 : m_buffer[8] == '3' ? 2 : graphics.IGN_CurrentImage;
      }
      else if(m_buffer[0] == 'd')
      {
          graphics.DOOR_CurrentImage = m_buffer[10] == '2' ? 1 : m_buffer[10] == '3' ? 2 : graphics.DOOR_CurrentImage;
      }
      else if(m_buffer[4] == 'p')
      {
          if(m_buffer[6] == '1')
          {
              graphics.Backlight(false);
          }
          else if(m_buffer[6] == '0')
          {
            graphics.Backlight(true);  
          }
      }
  
      memset(m_buffer, 0x00, 14);
    }
  }
}
