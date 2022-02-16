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
      stringCommand.toCharArray(charArray, 14);
      //Serial.println(charArray);

      byte arrayNum;
      byte arrayVal;
      switch(charArray[0])
      {
        case 'P':
          graphics.PAGE_CurrentImage = charArray[2] - 48;
        break;
        
        case 'I':
          graphics.IGN_CurrentImage = charArray[2] - 48;
        break;
        
        case 'S':
          if(charArray[3] == '.')
          {
            arrayNum = charArray[2] - 48;
            arrayVal = charArray[4] - 48;
          }
          else if(charArray[4] == '.')
          {
            arrayNum = (charArray[2] - 48) * 10 + (charArray[3] - 48);
            arrayVal = charArray[5] - 48;
          }
          if(arrayNum > (sizeof(graphics.SEAT_CurrentImage) - 1))
            break;
          graphics.SEAT_CurrentImage[arrayNum] = arrayVal;
        break;
        
        case 'B':
          if(charArray[3] == '.')
          {
            arrayNum = charArray[2] - 48;
            arrayVal = charArray[4] - 48;
          }
          else if(charArray[4] == '.')
          {
            arrayNum = (charArray[2] - 48) * 10 + (charArray[3] - 48);
            arrayVal = charArray[5] - 48;
          }
          if(arrayNum > (sizeof(graphics.BELT_CurrentImage) - 1))
            break;
          graphics.BELT_CurrentImage[arrayNum] = arrayVal;
        break;
        
        case 'R':
          graphics.REC_CurrentImage = charArray[2] - 48;
        break;
        
        case 'L':
          graphics.Backlight(charArray[2] - 48);
        break;
      }
      
      memset(charArray, 0x00, 14);
      
      
    }
  }
}
