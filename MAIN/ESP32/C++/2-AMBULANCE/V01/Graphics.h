#include "Importer.h"
#include <TFT_eSPI.h>
#include <XPT2046_Touchscreen.h> /* https://github.com/PaulStoffregen/XPT2046_Touchscreen */

#define TOUCH_CS_PIN  14
#define TOUCH_IRQ_PIN 27  

#define SEAT_COUNT_1
//#define SEAT_COUNT_2
//#define SEAT_COUNT_3
//#define SEAT_COUNT_4


class Graphics
{ 
  private:    
    #ifdef SEAT_COUNT_1
    const short unsigned int* PAGE_NameList[3] = {IMG_0, IMG_1_1, IMG_20};
    #elif SEAT_COUNT_2
    
    #elif SEAT_COUNT_3
    const short unsigned int* PAGE_NameList[3] = {IMG_0, IMG_1, IMG_20};
    #elif SEAT_COUNT_4
    #endif
    const uint16_t PAGE_Width = 240;
    const uint16_t PAGE_Height = 320;
    const uint16_t PAGE_PositionXY[2] = {0, 0};
    byte PAGE_LastImage = 255;
    bool PAGE_ImageProcess = false;
  public:
    byte PAGE_CurrentImage = 1;


  private:    
    const short unsigned int* SEAT_NameList[4] = {IMG_8, IMG_9, IMG_10, IMG_11};
    const uint16_t SEAT_Width = 65;
    const uint16_t SEAT_Height = 65;
    
    #ifdef SEAT_COUNT_1
    const uint16_t SEAT_PositionXY[1][2] = {
      {120 ,  127}
    };
    byte SEAT_LastImage[1] = {255};
    bool SEAT_ImageProcess[1] = {false};
  public:
    byte SEAT_CurrentImage[1] = {2};
    
    #elif SEAT_COUNT_2
    
    #elif SEAT_COUNT_3
    const uint16_t SEAT_PositionXY[3][2] = {
      {120 ,  27}, {120 ,  127}, {120 ,  227}
    };
    byte SEAT_LastImage[3] = {255, 255, 255};
    bool SEAT_ImageProcess[3] = {false, false, false};
  public:
    byte SEAT_CurrentImage[3] = {2, 2, 2};
    
    #elif SEAT_COUNT_4
    #endif

  private:    
    const short unsigned int* BELT_NameList[3] = {IMG_12, IMG_13, IMG_14};
    const uint16_t BELT_Width = 65;
    const uint16_t BELT_Height = 65;
    
    #ifdef SEAT_COUNT_1
    const uint16_t BELT_PositionXY[1][2] = {
      {46 ,  127}
    };
    byte BELT_LastImage[1] = {255};
    bool BELT_ImageProcess[1] = {false};
  public:
    byte BELT_CurrentImage[1] = {1};
    
    #elif SEAT_COUNT_2
    
    #elif SEAT_COUNT_3
    const uint16_t BELT_PositionXY[3][2] = {
      {46 ,  27}, {46 ,  127}, {46 ,  227}
    };
    byte BELT_LastImage[3] = {255, 255, 255};
    bool BELT_ImageProcess[3] = {false, false, false};
  public:
    byte BELT_CurrentImage[3] = {1, 1, 1};
    
    #elif SEAT_COUNT_4
    #endif


  private:    
    const short unsigned int* REC_NameList[2] = {IMG_4, IMG_5};
    const uint16_t REC_Width = 30;
    const uint16_t REC_Height = 84;
    const uint16_t REC_PositionXY[2] = {207, 236};
    byte REC_LastImage = 255;
    bool REC_ImageProcess = false;
  public:
    byte REC_CurrentImage = 1;
    
    
  private:    
    const short unsigned int* IGN_NameList[2] = {IMG_3, IMG_2};
    const uint16_t IGN_Width = 20;
    const uint16_t IGN_Height = 35;
    const uint16_t IGN_PositionXY[2] = {216, 6};
    byte IGN_LastImage = 255;
    bool IGN_ImageProcess = false;
  public:
    byte IGN_CurrentImage = 2;
    

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
        for(int j = 0; j < sizeof(this->SEAT_CurrentImage); j++)
          this->SEAT_LastImage[j] = 0;
        for(int j = 0; j < sizeof(this->BELT_CurrentImage); j++)
          this->BELT_LastImage[j] = 0;
        this->REC_LastImage = 0;
        this->IGN_LastImage = 0;
      }
      else if(this->PAGE_CurrentImage == 2 && this->PAGE_CurrentImage != this->PAGE_LastImage)
      {
        for(int j = 0; j < sizeof(this->SEAT_CurrentImage); j++)
          this->SEAT_LastImage[j] = 255;
        for(int j = 0; j < sizeof(this->BELT_CurrentImage); j++)
          this->BELT_LastImage[j] = 255;
        this->REC_LastImage = 255;
        this->IGN_LastImage = 255;
      }
      
      this->PAGE_LastImage = this->PAGE_LastImage != 0 ? this->PAGE_CurrentImage : this->PAGE_LastImage;   
      
      for(int j = 0; j < sizeof(this->SEAT_CurrentImage); j++)
      {
        this->SEAT_ImageProcess[j] = this->SEAT_CurrentImage[j] != this->SEAT_LastImage[j] && this->SEAT_LastImage[j] != 0;  
        this->SEAT_LastImage[j] = this->SEAT_LastImage[j] != 0 ? this->SEAT_CurrentImage[j] : this->SEAT_LastImage[j];
      }
      
      for(int j = 0; j < sizeof(this->BELT_CurrentImage); j++)
      {
        this->BELT_ImageProcess[j] = this->BELT_CurrentImage[j] != this->BELT_LastImage[j] && this->BELT_LastImage[j] != 0;  
        this->BELT_LastImage[j] = this->BELT_LastImage[j] != 0 ? this->BELT_CurrentImage[j] : this->BELT_LastImage[j];
      }
      
      this->REC_ImageProcess = this->REC_CurrentImage != this->REC_LastImage && this->REC_LastImage != 0;
      this->REC_LastImage = this->REC_LastImage != 0 ? this->REC_CurrentImage : this->REC_LastImage;      
      
      this->IGN_ImageProcess = this->IGN_CurrentImage != this->IGN_LastImage && this->IGN_LastImage != 0;
      this->IGN_LastImage = this->IGN_LastImage != 0 ? this->IGN_CurrentImage : this->IGN_LastImage;
    }
};
