#include "Importer.h"
#include <TFT_eSPI.h>  

#define SEAT_CONFIG (16+1)

class Graphics
{ 
  private:    
    const short unsigned int* PAGE_NameList[5] = {Page_0, Page_0_1, Page_1, Page_Alarm, Page_Bye};
    const uint16_t PAGE_Width = 240;
    const uint16_t PAGE_Height = 320;
    const uint16_t PAGE_PositionXY[2] = {0, 0};
    byte PAGE_LastImage = 255;
    bool PAGE_ImageProcess = false;
  public:
    byte PAGE_CurrentImage = 2;


  private:    
    const short unsigned int* COUNTER_NameList[26] = {C0, C1, C2, C3, C4, C5, C6, C7, C8, C9, C10, C11, C12, C13, C14, C15, C16, C17, C18, C19, C20, C21, C22, C23, C24, C25};
    const uint16_t COUNTER_Width = 24;
    const uint16_t COUNTER_Height = 24;
    const uint16_t COUNTER_PositionXY[2] = {213, 8};
    byte COUNTER_LastImage = 1;
    bool COUNTER_ImageProcess = false;
  public:
    byte COUNTER_CurrentImage = 1;


#if SEAT_CONFIG == (19+1)/************************************************************************************************************************************************************/
  private:    
    const short unsigned int* SEAT_NameList[5] = {Seat_Unregistered, Seat_Registered, Seat_Red, Seat_Ok, Seat_Fault};
    const uint16_t SEAT_Width = 40;
    const uint16_t SEAT_Height = 40;
    const uint16_t SEAT_PositionXY[18][2] = {
      {21 ,  58}, {74 ,  58},
      {21 , 100}, {74 , 100},
      {21 , 142}, {74 , 142},
      {21 , 184}, {74 , 184},
      {21 , 226}, {74 , 226},
      {21 , 268}, {74 , 268},
      
      {127, 268}, {180, 268},
                  {180, 226}, 
                  {180, 184},
                  {180, 142},
                  {180, 100},
    };
    byte SEAT_LastImage[18] = {1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1};
    bool SEAT_ImageProcess[18] = {false, false, false, false, false, false, false, false, false, false, false, false, false, false, false, false, false, false};
  public:
    byte SEAT_CurrentImage[18] = {1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1};
#elif SEAT_CONFIG == (16+1)/************************************************************************************************************************************************************/
  private:    
    const short unsigned int* SEAT_NameList[5] = {Seat_Unregistered, Seat_Registered, Seat_Red, Seat_Ok, Seat_Fault};
    const uint16_t SEAT_Width = 40;
    const uint16_t SEAT_Height = 40;
    const uint16_t SEAT_PositionXY[15][2] = {
      {21 , 100}, {74 , 100},
      {21 , 142}, {74 , 142},
      {21 , 184}, {74 , 184},
      {21 , 226}, {74 , 226},
      {21 , 268}, {74 , 268},
      
      {127, 268}, {180, 268},
                  {180, 226}, 
                  {180, 184},
                  {180, 142},
    };
    byte SEAT_LastImage[15] = {1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1};
    bool SEAT_ImageProcess[15] = {false, false, false, false, false, false, false, false, false, false, false, false, false, false, false};
  public:
    byte SEAT_CurrentImage[15] = {1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1};
#endif


  private:    
    const short unsigned int* REC_NameList[3] = {Mode_Null, Mode_Record, Mode_Service};
    const uint16_t REC_Width = 115;
    const uint16_t REC_Height = 30;
    const uint16_t REC_PositionXY[2] = {96, 6};
    byte REC_LastImage = 1;
    bool REC_ImageProcess = false;
  public:
    byte REC_CurrentImage = 1;
    
    
  private:    
    const short unsigned int* IGN_NameList[2] = {Ignition_Off, Ignition_On};
    const uint16_t IGN_Width = 20;
    const uint16_t IGN_Height = 35;
    const uint16_t IGN_PositionXY[2] = {11, 5};
    byte IGN_LastImage = 1;
    bool IGN_ImageProcess = false;
  public:
    byte IGN_CurrentImage = 1;
    
    
  private:    
    const short unsigned int* DOOR_NameList[];
    const uint16_t DOOR_Width = 16;
    const uint16_t DOOR_Height = 68;
    const uint16_t DOOR_PositionXY[2] = {212, 65};
    byte DOOR_LastImage = 1;
    bool DOOR_ImageProcess = false;
  public:
    byte DOOR_CurrentImage = 1;

  private:
    TFT_eSPI gfxLcd = TFT_eSPI();

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
      
      if(this->PAGE_CurrentImage != 3)
      {
        this->COUNTER_LastImage = 0;
        for(int j = 0; j < sizeof(this->SEAT_CurrentImage); j++)
          this->SEAT_LastImage[j] = 0;
        this->REC_LastImage = 0;
        this->IGN_LastImage = 0;
        this->DOOR_LastImage = 0;
      }
      else if(this->PAGE_CurrentImage == 3 && this->PAGE_CurrentImage != this->PAGE_LastImage)
      {
        this->COUNTER_LastImage = 255;
        for(int j = 0; j < sizeof(this->SEAT_CurrentImage); j++){
          this->SEAT_LastImage[j] = 255;
        }
        this->REC_LastImage = 255;
        this->IGN_LastImage = 255;
        this->DOOR_LastImage = 255;
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
      
      this->DOOR_ImageProcess = this->DOOR_CurrentImage != this->DOOR_LastImage && this->DOOR_LastImage != 0;
      this->DOOR_LastImage = this->DOOR_LastImage != 0 ? this->DOOR_CurrentImage : this->DOOR_LastImage;
    }
};
