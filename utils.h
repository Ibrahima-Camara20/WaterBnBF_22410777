#ifndef CLIMATECONTROL_H
#define CLIMATECONTROL_H

#include <Arduino.h>
#include <OneWire.h>
#include <DallasTemperature.h>
#include <Adafruit_NeoPixel.h>

// Used Pins
#define CLIMPIN 19
#define RADPIN 21
#define FANPIN 27
#define LEDSTRIPPIN 13
#define NUMLEDS 5

// Seuil
#define LIGHTMAX 3500

class ESPController {
public:
    ESPController();
    void begin();
    void update();
    void setHotspot(bool state);
    
    // Getters for state   
    float getTemperature();
    int getLuminosity();
    bool getCoolerState();
    bool getHeaterState();
    bool getFireDetected();
    int getFanSpeed();
    float getSB();
    float getSH();

private:
    // State variables
    int luminosity;
    float temperature;
    bool coolerState;
    bool heaterState;
    bool fireDetected;
    int fanSpeed;
    bool isHotspot;

    // Thresholds
    float SB;
    float SH;

    // Hardware objects
    OneWire oneWire;
    DallasTemperature tempSensor;
    Adafruit_NeoPixel strip;

    // Internal methods
    void initLeds();
    void initFan();
    float readTemperature();
    void getThresholds();
    void setLEDS(uint32_t color);
    void progressiveFan();
    void checkStatus(float t, int light);
    void controlSensors();
};

#endif