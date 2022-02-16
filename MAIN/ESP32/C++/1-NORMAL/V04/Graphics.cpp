#include "Graphics.h"

XPT2046_Touchscreen touch(TOUCH_CS_PIN, TOUCH_IRQ_PIN);

void Graphics::Init(void)
{
  //ledcSetup(15, 1000, 8);
  //ledcAttachPin(15, 0);
  //ledcWrite(15, 90);

  pinMode(32, OUTPUT);
  digitalWrite(32, LOW);

  touch.begin();
  touch.setRotation(1);
  
  this->gfxLcd.begin();               
  this->gfxLcd.setRotation(0);

  this->gfxLcd.fillScreen(TFT_BLACK);
  this->gfxLcd.setSwapBytes(true);
}

void Graphics::Loop(bool enable)
{
  if(!enable)
    return;
  
  this->BufferCheck();    
  this->SetBitmap(this->PAGE_CurrentImage == 2 ? this->PAGE_MainPositionXY[0] : this->PAGE_PositionXY[0], this->PAGE_CurrentImage == 2 ? this->PAGE_MainPositionXY[1] : this->PAGE_PositionXY[1], this->PAGE_CurrentImage == 2 ? this->PAGE_MainWidth : this->PAGE_Width, this->PAGE_CurrentImage == 2 ? this->PAGE_MainHeight : this->PAGE_Height, this->PAGE_NameList[this->PAGE_CurrentImage - 1], this->PAGE_ImageProcess);
  for(int j = 0; j < sizeof(this->SEAT_CurrentImage); j++)
  {
    this->SetBitmap(this->SEAT_PositionXY[j][0], this->SEAT_PositionXY[j][1], this->SEAT_Width, this->SEAT_Height, this->SEAT_NameList[this->SEAT_CurrentProcessImage[j] - 1][this->SEAT_CurrentImage[j] - 1], this->SEAT_ImageProcess[j]);
  }
}

void Graphics::Backlight(bool enable)
{
  digitalWrite(32, enable ? HIGH : LOW);
}
