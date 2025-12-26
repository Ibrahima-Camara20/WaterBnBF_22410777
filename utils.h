#ifndef CLIMATECONTROL_H
#define CLIMATECONTROL_H

#include <Adafruit_NeoPixel.h>
#include <Arduino.h>
#include <DallasTemperature.h>
#include <OneWire.h>


// Used Pins
#define CLIMPIN 19
#define RADPIN 21
#define FANPIN 27
#define LEDSTRIPPIN 13
#define NUMLEDS 5

// Seuil
#define LIGHTMAX 3500

enum AccessState { STATE_GREEN, STATE_YELLOW, STATE_RED };

class ESPController {
public:
  ESPController();
  void begin();
  void update();
  void setHotspot(bool state);
  void setAccess(AccessState state);

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
  AccessState accessState;
  unsigned long accessTimer;

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
  void managePoolLEDs();
};

#endif