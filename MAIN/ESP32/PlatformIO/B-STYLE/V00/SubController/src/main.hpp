#include <Arduino.h>

void TimerLoop(void);
void SetDeviceUniqId(void);
void StartWifiManager(void);
void ResetWifiManager(void);
void ReadAndShowRssiStrength(void);
void FirmwareUpdate(bool activity);
int  FirmwareVersionCheck(void);

String FirmwareVersion = {
  "0.0.0"
};

#define URL_Fw_Version "https://raw.githubusercontent.com/ozturkahmetcevdet/VSenst/main/MAIN/ESP32/PlatformIO/B-STYLE/V00/Firmware/version.txt"
#define URL_Fw_Bin "https://raw.githubusercontent.com/ozturkahmetcevdet/VSenst/main/MAIN/ESP32/PlatformIO/B-STYLE/V00/Firmware/firmware.bin"