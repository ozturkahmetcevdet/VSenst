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

    deserializeJson(doc, Serial);
    //serializeJson(doc, Serial);
  }
}
