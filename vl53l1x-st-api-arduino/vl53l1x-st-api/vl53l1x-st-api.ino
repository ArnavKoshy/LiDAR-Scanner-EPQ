/*******************************************************************************
This code is the code I wrote for the final program on the arduino.
It is written for a VL53L1X board using the ST api and a PCA9685 board using the Adafruit_PWMServoDriver library

*******************************************************************************/

#include <Wire.h>
#include "vl53l1_api.h"
#include <Adafruit_PWMServoDriver.h>



// Set up default servo class at address 0x40
Adafruit_PWMServoDriver pwm = Adafruit_PWMServoDriver();

//The maximum limits of the servo. These are WRONG for the moment. Calibration is needed
#define SERVO_MIN 100

#define SERVO_MAX 470

VL53L1_Dev_t                   dev;
VL53L1_DEV                     Dev = &dev;
int status;


void sendRanging(uint16_t i, uint16_t j){
  static VL53L1_RangingMeasurementData_t RangingData;

  status = VL53L1_WaitMeasurementDataReady(Dev);
  if(!status)
  {
    status = VL53L1_GetRangingMeasurementData(Dev, &RangingData);
    if(status==0)
    {
      Serial.print(map(i, SERVO_MIN, SERVO_MAX, -90, 90));
      Serial.print(F(","));
      Serial.print(map(j, SERVO_MIN, SERVO_MAX, -90, 90));
      Serial.print(F(","));
      Serial.print(RangingData.RangeMilliMeter);
      Serial.println();
      
    }
    status = VL53L1_ClearInterruptAndStartMeasurement(Dev);
  }
  else
  {
    Serial.print(F("error waiting for data ready: "));
    Serial.println(status);
    status = VL53L1_StartMeasurement(Dev);
    delay(0.01);
  }
}
  
void setup()
{
  uint8_t byteData;
  uint16_t wordData;
  pwm.begin();
  
  pwm.setPWMFreq(50);  // Analog servos run at ~50 Hz updates

  Wire.begin();
  Wire.setClock(400000);
  Serial.begin(115200);

  Dev->I2cDevAddr = 0x52;

  VL53L1_software_reset(Dev);

  VL53L1_RdByte(Dev, 0x010F, &byteData);
  Serial.print(F("VL53L1X Model_ID: "));
  Serial.println(byteData, HEX);
  VL53L1_RdByte(Dev, 0x0110, &byteData);
  Serial.print(F("VL53L1X Module_Type: "));
  Serial.println(byteData, HEX);
  VL53L1_RdWord(Dev, 0x010F, &wordData);
  Serial.print(F("VL53L1X: "));
  Serial.println(wordData, HEX);

  status = VL53L1_WaitDeviceBooted(Dev);
  status = VL53L1_DataInit(Dev);
  status = VL53L1_StaticInit(Dev);
  status = VL53L1_SetDistanceMode(Dev, VL53L1_DISTANCEMODE_SHORT);
  status = VL53L1_SetMeasurementTimingBudgetMicroSeconds(Dev, 30000);
  status = VL53L1_SetInterMeasurementPeriodMilliSeconds(Dev, 33);
  status = VL53L1_StartMeasurement(Dev);
  VL53L1_UserRoi_t roiConfig;
  roiConfig.TopLeftX = 6;
  roiConfig.TopLeftY = 9;
  roiConfig.BotRightX = 9;
  roiConfig.BotRightY = 6;
  status = VL53L1_SetUserROI(Dev, &roiConfig);
  if(status)
  {
    Serial.println(F("VL53L1_StartMeasurement failed"));
    while(1);
  }
}

void loop()
{
//  delay(50);
for(uint16_t j = (SERVO_MIN + SERVO_MAX)/2; j<SERVO_MAX; j=j+5){

for(uint16_t i = SERVO_MIN +50; i<SERVO_MAX - 50; i=i+2){
   pwm.setPWM(0,0, i);
   pwm.setPWM(1,0, j);

  sendRanging(i, j);
    
}
j = j+5;
for(uint16_t i = SERVO_MAX - 50; i>SERVO_MIN + 50; i=i-2){

  pwm.setPWM(0,0, i);
  pwm.setPWM(1,0, j);
  sendRanging(i, j);
}
}
}
