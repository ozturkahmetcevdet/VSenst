#include "Adafruit_GFX.h"     
#include "Adafruit_ILI9341.h" 
#include "URTouch.h"          

#define TFT_DC 2              
#define TFT_CS 15            
#define TFT_RST 4
#define TFT_MISO 12         
#define TFT_MOSI 13           
#define TFT_CLK 0            

Adafruit_ILI9341 tft = Adafruit_ILI9341(TFT_CS, TFT_DC, TFT_MOSI, TFT_CLK, TFT_RST, TFT_MISO);

#define t_SCK 18              
#define t_CS 16                
#define t_MOSI 23              
#define t_MISO 19             
#define t_IRQ 22              

URTouch ts(t_SCK, t_CS, t_MOSI, t_MISO, t_IRQ);

#define TFT_BK 32

void setup(){
  pinMode(TFT_BK, OUTPUT);
  digitalWrite(TFT_BK, HIGH);
  
  tft.begin();                     
  tft.setRotation(3);           
 
  ts.InitTouch();                   
  ts.setPrecision(PREC_EXTREME);
  tft.fillScreen(ILI9341_BLACK);

  tft.setTextColor(ILI9341_RED);  
  tft.setTextSize(2);               
  tft.setCursor(85,5);              
  tft.print("Touch Demo"); 

  
  tft.setTextColor(ILI9341_GREEN);  
  tft.setCursor(20,220);           
  tft.print("http://www.educ8s.tv");
}
 
void loop()
{
  int x, y;                        
 
  while(ts.dataAvailable())        
  {
    ts.read();                      
    x = ts.getX();                 
    y = ts.getY();                  
    if((x!=-1) && (y!=-1))          
    {
      x += 13;                      
      y += 4;                       
      int radius = 4;               
      tft.fillCircle(x, y, radius, ILI9341_YELLOW);
    }
  }
}
