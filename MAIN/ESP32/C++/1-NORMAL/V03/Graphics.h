#include "Importer.h"
#include <TFT_eSPI.h>  
#include <XPT2046_Touchscreen.h> /* https://github.com/PaulStoffregen/XPT2046_Touchscreen */

#define TOUCH_CS_PIN  14
#define TOUCH_IRQ_PIN 27  

class Graphics
{ 
  private:    
    const short unsigned int* PAGE_NameList[4] = {Page_0_1, Page_1, Page_Bye, Page_Alarm};
    const uint16_t PAGE_Width = 240;
    const uint16_t PAGE_Height = 320;
    const uint16_t PAGE_PositionXY[2] = {0, 0};
    byte PAGE_LastImage = 255;
    bool PAGE_ImageProcess = false;
  public:
    byte PAGE_CurrentImage = 1;


  private:    
    const short unsigned int* SEAT_NameList[9] = {Seat_Ok, Seat_Unregistered, Seat_Registered, Seat_Red, Seat_Green, Seat_Yellow, Seat_Fault, Seat_Fault, Seat_Fault};


  private:    
    const short unsigned int* REC_NameList[3] = {Mode_Null, Mode_Record, Mode_Service};
    const uint16_t REC_Width = 115;
    const uint16_t REC_Height = 30;
    const uint16_t REC_PositionXY[2] = {96, 6};
    byte REC_LastImage = 255;
    bool REC_ImageProcess = false;
  public:
    byte REC_CurrentImage = 1;
    
    
  private:    
    const short unsigned int* IGN_NameList[2] = {Ignition_On, Ignition_Off};
    const uint16_t IGN_Width = 20;
    const uint16_t IGN_Height = 35;
    const uint16_t IGN_PositionXY[2] = {11, 5};
    byte IGN_LastImage = 255;
    bool IGN_ImageProcess = false;
  public:
    byte IGN_CurrentImage = 1;
    

  private:
    TFT_eSPI gfxLcd = TFT_eSPI();
    
  public:
    TS_Point rawLocation;

  public:
    bool ImageProcess = true;
    Graphics(){}
    void Init(void);
    void Loop(bool enable);
    void Backlight(bool enable);

  private:
    inline void SetBitmap(int x, int y, int width, int height, const short unsigned int* image, bool imageProcess)
    {
      if(!imageProcess)
        return;
        
      this->gfxLcd.pushImage(x, y, width, height, image);
    }
    
    inline void BufferCheck()
    {
      this->PAGE_ImageProcess = this->PAGE_CurrentImage != this->PAGE_LastImage && this->PAGE_LastImage != 0;
      
      if(this->PAGE_CurrentImage != 2)
      {
        this->COUNTER_LastImage = 0;
        for(int j = 0; j < sizeof(this->SEAT_CurrentImage); j++)
          this->SEAT_LastImage[j] = 0;
        this->REC_LastImage = 0;
        this->IGN_LastImage = 0;
      }
      else if(this->PAGE_CurrentImage == 2 && this->PAGE_CurrentImage != this->PAGE_LastImage)
      {
        this->COUNTER_LastImage = 255;
        for(int j = 0; j < sizeof(this->SEAT_CurrentImage); j++){
          this->SEAT_LastImage[j] = 255;
        }
        this->REC_LastImage = 255;
        this->IGN_LastImage = 255;
      }
      
      this->PAGE_LastImage = this->PAGE_LastImage != 0 ? this->PAGE_CurrentImage : this->PAGE_LastImage;   
      
      for(int j = 0; j < sizeof(this->SEAT_CurrentImage); j++)
      {
        this->SEAT_ImageProcess[j] = this->SEAT_CurrentImage[j] != this->SEAT_LastImage[j] && this->SEAT_LastImage[j] != 0;  
        this->SEAT_LastImage[j] = this->SEAT_LastImage[j] != 0 ? this->SEAT_CurrentImage[j] : this->SEAT_LastImage[j];
      }
      
      this->REC_ImageProcess = this->REC_CurrentImage != this->REC_LastImage && this->REC_LastImage != 0;
      this->REC_LastImage = this->REC_LastImage != 0 ? this->REC_CurrentImage : this->REC_LastImage;      
      
      this->COUNTER_ImageProcess = this->COUNTER_CurrentImage != this->COUNTER_LastImage && this->COUNTER_LastImage != 0;
      this->COUNTER_LastImage = this->COUNTER_LastImage != 0 ? this->COUNTER_CurrentImage : this->COUNTER_LastImage;
      
      this->IGN_ImageProcess = this->IGN_CurrentImage != this->IGN_LastImage && this->IGN_LastImage != 0;
      this->IGN_LastImage = this->IGN_LastImage != 0 ? this->IGN_CurrentImage : this->IGN_LastImage;
    }
};
