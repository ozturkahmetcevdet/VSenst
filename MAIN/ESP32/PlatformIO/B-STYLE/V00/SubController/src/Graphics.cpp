#include "Graphics.h"

void Graphics::Init(void)
{
  //ledcSetup(15, 1000, 8);
  //ledcAttachPin(15, 0);
  //ledcWrite(15, 90);

  pinMode(32, OUTPUT);
  digitalWrite(32, LOW);  
  
  if(!EEPROM.begin(EEPROM_SIZE))
  {
    Serial.println("Failed to initialize EEPROM");
    delay(250);
    ESP.restart();
  }
  else
  {
    Serial.println("EEPROM Initialize is done!");
  }

  this->gfxLcd.init();
  this->gfxLcd.begin();               
  this->gfxLcd.setRotation(0);
  //uint16_t calData[5] = { 331, 3397, 248, 3453, 4 };
  //this->gfxLcd.setTouch(calData);
  this->TouchCalibrate();

  this->gfxLcd.fillScreen(TFT_BLACK);
  this->gfxLcd.setSwapBytes(true);
}

void Graphics::Loop(bool enable)
{
  uint16_t x, y;
  if (this->gfxLcd.getTouch(&x, &y, 150))
  {
    if((x >= this->WIFI_PositionXY[0]) && (x <= this->WIFI_PositionXY[0] + this->WIFI_Size[0]) &&\
       (y >= this->WIFI_PositionXY[1]) && (y <= this->WIFI_PositionXY[1] + this->WIFI_Size[1]))
    {
      this->WIFI_TouchActivity = true;
    }
  }
  if(!enable)
    return;
  
  this->BufferCheck();    
  if(this->PAGE_ImageProcess)
  {
    this->gfxLcd.fillScreen(TFT_BLACK);
  }
  this->SetBitmap(this->PAGE_PositionXY[this->PAGE_CurrentImage - 1], this->PAGE_Size[this->PAGE_CurrentImage - 1], this->PAGE_NameList[this->PAGE_CurrentImage - 1], this->PAGE_ImageProcess);
  for(int j = 0; j < sizeof(this->SEAT_CurrentImage); j++)
  {
    this->SetBitmap(this->SEAT_PositionXY[j], this->SEAT_Size[this->SEAT_Selector[j] - 1], this->SEAT_NameList[this->SEAT_Selector[j] - 1][this->SEAT_CurrentImage[j] - 1], this->SEAT_ImageProcess[j]);
  }
  this->SetBitmap(this->BATTERY_PositionXY, this->BATTERY_Size, this->BATTERY_NameList[this->BATTERY_CurrentImage - 1], this->BATTERY_ImageProcess);
  this->SetBitmap(this->WIFI_PositionXY, this->WIFI_Size, this->WIFI_NameList[this->WIFI_CurrentImage - 1], this->WIFI_ImageProcess);
  this->SetBitmap(this->GPS_PositionXY, this->GPS_Size, this->GPS_NameList[this->GPS_CurrentImage - 1], this->GPS_ImageProcess);
}

void Graphics::Backlight(bool enable)
{
  digitalWrite(32, enable ? HIGH : LOW);
}

void Graphics::Clear(const uint16_t* position, const uint16_t* size, uint16_t color)
{
  this->gfxLcd.fillRect(position[0], position[1], size[0], size[1], color);
}

void Graphics::Text(String txt, const uint16_t* position, uint16_t txtColor, uint16_t backColor)
{
  this->gfxLcd.setCursor(position[0], position[1]);
  this->gfxLcd.setTextColor(txtColor, backColor);
  this->gfxLcd.println(txt);
}
