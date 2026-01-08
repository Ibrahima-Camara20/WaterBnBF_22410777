from datetime import datetime
class TemperatureManager:
    def __init__(self, default_temp=25.0):
        self.default_temp = default_temp
        self.pool_temperatures = {}  # {pool_id: {"temp": float, "updated_at": datetime}}
    
    def update_temperature(self, pool_id, temperature):
        self.pool_temperatures[pool_id] = {
            "temp": float(temperature),
            "updated_at": datetime.now()
        }
            
    def get_temperature(self, pool_id):
        if pool_id in self.pool_temperatures:
            temp_data = self.pool_temperatures[pool_id]
            return temp_data["temp"]
        else:
            print(f"No temperature data for pool {pool_id}, using default: {self.default_temp}°C")
            return self.default_temp
    
    def process_mqtt_message(self, mqtt_data):
        try:
            ident = mqtt_data.get("info", {}).get("ident", "")
            if ident.startswith("P__"):
                pool_id = ident.split("_")[2]
            else:
                print(f"Unexpected ident format: {ident}")
                return None, None
            temp = mqtt_data.get("status", {}).get("temperature")
            if temp is not None:
                self.update_temperature(pool_id, temp)
                return pool_id, float(temp)
            else:
                print(f"No temperature in MQTT message for {pool_id}")
                return pool_id, None
        except Exception as e:
            print(f"Error processing MQTT message: {e}")
            return None, None

temp_manager = TemperatureManager()
