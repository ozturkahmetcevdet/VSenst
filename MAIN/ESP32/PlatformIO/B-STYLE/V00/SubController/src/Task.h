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
      DeserializationError error = deserializeJson(doc, Serial);
      if(error)
      {
          Serial.print(F("Failed to deserialize, reason: \""));
          Serial.print(error.c_str());
          Serial.println('"');
      }
      else
      {
          //Serial.print(F("Recevied valid json document with "));
          //Serial.print(jsonBuffer.size());
          //Serial.println(F(" elements."));
          //Serial.println(F("Pretty printed back at you:"));
          //serializeJsonPretty(jsonBuffer, Serial);
          //Serial.println();
          //const char* dat = jsonBuffer["Record"];
          //Serial.print(dat);
          //Serial.println();

        deserializeJson(jsonBuffer, doc.as<String>());
        
        if(jsonBuffer["Type"].as<uint8_t>() == 0)
        {
          if(jsonBuffer["c"].size())
          {
            for(int j = 0; j < sizeof(graphics.SEAT_CurrentImage); j++)
            {
              if(jsonBuffer["c"][j].size())
              {
                graphics.SEAT_PositionXY[j][0] = jsonBuffer["c"][j][0].as<uint16_t>();
                graphics.SEAT_PositionXY[j][1] = jsonBuffer["c"][j][1].as<uint16_t>();
                graphics.SEAT_Selector[j]      = jsonBuffer["c"][j][2].as<uint8_t>();
              }
              else
                break;
            }
          }
        }
        else if(jsonBuffer["Type"].as<uint8_t>() == 1)
        {
          graphics.PAGE_CurrentImage = jsonBuffer["Page"].as<uint8_t>();
          
          if(graphics.PAGE_CurrentImage == 2)
          {
            uint8_t seatCounter = 0;
            for(int j = 0; j < sizeof(graphics.SEAT_CurrentImage); j++)
            {
              if(jsonBuffer["PxHubs"][String(j)].size())
              {
                if(jsonBuffer["PxHubs"][String(j)][1].size())
                {
                  graphics.SEAT_CurrentImage[jsonBuffer["PxHubs"][String(j)][1][0].as<uint8_t>()] = jsonBuffer["Record"].as<uint8_t>() == 2 ? graphics.REGS_ : 
                                                                                                    jsonBuffer["PxHubs"][String(j)][1][1].as<uint8_t>() &&  jsonBuffer["PxHubs"][String(j)][1][4].as<uint8_t>() ? graphics.FULL_ :
                                                                                                  !jsonBuffer["PxHubs"][String(j)][1][1].as<uint8_t>() && !jsonBuffer["PxHubs"][String(j)][1][4].as<uint8_t>() ? graphics.NULL_ : graphics.PASS_;
                  seatCounter++;
                }
                if(jsonBuffer["PxHubs"][String(j)][2].size())
                {
                  graphics.SEAT_CurrentImage[jsonBuffer["PxHubs"][String(j)][2][0].as<uint8_t>()] = jsonBuffer["Record"].as<uint8_t>() == 2 ? graphics.REGS_ : 
                                                                                                    jsonBuffer["PxHubs"][String(j)][2][1].as<uint8_t>() &&  jsonBuffer["PxHubs"][String(j)][2][4].as<uint8_t>() ? graphics.FULL_ :
                                                                                                  !jsonBuffer["PxHubs"][String(j)][2][1].as<uint8_t>() && !jsonBuffer["PxHubs"][String(j)][2][4].as<uint8_t>() ? graphics.NULL_ : graphics.PASS_;
                  seatCounter++;
                }
              }
            }
            if(seatCounter < sizeof(graphics.SEAT_CurrentImage))
            {
              for(int j = seatCounter; j < sizeof(graphics.SEAT_CurrentImage); j++)
              {
                graphics.SEAT_CurrentImage[j] = graphics.UNRE_;
              }
            }
          }
        }
      }
    }
  }
}
