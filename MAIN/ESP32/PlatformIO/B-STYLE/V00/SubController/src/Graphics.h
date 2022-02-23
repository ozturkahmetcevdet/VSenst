#include "Importer.h"
#include <TFT_eSPI.h>  
#include <EEPROM.h>

#define SEAT_MAX_NUMBER 24
#define EEPROM_SIZE 24
#define EEPROM_CALB_ADDRESS 0x00

class Graphics
{ 
  private:    
    #if B_STYLE == (1)
    const short unsigned int* PAGE_NameList[3] = {P0, SUB, PBYE};
    const uint16_t PAGE_Size[3][2] = {{150, 232}, {240, 29}, {82, 27}};
    const uint16_t PAGE_PositionXY[3][2] = {{45, 44}, {0, 0}, {79, 146}};
    #else
    const short unsigned int* PAGE_NameList[3] = {VELDO_P0, SUB, PBYE};
    const uint16_t PAGE_Size[3][2] = {{172, 80}, {240, 29}, {82, 27}};
    const uint16_t PAGE_PositionXY[3][2] = {{34, 120}, {0, 0}, {79, 146}};
    #endif
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
    byte BATTERY_CurrentImage = 1;

  private:    
    const short unsigned int* WIFI_NameList[5] = {WIFI_OFF, WIFI_1, WIFI_2, WIFI_3, WIFI_4};
    const uint16_t WIFI_Size[2] = {19, 19};
    const uint16_t WIFI_PositionXY[2] = {4, 4};
    byte WIFI_LastImage = 255;
    bool WIFI_ImageProcess = false;
  public:
    byte WIFI_CurrentImage = 1;
    bool WIFI_TouchActivity = false;

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
    void Clear(const uint16_t* position, const uint16_t* size, uint16_t color);
    void Text(String txt, const uint16_t* position, uint16_t txtColor, uint16_t backColor);

  private:
    inline void SetBitmap(const short unsigned int* xy, const short unsigned int* wh, const short unsigned int* image, bool imageProcess)
    {
      if(!imageProcess)
        return;
        
      this->gfxLcd.pushImage(xy[0], xy[1], wh[0], wh[1], image);
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

    void TouchCalibrate()
    {
      uint16_t calData[5];

      this->ReadIntArrayFromEEPROM(EEPROM_CALB_ADDRESS, calData, 5);
      //Serial.println("EEPROM Calibration data:");
      //Serial.println(calData[4]);
      //Serial.println();
      if(calData[4] != 0xFFFF)
      {
        this->gfxLcd.setTouch(calData);
        //Serial.println("EEPROM Calibration complete!");
        return;
      }

      // Calibrate
      this->gfxLcd.fillScreen(TFT_BLACK);
      this->gfxLcd.setCursor(20, 0);
      this->gfxLcd.setTextFont(2);
      this->gfxLcd.setTextSize(1);
      this->gfxLcd.setTextColor(TFT_WHITE, TFT_BLACK);

      this->gfxLcd.println("Touch corners as indicated");

      this->gfxLcd.setTextFont(1);
      this->gfxLcd.println();

      this->gfxLcd.calibrateTouch(calData, TFT_MAGENTA, TFT_BLACK, 15);

      Serial.println(); Serial.println();
      Serial.println("// Use this calibration code in setup():");
      Serial.print("  uint16_t calData[5] = ");
      Serial.print("{ ");

      for (uint8_t i = 0; i < 5; i++)
      {
        Serial.print(calData[i]);
        if (i < 4) Serial.print(", ");
      }

      Serial.println(" };");
      Serial.print("  tft.setTouch(calData);");
      Serial.println(); Serial.println();

      this->gfxLcd.fillScreen(TFT_BLACK);
      
      this->gfxLcd.setTextColor(TFT_GREEN, TFT_BLACK);
      this->gfxLcd.println("Calibration complete!");
      this->gfxLcd.println("Calibration code sent to Serial port.");

      this->WriteIntArrayIntoEEPROM(EEPROM_CALB_ADDRESS, calData, 5);

      delay(4000);
    }

    void WriteIntArrayIntoEEPROM(uint16_t address, uint16_t* numbers, uint16_t arraySize)
    {
      int addressIndex = address;
      for (int i = 0; i < arraySize; i++) 
      {
        EEPROM.writeUShort(addressIndex, numbers[i]);
        addressIndex += sizeof(uint16_t);
      }
      EEPROM.commit();
    }
    void ReadIntArrayFromEEPROM(uint16_t address, uint16_t* numbers, uint16_t arraySize)
    {
      int addressIndex = address;
      for (int i = 0; i < arraySize; i++)
      {
        numbers[i] = EEPROM.readUShort(addressIndex);
        addressIndex += sizeof(uint16_t);
      }
    }
};
