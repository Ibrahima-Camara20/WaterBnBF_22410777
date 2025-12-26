#include "NetworkController.h"
#include "utils.h"

extern ESPController esp;

// Callback function wrapper to bridge C-style callback to C++ class
NetworkController *instance = nullptr;

void callback(char *topic, byte *payload, unsigned int length) {
  if (instance) {
    instance->handleMessage(topic, payload, length);
  }
}

NetworkController::NetworkController() : mqttClient(espClient) {
  instance = this;
}

void NetworkController::begin(const char *hostname) {
  this->hostname = hostname;

  // Connect to WiFi using the utility function
  wifi_connect_multi(hostname);
  wifi_printstatus(0);

  // Setup MQTT
  mqttClient.setServer(MQTT_SERVER, MQTT_PORT);
  mqttClient.setCallback(callback);
  mqttClient.setBufferSize(MQTT_MAX_PACKET_SIZE); // Increase buffer size
}

void NetworkController::loop() {
  if (!mqttClient.connected()) {
    connectMQTT();
  }
  mqttClient.loop();
}

void NetworkController::connectMQTT() {
  // Loop until we're reconnected
  while (!mqttClient.connected()) {
    Serial.print("Attempting MQTT connection... ");

    // Create a client ID from MAC address
    String clientId = "ESP32-";
    clientId += WiFi.macAddress();
    clientId.replace(":", "");

    if (mqttClient.connect(clientId.c_str())) {
      Serial.println("connected");
      mqttClient.subscribe(MQTT_TOPIC);
      mqttClient.subscribe("uca/iot/piscine"); // Subscribe to pool topic
      subscribeAccess();
    } else {
      Serial.print("failed, rc=");
      Serial.print(mqttClient.state());
      Serial.println(" try again in 5 seconds");
      delay(5000);
    }
  }
}

bool NetworkController::publish(const JsonDocument &doc) {
  if (!mqttClient.connected()) {
    return false;
  }

  String jsonString;
  serializeJson(doc, jsonString);

  unsigned int len = jsonString.length();

  // Begin publish
  if (!mqttClient.beginPublish(MQTT_TOPIC, len, false)) {
    Serial.print("publish start fail, state=");
    Serial.println(mqttClient.state());
    return false;
  }

  // Write payload
  mqttClient.write((const uint8_t *)jsonString.c_str(), len);

  // End publish
  if (!mqttClient.endPublish()) {
    Serial.print("publish end fail, state=");
    Serial.println(mqttClient.state());
    return false;
  }

  return true;
}

// Helpers
bool NetworkController::isConnected() { return mqttClient.connected(); }

String NetworkController::getMacAddress() { return WiFi.macAddress(); }

String NetworkController::getIP() { return WiFi.localIP().toString(); }

String NetworkController::getSSID() { return WiFi.SSID(); }

// Hotspot Logic

double NetworkController::haversine(double lat1, double lon1, double lat2,
                                    double lon2) {
  double R = 6371.0; // Earth radius in km
  double dLat = (lat2 - lat1) * M_PI / 180.0;
  double dLon = (lon2 - lon1) * M_PI / 180.0;
  lat1 = lat1 * M_PI / 180.0;
  lat2 = lat2 * M_PI / 180.0;

  double a = sin(dLat / 2) * sin(dLat / 2) +
             sin(dLon / 2) * sin(dLon / 2) * cos(lat1) * cos(lat2);
  double c = 2 * atan2(sqrt(a), sqrt(1 - a));
  return R * c;
}

void NetworkController::handleMessage(char *topic, byte *payload,
                                      unsigned int length) {
  handleAccessTopic(topic, payload, length);

  String message;
  for (int i = 0; i < length; i++) {
    message += (char)payload[i];
  }

  // Only process piscine topic
  if (String(topic) == MQTT_TOPIC) {
    StaticJsonDocument<1024> doc;
    DeserializationError error = deserializeJson(doc, message);

    if (error) {
      Serial.print(F("deserializeJson() failed: "));
      Serial.println(error.f_str());
      return;
    }

    // Extract data
    if (doc.containsKey("status") && doc.containsKey("location") &&
        doc.containsKey("info")) {
      // Check if it's me (ignore my own messages)
      String id = doc["info"]["ident"]; // or mac
      if (id == hostname)
        return;

      float temp = doc["status"]["temperature"];
      double lat = doc["location"]["gps"]["lat"];
      double lon = doc["location"]["gps"]["lon"];

      // Update or add neighbor
      bool found = false;
      for (auto &neighbor : neighbors) {
        if (neighbor.id == id) {
          neighbor.lat = lat;
          neighbor.lon = lon;
          neighbor.temp = temp;
          neighbor.lastSeen = millis();
          found = true;
          break;
        }
      }

      if (!found) {
        neighbors.push_back({id, lat, lon, temp, millis()});
      }
    }
  }
}

bool NetworkController::checkHotspot(float myTemp, double myLat, double myLon,
                                     float radius) {
  // Clean up old neighbors (e.g., > 1 hour old) - Optional, but good practice
  // For now, just check all known neighbors

  for (const auto &neighbor : neighbors) {
    double dist = haversine(myLat, myLon, neighbor.lat, neighbor.lon);
    if (dist <= radius) {
      if (neighbor.temp >= myTemp) {
        // Found a neighbor in radius with higher or equal temp
        return false;
      }
    }
  }
  return true; // No neighbor in radius has higher temp
}

void NetworkController::subscribeAccess() {
  String topic = "uca/iot/piscine/";
  topic += hostname;
  topic += "/access";
  mqttClient.subscribe(topic.c_str());
}

void NetworkController::handleAccessTopic(char *topic, byte *payload,
                                          unsigned int length) {
  String expectedTopic = "uca/iot/piscine/";
  expectedTopic += hostname;
  expectedTopic += "/access";

  if (String(topic) == expectedTopic) {
    String message;
    for (int i = 0; i < length; i++) {
      message += (char)payload[i];
    }
    StaticJsonDocument<256> doc;
    DeserializationError error = deserializeJson(doc, message);

    if (error) {
      Serial.print(F("deserializeJson() for access failed: "));
      Serial.println(error.f_str());
      return;
    }

    const char *command = doc["command"];
    if (command) {
      if (strcmp(command, "GRANTED") == 0) {
        esp.setAccess(STATE_YELLOW);
      } else if (strcmp(command, "DENIED") == 0) {
        esp.setAccess(STATE_RED);
      }
    }
  }
}
