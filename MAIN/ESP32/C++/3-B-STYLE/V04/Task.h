void TaskSerial()
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
        Serial.print(F("Recevied valid json document with "));
        Serial.print(jsonBuffer.size());
        Serial.println(F(" elements."));
        Serial.println(F("Pretty printed back at you:"));
        serializeJsonPretty(jsonBuffer, Serial);
        Serial.println();
        const char* dat = jsonBuffer["Record"];
        Serial.print(dat);
        Serial.println();

      deserializeJson(jsonBuffer, doc.as<String>());
      
      if(jsonBuffer["Type"].as<uint8_t>() == 1)
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
                graphics.SEAT_CurrentImage[jsonBuffer["PxHubs"][String(j)][1][0].as<uint8_t>()] = jsonBuffer["Record"].as<uint8_t>() == 2 ? 6 : jsonBuffer["PxHubs"][String(j)][1][2].as<uint8_t>() + (jsonBuffer["PxHubs"][String(j)][1][5].as<uint8_t>() ? 1 : 3);
                graphics.SEAT_CurrentProcessImage[jsonBuffer["PxHubs"][String(j)][1][0].as<uint8_t>()] = jsonBuffer["Record"].as<uint8_t>() == 2 ? 1 : jsonBuffer["PxHubs"][String(j)][6].as<uint8_t>() > 0 ? 5 - (jsonBuffer["PxHubs"][String(j)][6].as<uint8_t>() / 25) : 6;
                graphics.SEAT_CurrentProcessImage[jsonBuffer["PxHubs"][String(j)][1][0].as<uint8_t>()] = jsonBuffer["Record"].as<uint8_t>() == 2 ? 1 : jsonBuffer["PxHubs"][String(j)][1][1].as<uint8_t>() ? 7 : graphics.SEAT_CurrentProcessImage[jsonBuffer["PxHubs"][String(j)][1][0].as<uint8_t>()];
                graphics.SEAT_Animation[jsonBuffer["PxHubs"][String(j)][1][0].as<uint8_t>()] = ((jsonBuffer["PxHubs"][String(j)][6].as<uint8_t>() < 1) || (jsonBuffer["PxHubs"][String(j)][2][1].as<uint8_t>())) && (jsonBuffer["Record"].as<uint8_t>() != 2);
                seatCounter++;
              }
              if(jsonBuffer["PxHubs"][String(j)][2].size())
              {
                graphics.SEAT_CurrentImage[jsonBuffer["PxHubs"][String(j)][2][0].as<uint8_t>()] = jsonBuffer["Record"].as<uint8_t>() == 2 ? 6 : jsonBuffer["PxHubs"][String(j)][2][2].as<uint8_t>() + (jsonBuffer["PxHubs"][String(j)][2][5].as<uint8_t>() ? 1 : 3);
                graphics.SEAT_CurrentProcessImage[jsonBuffer["PxHubs"][String(j)][2][0].as<uint8_t>()] = jsonBuffer["Record"].as<uint8_t>() == 2 ? 1 : jsonBuffer["PxHubs"][String(j)][6].as<uint8_t>() > 0 ? 5 - (jsonBuffer["PxHubs"][String(j)][6].as<uint8_t>() / 25) : 6;
                graphics.SEAT_CurrentProcessImage[jsonBuffer["PxHubs"][String(j)][2][0].as<uint8_t>()] = jsonBuffer["Record"].as<uint8_t>() == 2 ? 1 : jsonBuffer["PxHubs"][String(j)][2][1].as<uint8_t>() ? 7 : graphics.SEAT_CurrentProcessImage[jsonBuffer["PxHubs"][String(j)][2][0].as<uint8_t>()];
                graphics.SEAT_Animation[jsonBuffer["PxHubs"][String(j)][2][0].as<uint8_t>()] = ((jsonBuffer["PxHubs"][String(j)][6].as<uint8_t>() < 1) || (jsonBuffer["PxHubs"][String(j)][2][1].as<uint8_t>())) && (jsonBuffer["Record"].as<uint8_t>() != 2);
                seatCounter++;
              }
            }
          }
          if(seatCounter < sizeof(graphics.SEAT_CurrentImage))
          {
            for(int j = seatCounter; j < sizeof(graphics.SEAT_CurrentImage); j++)
            {
              graphics.SEAT_Animation[j] = false;
              graphics.SEAT_CurrentImage[j] = jsonBuffer["Record"].as<uint8_t>() == 2 ? 5 : 7;
              graphics.SEAT_CurrentProcessImage[j] = 1;
            }
          }
        }
      }
    }
  }
}
