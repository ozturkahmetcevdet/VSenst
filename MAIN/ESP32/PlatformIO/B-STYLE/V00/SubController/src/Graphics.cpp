#include "Graphics.h"

void Graphics::Init(void)
{
  //ledcSetup(15, 1000, 8);
  //ledcAttachPin(15, 0);
  //ledcWrite(15, 90);

  pinMode(32, OUTPUT);
  digitalWrite(32, LOW);

  this->gfxLcd.init();
  this->gfxLcd.begin();               
  this->gfxLcd.setRotation(0);
  uint16_t calData[5] = { 331, 3397, 248, 3453, 4 };
  this->gfxLcd.setTouch(calData);

  this->gfxLcd.fillScreen(TFT_BLACK);
  this->gfxLcd.setSwapBytes(true);
}

void Graphics::Loop(bool enable)
{
  /*uint16_t x, y;
  if (this->gfxLcd.getTouch(&x, &y, 0))
  {
    Serial.println();
    Serial.print("x:\t");
    Serial.print(x);
    Serial.print("\t\ty:\t");
    Serial.print(y);
  }*/
  if(!enable)
    return;
  
  this->BufferCheck();    
  if(this->PAGE_ImageProcess)
  {
    this->gfxLcd.fillScreen(TFT_BLACK);
  }
  this->SetBitmap(this->PAGE_PositionXY[this->PAGE_CurrentImage - 1][0], this->PAGE_PositionXY[this->PAGE_CurrentImage - 1][1], this->PAGE_Size[this->PAGE_CurrentImage - 1][0], this->PAGE_Size[this->PAGE_CurrentImage - 1][1], this->PAGE_NameList[this->PAGE_CurrentImage - 1], this->PAGE_ImageProcess);
  for(int j = 0; j < sizeof(this->SEAT_CurrentImage); j++)
  {
    this->SetBitmap(this->SEAT_PositionXY[j][0], this->SEAT_PositionXY[j][1], this->SEAT_Size[this->SEAT_Selector[j] - 1][0], this->SEAT_Size[this->SEAT_Selector[j] - 1][1], this->SEAT_NameList[this->SEAT_Selector[j] - 1][this->SEAT_CurrentImage[j] - 1], this->SEAT_ImageProcess[j]);
  }
  this->SetBitmap(this->BATTERY_PositionXY[0], this->BATTERY_PositionXY[1], this->BATTERY_Size[0], this->BATTERY_Size[1], this->BATTERY_NameList[this->BATTERY_CurrentImage - 1], this->BATTERY_ImageProcess);
  this->SetBitmap(this->WIFI_PositionXY[0], this->WIFI_PositionXY[1], this->WIFI_Size[0], this->WIFI_Size[1], this->WIFI_NameList[this->WIFI_CurrentImage - 1], this->WIFI_ImageProcess);
  this->SetBitmap(this->GPS_PositionXY[0], this->GPS_PositionXY[1], this->GPS_Size[0], this->GPS_Size[1], this->GPS_NameList[this->GPS_CurrentImage - 1], this->GPS_ImageProcess);
}

void Graphics::Backlight(bool enable)
{
  digitalWrite(32, enable ? HIGH : LOW);
}
