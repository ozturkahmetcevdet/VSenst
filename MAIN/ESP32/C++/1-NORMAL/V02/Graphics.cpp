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
  this->SetBitmap(this->PAGE_PositionXY[0], this->PAGE_PositionXY[1], this->PAGE_Width, this->PAGE_Height, this->PAGE_NameList[this->PAGE_CurrentImage - 1], this->PAGE_ImageProcess);
  this->SetBitmap(this->COUNTER_PositionXY[0], this->COUNTER_PositionXY[1], this->COUNTER_Width, this->COUNTER_Height, this->COUNTER_NameList[this->COUNTER_CurrentImage - 1], this->COUNTER_ImageProcess);
  for(int j = 0; j < sizeof(this->SEAT_CurrentImage); j++)
  {
    this->SetBitmap(this->SEAT_PositionXY[j][0], this->SEAT_PositionXY[j][1], this->SEAT_Width, this->SEAT_Height, this->SEAT_NameList[this->SEAT_CurrentImage[j] - 1], this->SEAT_ImageProcess[j]);
  }
  this->SetBitmap(this->REC_PositionXY[0], this->REC_PositionXY[1], this->REC_Width, this->REC_Height, this->REC_NameList[this->REC_CurrentImage - 1], this->REC_ImageProcess);
  this->SetBitmap(this->IGN_PositionXY[0], this->IGN_PositionXY[1], this->IGN_Width, this->IGN_Height, this->IGN_NameList[this->IGN_CurrentImage - 1], this->IGN_ImageProcess);
}

void Graphics::Backlight(bool enable)
{
  digitalWrite(32, enable ? HIGH : LOW);
}
