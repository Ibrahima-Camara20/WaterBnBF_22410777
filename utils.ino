#include "utils.h"

ESPController::ESPController() 
    : luminosity(0), temperature(0.0), coolerState(false), heaterState(false), 
      fireDetected(false), isHotspot(false), fanSpeed(0), SB(25.8), SH(26.0),
      oneWire(23), tempSensor(&oneWire), 
      strip(NUMLEDS, LEDSTRIPPIN, NEO_GRB + NEO_KHZ800) {
}

void ESPController::begin() {
    initLeds();
    initFan();
    tempSensor.begin();
}

void ESPController::update() {
    temperature = readTemperature();
    luminosity = 4095 - analogRead(A5);

    getThresholds();
    
    checkStatus(temperature, luminosity);
    controlSensors();
}

void ESPController::setHotspot(bool state) {
    isHotspot = state;
}

void ESPController::initLeds() {
    // init ledPins as an OUTPUT
    pinMode(CLIMPIN, OUTPUT);
    pinMode(RADPIN, OUTPUT);
    pinMode(2, OUTPUT); // led d'incendie / hotspot
    digitalWrite(CLIMPIN, LOW);
    digitalWrite(RADPIN, LOW);
    digitalWrite(2, LOW);

    // init LedStrips 
    strip.begin();
    strip.clear();
    strip.show();
}

void ESPController::initFan() {
    // init fan
    ledcAttach(FANPIN, 25000, 8);
    ledcWrite(FANPIN, 0);
}

void ESPController::getThresholds() {
    if (Serial.available() > 0) {
        String data = Serial.readStringUntil('\n');
        if (data.startsWith("LT:")) {
            int ltIndex = data.indexOf("LT:") + 3;
            int commaIndex = data.indexOf(",");
            int htIndex = data.indexOf("HT:") + 3;
            if (commaIndex > ltIndex && htIndex > commaIndex) {
                String ltStr = data.substring(ltIndex, commaIndex);
                String htStr = data.substring(htIndex);
                SB = ltStr.toFloat();
                SH = htStr.toFloat();
            }
        }
    }
}

float ESPController::readTemperature() {
    tempSensor.requestTemperatures();
    return tempSensor.getTempCByIndex(0);
}

void ESPController::setLEDS(uint32_t color) {
    for (int i = 0; i < NUMLEDS; i++) {
        strip.setPixelColor(i, color);
    }
    strip.show();
}

void ESPController::progressiveFan() {
    static unsigned long previousMillisFan = 0;
    unsigned long currentMillis = millis();

    if (fanSpeed == 0) {
        fanSpeed = 64; // Démarrer la progression
        ledcWrite(FANPIN, fanSpeed);
        previousMillisFan = currentMillis;
    } else if (fanSpeed < 255 && currentMillis - previousMillisFan >= 1000) {
        fanSpeed += 64; // Passer à l'étape suivante
        if (fanSpeed > 255) fanSpeed = 255; // Limiter à 255
        ledcWrite(FANPIN, fanSpeed);
        previousMillisFan = currentMillis;
    } else if (fanSpeed != 0 && fanSpeed != 64 && fanSpeed != 128 && fanSpeed != 192 && fanSpeed != 255) {
        ledcWrite(FANPIN, fanSpeed); // Appliquer fanSpeed dynamique si hors progression
    }
}

void ESPController::checkStatus(float t, int light) {
    if (light > LIGHTMAX && t > SH) {
        fireDetected = true;
        coolerState = false;
        heaterState = false;
    } else {
        fireDetected = false;
        if (t > SH) {
            coolerState = true;
            heaterState = false;
        } else if (t < SH) {
            coolerState = false;
        }

        if (t < SB) {
            heaterState = true;
            coolerState = false;
        } else if (t > SB) {
            heaterState = false;
        }
    }
}

void ESPController::controlSensors() {
    if (coolerState) {
        digitalWrite(2, LOW);
        setLEDS(strip.Color(255, 0, 0));
        digitalWrite(CLIMPIN, HIGH);
        digitalWrite(RADPIN, LOW);
        progressiveFan();
    } else {
        ledcWrite(FANPIN, 0);
        fanSpeed = 0;
        
        // Pin 2 Logic: Fire > Hotspot
        if (fireDetected) {
             digitalWrite(2, HIGH);
        } else if (isHotspot) {
             digitalWrite(2, HIGH);
        } else {
             digitalWrite(2, LOW);
        }

        if (heaterState) {
            setLEDS(strip.Color(0, 0, 255));
            digitalWrite(RADPIN, HIGH);
            digitalWrite(CLIMPIN, LOW);
        } else if (fireDetected) {
            setLEDS(strip.Color(255, 0, 0));
            // Pin 2 handled above
            digitalWrite(RADPIN, LOW);
            digitalWrite(CLIMPIN, LOW);
        } else {
            setLEDS(strip.Color(0, 255, 0));
            digitalWrite(RADPIN, LOW);
            digitalWrite(CLIMPIN, LOW);
        }
    }
}

// Getters
float ESPController::getTemperature() { return temperature; }
int ESPController::getLuminosity() { return luminosity; }
bool ESPController::getCoolerState(){ return coolerState; }
bool ESPController::getHeaterState() { return heaterState; }
bool ESPController::getFireDetected() { return fireDetected; }
int ESPController::getFanSpeed() { return fanSpeed; }
float ESPController::getSB() { return SB; }
float ESPController::getSH() { return SH; }