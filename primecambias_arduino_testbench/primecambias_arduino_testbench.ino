/**
 * @file arduino_based_testcode
 * @author carobers@asu.edu
 * @brief primecam Bias Board Control and Test Code
 * @date 2025-05-02
 *
 * @copyright Copyright (c) 2025 Arizona State University. All Rights Reserved.
 *
 */

#include <Arduino.h>

#include <Adafruit_INA219.h>
#include <Wire.h>
#define SW_VERSION_NUMBER "0.6"

// *********** I2C DEVICE ADDRESSES *****************
const uint8_t ADDR_AD5144  = 0x2F;
const uint8_t ADDR_LTC4302 = 0x60;
const uint8_t ADDR_INA219  = 0x40;


// *********** I2C DEVICE COMMANDS *****************
const uint8_t CMD_SETRDAC1 = 0b00010000;
const uint8_t CMD_SETRDAC2 = 0b00010001;
const uint8_t CMD_SETRDAC3 = 0b00010010;
const uint8_t CMD_SETRDAC4 = 0b00010011;
const uint8_t CMD_CONNECT_LTC = 0b10100000;
const uint8_t CMD_GPIO1_HIGH = 0b10100000;
const uint8_t CMD_GPIO1_LOW = 0b10000000;

Adafruit_INA219 ina219;


const char MENU[] = ""
    "1. Init I2C devices\n"
    "2. gpio1 from LTC4302-19 HIGH\n"
    "3. gpio1 form LTC4302-19 LOW\n"
    "4. Set Pot\n"
    "5. Read INA219\n";

int setWiper(uint8_t dpot_i2c_addr, uint8_t wiper, uint8_t val);

void clear(){
    while(Serial.available() > 0){
        Serial.read();
    }
}

void wait(){
    while(Serial.available() == 0);
}

int writeLTC(uint8_t address, uint8_t cmd)
{
    Wire.beginTransmission( ADDR_LTC4302 + address);
    Wire.write(cmd); // Connect IIC Bus
    return Wire.endTransmission();
}

void setup()
{
  Serial.begin(115200);
  Wire.begin();                         // start/setup i2c arduino interface
  
}

void loop()
{

    wait();
    String s = Serial.readStringUntil('\n');
    String s2;
    String s3;
    int cmd = s.toInt();
    clear();


    Serial.println("\r\nPRIMECAM  BIAS BOARD TEST CODE (built: " + String(__DATE__) + "_" + String(__TIME__) + "_v" + SW_VERSION_NUMBER +"\r\n");
    Serial.println(MENU);

    int wiper = 0, wiperval = 0, status = -1, pot = 0, pin = 0, state = 0, ina = 0;
    float cur = 0, vol = 0;
    int addr = 0;
    double shuntvoltage = 0;
    double busvoltage = 0;
    double current_mA = 0; // current in miliamps from INA219-1
    switch (cmd)
    {
        case 1: // INIT IIC DEVICES
            Serial.print("Connect LTC4302-1 --> ");
            status = writeLTC(1, CMD_CONNECT_LTC);
            Serial.println(status);
            Serial.print("Connect LTC4302-19 --> ");
            status = writeLTC(19, CMD_CONNECT_LTC);
            Serial.println(status);
            Serial.println("Init INA219");
            ina219.begin();
        
        break;

        case 2: // Enable GPIO1
            Serial.print("GPIO1  HIGH-->");
            status = writeLTC(19, CMD_GPIO1_HIGH);
            Serial.println(status);
            break;

        case 3: // Disable GPIO1
            Serial.print("GPIO1 LOW -->");
            status = writeLTC(19, CMD_GPIO1_LOW);
            Serial.println(status);
            break;

        case 4: // Set PotString(current_mA)
            Serial.println("Wiper (1-4)?");
            wait();
            s2 = Serial.readStringUntil('\n');
            wiper = s2.toInt();
            if (wiper < 1) wiper = 1;
            if (wiper > 4) wiper = 4;
            Serial.println("Wiper "+String(wiper));
            wiper = wiper-1;
            clear();

            Serial.println("Value?");
            wait();
            s3 = Serial.readStringUntil('\n');
            pot = s3.toInt();
            if (pot > 255) pot = 255;
            if (pot < 0) pot = 0;
            clear();
            Serial.println("value of " + String(pot));
            Serial.print("Set pot --> ");
            status = setWiper(ADDR_AD5144, wiper, pot);
            Serial.println(status);
            break;


        case 5:
            Serial.println("Read INA219");
            shuntvoltage = ina219.getShuntVoltage_mV();
            busvoltage = ina219.getBusVoltage_V();
            current_mA = ina219.getCurrent_mA();
            Serial.print("current (mA): ");
            Serial.println(current_mA);
            Serial.print("Bus Voltage (V):   ");
            Serial.println(busvoltage);
            Serial.print("Shunt Voltage (mV): ");
            Serial.println(shuntvoltage);
    }
}

int setWiper(uint8_t dpot_i2c_addr, uint8_t wiper, uint8_t val)
{
    int status = 0;
    Wire.beginTransmission(dpot_i2c_addr);
    Wire.write(CMD_SETRDAC1 + wiper);
    Wire.write(val);                             

    status = Wire.endTransmission();
    if (status != 0)
    Serial.println("\r\nError, couldn't communicate with AD5144 chip over i2c status=" + String(status) + "\r\n");

    return status;
}
