#ifndef NETWORKCONTROLLER_H
#define NETWORKCONTROLLER_H

#include "wifi_utils.h"
#include <Arduino.h>
#include <ArduinoJson.h>
#include <PubSubClient.h>
#include <WiFi.h>
#include <vector>

// MQTT Configuration
#define MQTT_MAX_PACKET_SIZE 1024
#define MQTT_SERVER "broker.hivemq.com"
#define MQTT_PORT 1883
#define MQTT_TOPIC "uca/iot/piscine"

class NetworkController {
public:
  NetworkController();
  void begin(const char *hostname);
  void loop();
  bool publish(const JsonDocument &doc);

  // Status helpers
  bool isConnected();
  String getMacAddress();
  String getIP();
  String getSSID();

  // Hotspot Logic
  bool checkHotspot(float myTemp, double myLat, double myLon, float radius);
  void handleMessage(char *topic, byte *payload, unsigned int length);
  void subscribeAccess();
  void handleAccessTopic(char *topic, byte *payload, unsigned int length);

private:
  WiFiClient espClient;
  PubSubClient mqttClient;
  String hostname;

  struct Neighbor {
    String id;
    double lat;
    double lon;
    float temp;
    unsigned long lastSeen;
  };

  std::vector<Neighbor> neighbors;

  void connectMQTT();
  double haversine(double lat1, double lon1, double lat2, double lon2);
};

#endif
