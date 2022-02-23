#include "main.hpp"
#include <Arduino.h>
#include "Graphics.h"
#include <soc/rtc.h>

#include <ESP_WiFiManager.h>
#include <HTTPClient.h>
#include <HTTPUpdate.h>
#include <WiFiClientSecure.h>
#include "cert.h"

Graphics graphics;

#include "soc/timer_group_struct.h"
#include "soc/timer_group_reg.h"

#include "SerialCom.h"
#include "Task.h"

struct Timer
{
  unsigned long base;
  unsigned long ms_100;
  const unsigned long _ms_100 = 100;
  unsigned long ms_500;
  const unsigned long _ms_500 = 500;
  unsigned long ms_1000;
  const unsigned long _ms_1000 = 1000;
  unsigned long ms_2500;
  const unsigned long _ms_2500 = 2500;
  unsigned long ms_5000;
  const unsigned long _ms_5000 = 5000;
  unsigned long ms_10000;
  const unsigned long _ms_10000 = 10000;
  unsigned long ms_60000;
  const unsigned long _ms_60000 = 60000;
}Timer;
               

ESP_WiFiManager *wifiManager;
char *DEVICE_ID;  

void setup(void) 
{
  SerialInit();
  graphics.Init();
  //graphics.Backlight(true);
  xTaskCreatePinnedToCore(&TaskSerial  , "SER_task", 9216, NULL, 1, NULL, 0);  

  SetDeviceUniqId();
  StartWifiManager();

  delay(250);
  Serial.println("BOOT");
  delay(250);
}

void loop()
{
  //TaskSerial();
  graphics.Loop(graphics.ImageProcess);
  TimerLoop();
  vTaskDelay(50);
}

void TouchActivity()
{
  if(graphics.WIFI_TouchActivity)
  {
    ResetWifiManager();
    /*Serial.println("uOTA start");
    delay(10);
    Serial.println("FName@test.py");
    delay(10);
    Serial.print("import utime\r\n\r\ndef foo():\r\n\treturn str(foo())\r\n\r\ndef test():\r\n\ta = 3\r\n\tb = 5\r\n\treturn a + b");
    delay(10);
    Serial.println("uOTA end");*/
    graphics.WIFI_TouchActivity = false;
  }
}

void TimerLoop()
{
  Timer.base = millis();
  if(Timer.base - Timer.ms_100 > Timer._ms_100)
  {
    Timer.ms_100 = Timer.base;
    TouchActivity();
  }
  if(Timer.base - Timer.ms_500 > Timer._ms_500)
  {
    Timer.ms_500 = Timer.base;
  }
  if(Timer.base - Timer.ms_1000 > Timer._ms_1000)
  {
    Timer.ms_1000 = Timer.base;
  }
  if(Timer.base - Timer.ms_2500 > Timer._ms_2500)
  {
    Timer.ms_2500 = Timer.base;
    ReadAndShowRssiStrength();
  }
  if(Timer.base - Timer.ms_5000 > Timer._ms_5000)
  {
    Timer.ms_5000 = Timer.base;
  }
  if(Timer.base - Timer.ms_10000 > Timer._ms_10000)
  {
    Timer.ms_10000 = Timer.base;
  }
  if(Timer.base - Timer.ms_60000 > Timer._ms_60000)
  {
    Timer.ms_60000 = Timer.base;    
    FirmwareUpdate(FirmwareVersionCheck());
  }
}

void SetDeviceUniqId()
{
  uint8_t mac[6];
  DEVICE_ID = (char *)malloc(18);
  esp_efuse_mac_get_default(mac);
  snprintf(DEVICE_ID, 18, "%02x%02x%02x%02x%02x%02x", mac[0], mac[1], mac[2], mac[3], mac[4], mac[5]);
  Serial.println("Device ID is: " + String(DEVICE_ID));
}

void StartWifiManager()
{
  wifiManager = new ESP_WiFiManager(DEVICE_ID);
  //wifiManager->resetSettings();
  //wifiManager->autoConnect(DEVICE_ID);

  WiFi.begin();
  if (WiFi.psk() != "" && WiFi.psk() != "0")
  {
    Serial.print("Trying to connect with previous Wifi");
    Serial.println("Previous Password: " + WiFi.psk());
    for (int i = 0; i < 60; i++)
    {
      delay(50);
      Serial.print(".");
      if (WiFi.status() == WL_CONNECTED)
        break;
    }
    if (WiFi.status() == WL_CONNECTED)
    {
      Serial.println("Connected with " + WiFi.SSID());
    }
    else
    {
      Serial.println("Not connected!");
    }
  }
  else
  {
    Serial.println("No previous credentials detected. Continuing in offline mode");
  }

  ReadAndShowRssiStrength();
}

void ResetWifiManager()
{
  graphics.WIFI_CurrentImage = 1;
  wifiManager->resetSettings();
  wifiManager->setTimeout(180);
  const uint16_t txtPos[2] = {4, 32};
  const uint16_t clrSze[2] = {232, 12};
  graphics.Clear(txtPos, clrSze, TFT_BLACK);
  graphics.Text("SSID: " + String(DEVICE_ID), txtPos, TFT_GREEN, TFT_BLACK);

  Serial.println(F("\nCleared wifi configuration. Starting configuration portal."));

  wifiManager->startConfigPortal(DEVICE_ID);
  if (WiFi.status() == WL_CONNECTED)
  {
    graphics.Clear(txtPos, clrSze, TFT_BLACK);
    Serial.print(F("\nConnected. Local IP: "));
    Serial.println(WiFi.localIP());
  }
  else
  {
    graphics.Clear(txtPos, clrSze, TFT_BLACK);
    graphics.Text(wifiManager->getStatus(WiFi.status()), txtPos, TFT_YELLOW, TFT_BLACK);
    Serial.println(wifiManager->getStatus(WiFi.status()));
    delay(1000);
    graphics.Clear(txtPos, clrSze, TFT_BLACK);
  }
  ReadAndShowRssiStrength();
}

void ReadAndShowRssiStrength()
{
  if (WiFi.status() == WL_CONNECTED)
  {
    int rssi = WiFi.RSSI();
    rssi = rssi <= -100 ? 0 : rssi >= -50 ? 100 : 2 * (rssi + 100);
    if(rssi > 75)
      graphics.WIFI_CurrentImage = 2;
    else if(rssi > 50)
      graphics.WIFI_CurrentImage = 3;
    else if(rssi > 25)
      graphics.WIFI_CurrentImage = 4;
    else
      graphics.WIFI_CurrentImage = 5;
  }
  else if (WiFi.getMode() == WIFI_MODE_AP || WiFi.getMode() == WIFI_MODE_APSTA)
  {
    graphics.WIFI_CurrentImage = 1;
  }
  else
  {
    graphics.WIFI_CurrentImage = 1;
  }
}

void FirmwareUpdate(bool activity)
{
  if(!activity)
    return;

  WiFiClientSecure client;
  client.setCACert(rootCACertificate);
  t_httpUpdate_return ret = httpUpdate.update(client, URL_Fw_Bin);

  switch (ret)
  {
  case HTTP_UPDATE_FAILED:
    Serial.printf("HTTP_UPDATE_FAILD Error (%d): %s\n", httpUpdate.getLastError(), httpUpdate.getLastErrorString().c_str());
    break;

  case HTTP_UPDATE_NO_UPDATES:
    Serial.println("HTTP_UPDATE_NO_UPDATES");
    break;

  case HTTP_UPDATE_OK:
    Serial.println("HTTP_UPDATE_OK");
    delay(2000);
    esp_restart();
    break;
  }
}

int FirmwareVersionCheck()
{
  if (WiFi.status() != WL_CONNECTED)
    return 0;

  String payload;
  int httpCode;
  String fwurl = "";
  fwurl += URL_Fw_Version;
  fwurl += "?";
  fwurl += String(rand());
  Serial.println(fwurl);
  WiFiClientSecure *client = new WiFiClientSecure;

  if (client)
  {
    client->setCACert(rootCACertificate);

    // Add a scoping block for HTTPClient https to make sure it is destroyed before WiFiClientSecure *client is
    HTTPClient https;

    if (https.begin(*client, fwurl))
    { // HTTPS
      Serial.print("[HTTPS] GET...\n");
      // start connection and send HTTP header
      delay(100);
      httpCode = https.GET();
      delay(100);
      if (httpCode == HTTP_CODE_OK) // if version received
      {
        payload = https.getString(); // save received version
      }
      else
      {
        Serial.print("error in downloading version file:");
        Serial.println(httpCode);
      }
      https.end();
    }
    delete client;
  }

  if (httpCode == HTTP_CODE_OK) // if version received
  {
    payload.trim();
    if (payload.equals(FirmwareVersion))
    {
      Serial.printf("\nDevice already on latest firmware version:%s\n", FirmwareVersion);
      return 0;
    }
    else
    {
      Serial.println(payload);
      Serial.println("New firmware detected");
      return 1;
    }
  }
  return 0;
}