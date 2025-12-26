#include "makeJSON.h"


void updateValues( esp_model *esp, int luminosity, float temperature, int fanSpeed, bool coolerState, bool heaterState, bool fireDetected, float sb, float sh){
  esp->luminosity = luminosity;
  esp->temperature = temperature;
  esp->fanSpeed = fanSpeed;
  esp->coolerState = coolerState;
  esp->heaterState = heaterState;
  esp->fireDetected = fireDetected;
  esp->lowTempThreshold = sb;
  esp->highTempThreshold = sh;
}


StaticJsonDocument<1000> makeJSON_fromStatus(esp_model *em){
  StaticJsonDocument<1000> doc;

  // Status section
  JsonObject status = doc.createNestedObject("status");
  status["temperature"] = em->temperature;
  status["light"] = em->luminosity;

  if (em->coolerState|| em->fireDetected)
    status["regul"] = "COLD";
  else if (em->heaterState)
    status["regul"] =  "HEAT";
  else
    status["regul"] = "HALT";

  status["fire"] = em->fireDetected;
  status["heat"] = em->heaterState ? "ON" : "OFF";
  status["cold"] = em->coolerState ? "ON" : "OFF";
  status["fanspeed"] = em->fanSpeed;

  // Location section
  JsonObject location = doc.createNestedObject("location");
  location["room"] = "200";
  JsonObject gps = location.createNestedObject("gps");
  gps["lat"] = em->latitude;
  gps["lon"] = em->longitude;
  location["address"] = "Jean Médecin";

  // Regul section
  JsonObject regul = doc.createNestedObject("regul");
  regul["lt"] = em->lowTempThreshold; 
  regul["ht"] = em->highTempThreshold; 

  // Info section (hypothetical, as not in esp_model)
  JsonObject info = doc.createNestedObject("info");
  info["ident"] = em->ident; 
  info["user"] = "Mamadou et Ibrahima";         
  info["loc"] = "Nice";   

  // Net section
  JsonObject net = doc.createNestedObject("net");
  net["uptime"] = "0"; // Example: System uptime
  net["ssid"] = em->WiFiSSID.isEmpty() ? "NOP" : em->WiFiSSID;
  net["mac"] = em->MAC.isEmpty() ? "NOP" : em->MAC;
  net["ip"] = em->IP.isEmpty() ? "NOP" : em->IP;

  // Reporthost section
  JsonObject reporthost = doc.createNestedObject("reporthost");
  reporthost["target_ip"] = "127.0.0.1";
  reporthost["target_port"] = 1800;
  reporthost["sp"] = 2;

  // Piscine section (Added from mqtt_full)
  JsonObject piscine = doc.createNestedObject("piscine");
  piscine["occuped"] = (em->luminosity > LIGHTMAX) ? true :  false;
  piscine["hotspot"] = em->isHotspot;

  return doc;
}