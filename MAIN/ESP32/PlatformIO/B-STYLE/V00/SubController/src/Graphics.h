#include "Importer.h"
#include <TFT_eSPI.h>  

#define TOUCH_CS_PIN  14
#define TOUCH_IRQ_PIN 27  

#define SEAT_MAX_NUMBER 24

class Graphics
{ 
  private:    
    const short unsigned int* PAGE_NameList[3] = {P0, SUB, PBYE};
    const uint16_t PAGE_Size[3][2] = {{150, 232}, {240, 29}, {82, 27}};
    const uint16_t PAGE_PositionXY[3][2] = {{45, 44}, {0, 0}, {79, 146}};
    byte PAGE_LastImage = 255;
    bool PAGE_ImageProcess = false;
  public:
    byte PAGE_CurrentImage = 1;


  private:    
    const short unsigned int* SEAT_NameList[2][5] = {{S_F, S_N, S_P, S_U, S_R}, {W_F, W_N, W_P, W_U, W_R}};

    const uint16_t SEAT_Size[2][2] = {{40, 40}, {35, 55}};
    byte     SEAT_LastImage[SEAT_MAX_NUMBER]           = {255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255};
    bool     SEAT_ImageProcess[SEAT_MAX_NUMBER]        = {false, false, false, false, false, false, false, false, false, false, false, false, false, false, false, false, false, false, false, false, false, false, false, false};
  public:
    enum SEAT_TYPE
    {
      FULL_ = 1,
      NULL_,
      PASS_,
      UNRE_,
      REGS_
    };
    uint16_t SEAT_PositionXY[SEAT_MAX_NUMBER][2]       = {{0}};
    byte     SEAT_CurrentImage[SEAT_MAX_NUMBER]        = {5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5};
    byte     SEAT_Selector[SEAT_MAX_NUMBER]            = {0};
    
  private:    
    const short unsigned int* BATTERY_NameList[3] = {B_HIGH, B_LOW};
    const uint16_t BATTERY_Size[2] = {51, 19};
    const uint16_t BATTERY_PositionXY[2] = {94, 4};
    byte BATTERY_LastImage = 255;
    bool BATTERY_ImageProcess = false;
  public:
    byte BATTERY_CurrentImage = 2;

  private:    
    const short unsigned int* WIFI_NameList[3] = {WIFI_OFF};
    const uint16_t WIFI_Size[2] = {19, 19};
    const uint16_t WIFI_PositionXY[2] = {4, 4};
    byte WIFI_LastImage = 255;
    bool WIFI_ImageProcess = false;
  public:
    byte WIFI_CurrentImage = 1;

  private:    
    const short unsigned int* GPS_NameList[3] = {GPS_OFF};
    const uint16_t GPS_Size[2] = {19, 19};
    const uint16_t GPS_PositionXY[2] = {30, 4};
    byte GPS_LastImage = 255;
    bool GPS_ImageProcess = false;
  public:
    byte GPS_CurrentImage = 1;
    

  private:
    TFT_eSPI gfxLcd = TFT_eSPI();
    
  public:
    //TS_Point rawLocation;

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
        }
        this->BATTERY_LastImage = 0;
        this->WIFI_LastImage = 0;
        this->GPS_LastImage = 0;
      }
      else if(this->PAGE_CurrentImage == 2 && this->PAGE_CurrentImage != this->PAGE_LastImage)
      {
        for(int j = 0; j < sizeof(this->SEAT_CurrentImage); j++)
        {
          this->SEAT_LastImage[j] = 255;
        }
        this->BATTERY_LastImage = 255;
        this->WIFI_LastImage = 255;
        this->GPS_LastImage = 255;
      }
      
      this->PAGE_LastImage = this->PAGE_LastImage != 0 ? this->PAGE_CurrentImage : this->PAGE_LastImage;   
      
      for(int j = 0; j < sizeof(this->SEAT_CurrentImage); j++)
      {        
        this->SEAT_ImageProcess[j] = this->SEAT_CurrentImage[j] != this->SEAT_LastImage[j] && this->SEAT_LastImage[j] != 0 && this->SEAT_Selector[j] != 0;  
        this->SEAT_LastImage[j] = this->SEAT_LastImage[j] != 0 && this->SEAT_Selector[j] != 0 ? this->SEAT_CurrentImage[j] : this->SEAT_LastImage[j];   
      }

      this->BATTERY_ImageProcess = this->BATTERY_CurrentImage != this->BATTERY_LastImage && this-BATTERY_LastImage != 0;
      this->BATTERY_LastImage = this->BATTERY_LastImage != 0 ? this->BATTERY_CurrentImage : this->BATTERY_LastImage;

      this->WIFI_ImageProcess = this->WIFI_CurrentImage != this->WIFI_LastImage && this-WIFI_LastImage != 0;
      this->WIFI_LastImage = this->WIFI_LastImage != 0 ? this->WIFI_CurrentImage : this->WIFI_LastImage;

      this->GPS_ImageProcess = this->GPS_CurrentImage != this->GPS_LastImage && this-GPS_LastImage != 0;
      this->GPS_LastImage = this->GPS_LastImage != 0 ? this->GPS_CurrentImage : this->GPS_LastImage;
    }
};
