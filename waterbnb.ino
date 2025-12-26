#include "NetworkController.h"
#include "makeJSON.h"
#include "utils.h"


#define HOTSPOT_RADIUS 10.0
#define IDENT "22410771"
ESPController esp;
NetworkController network;
esp_model model; // Allocated on stack/global

void setup() {
  Serial.begin(9600);

  while (!Serial) {
    ; // Wait
  }

  esp.begin();

  // Initialize Network (WiFi + MQTT)
  network.begin(IDENT); // Hostname from mqtt_full

  // Update model with network info
  model.WiFiSSID = network.getSSID();
  model.IP = network.getIP();
  model.MAC = network.getMacAddress();
  model.ident = IDENT;
}

void loop() {
  static unsigned long lastPublishTime = 0;
  const unsigned long publishInterval = 5000;

  // Maintain network connection (handle incoming MQTT messages immediately)
  network.loop();

  // Update sensors (Note: readTemperature might still block for ~750ms)
  esp.update();

  // Calculate Hotspot Status immediately
  bool isHotspot = network.checkHotspot(esp.getTemperature(), model.latitude,
                                        model.longitude, HOTSPOT_RADIUS);

  esp.setHotspot(isHotspot);
  model.isHotspot = isHotspot;
  // Update model
  updateValues(&model, esp.getLuminosity(), esp.getTemperature(),
               esp.getFanSpeed(), esp.getCoolerState(), esp.getHeaterState(),
               esp.getFireDetected(), esp.getSB(), esp.getSH());

  // Publish JSON periodically
  if (millis() - lastPublishTime >= publishInterval) {
    lastPublishTime = millis();

    // Create JSO
    StaticJsonDocument<1000> statusJSON = makeJSON_fromStatus(&model);
    // Print to Serial (for debug)
    // serializeJson(statusJSON,);

    // Publish to MQTT
    network.publish(statusJSON);
  }
}
