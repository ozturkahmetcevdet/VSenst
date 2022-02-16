#include "Importer.h"
#include <TFT_eSPI.h>  
#include <XPT2046_Touchscreen.h> /* https://github.com/PaulStoffregen/XPT2046_Touchscreen */

#define TOUCH_CS_PIN  14
#define TOUCH_IRQ_PIN 27  

#define SEAT_SIZE 12

class Graphics
{ 
  private:    
    const short unsigned int* PAGE_NameList[4] = {P0, MAIN, PBYE};
    const uint16_t PAGE_Width = 172;
    const uint16_t PAGE_Height = 80;
    const uint16_t PAGE_MainWidth = 240;
    const uint16_t PAGE_MainHeight = 320;
    const uint16_t PAGE_PositionXY[2] = {34, 120};
    const uint16_t PAGE_MainPositionXY[2] = {0, 0};
    byte PAGE_LastImage = 255;
    bool PAGE_ImageProcess = false;
  public:
    byte PAGE_CurrentImage = 1;


  private:    
    const short unsigned int* SEAT_WheelChairList[4] = {  W_B,    W_F,    W_N,    W_P};
    const short unsigned int* SEAT_NameList[9][7] = { {S_B_B5, S_F_B5, S_N_B5, S_P_B5, S_U   , S_R   , S_NULL},
                                                      {S_B_B4, S_F_B4, S_N_B4, S_P_B4, S_U   , S_R   , S_NULL},
                                                      {S_B_B3, S_F_B3, S_N_B3, S_P_B3, S_U   , S_R   , S_NULL},
                                                      {S_B_B2, S_F_B2, S_N_B2, S_P_B2, S_U   , S_R   , S_NULL},
                                                      {S_B_B1, S_F_B1, S_N_B1, S_P_B1, S_U   , S_R   , S_NULL},
                                                      {B_1   , B_2   , B_3   , B_2   , B_1   , B_2   , B_3   },
                                                      {S_C_1 , S_C_2 , S_C_3 , S_C_2 , S_C_1 , S_C_2 , S_C_3 },
                                                      {SPAD  , SPAD  , SPAD  , SPAD  , SPAD  , SPAD  , SPAD  },
                                                      {RF    , RF    , RF    , RF    , RF    , RF    , RF    }};

    uint16_t SEAT_Width = 40;
    uint16_t SEAT_Height = 40;
    uint16_t SEAT_PositionXY[SEAT_SIZE][2]       = {
      {6  ,  52}, {70 ,  85},
      {6  , 117}, {6  , 182},
      {70 , 215}, {6  , 247},
      {192, 247}, {132, 215},
      {192, 182}, {192, 117},
      {132,  85}, {192,  52}
    };
    byte     SEAT_LastImage[SEAT_SIZE]           = {255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255};
    byte     SEAT_LastProcessImage[SEAT_SIZE]    = {255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255};
    bool     SEAT_ImageProcess[SEAT_SIZE]        = {false, false, false, false, false, false, false, false, false, false, false, false};
    byte     SEAT_AnimationCounter[SEAT_SIZE]    = {1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1};
    const byte SEAT_ANIMATION_CYCLE       = 6;
    uint32_t SEAT_AnimationCycleTime[SEAT_SIZE]  = {0}; 
  public:
    byte     SEAT_CurrentImage[SEAT_SIZE]        = {5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5};
    byte     SEAT_CurrentProcessImage[SEAT_SIZE] = {1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1};
    bool     SEAT_Animation[SEAT_SIZE]           = {false, false, false, false, false, false, false, false, false, false, false, false};
    bool     SEAT_WheelChairActive[SEAT_SIZE]    = {false, true, false, false, true, false, false, true, false, false, true, false};
    

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
        {
          this->SEAT_LastImage[j] = 0;
          this->SEAT_LastProcessImage[j] = 0;
        }
      }
      else if(this->PAGE_CurrentImage == 2 && this->PAGE_CurrentImage != this->PAGE_LastImage)
      {
        for(int j = 0; j < sizeof(this->SEAT_CurrentImage); j++)
        {
          this->SEAT_LastImage[j] = 255;
          this->SEAT_LastProcessImage[j] = 255;
        }
      }
      
      this->PAGE_LastImage = this->PAGE_LastImage != 0 ? this->PAGE_CurrentImage : this->PAGE_LastImage;   

      uint64_t timeStamp = millis(); 
      
      for(int j = 0; j < sizeof(this->SEAT_CurrentImage); j++)
      {
        if(((timeStamp - this->SEAT_AnimationCycleTime[j]) > 150) && this->SEAT_Animation[j])
        {
          this->SEAT_AnimationCycleTime[j] = timeStamp;
          this->SEAT_AnimationCounter[j] += this->SEAT_AnimationCounter[j] < this->SEAT_ANIMATION_CYCLE && this->SEAT_Animation[j] ? 1 : -this->SEAT_AnimationCounter[j];
          this->SEAT_CurrentImage[j] = this->SEAT_Animation[j] ? this->SEAT_AnimationCounter[j] + 1 : this->SEAT_CurrentImage[j];
          /*Serial.println();
          Serial.print("Time: ");
          Serial.print(timeStamp);
          Serial.println();
          Serial.print("Var: ");
          Serial.print(this->SEAT_AnimationCycleTime);
          Serial.println();
          Serial.print("Bool: ");
          Serial.print(this->SEAT_Animation[j]);
          Serial.println();
          Serial.print("Counter: ");
          Serial.print(this->SEAT_AnimationCounter[j]);
          Serial.println();
          Serial.print("Image: ");
          Serial.print(this->SEAT_CurrentImage[j]);*/
        }
        
        this->SEAT_ImageProcess[j] = (this->SEAT_CurrentImage[j] != this->SEAT_LastImage[j] && this->SEAT_LastImage[j] != 0) | (this->SEAT_CurrentProcessImage[j] != this->SEAT_LastProcessImage[j] && this->SEAT_LastProcessImage[j] != 0);  
        this->SEAT_LastImage[j] = this->SEAT_LastImage[j] != 0 ? this->SEAT_CurrentImage[j] : this->SEAT_LastImage[j];
        this->SEAT_LastProcessImage[j] = this->SEAT_LastProcessImage[j] != 0 ? this->SEAT_CurrentProcessImage[j] : this->SEAT_LastProcessImage[j];        
      }
    }
};
