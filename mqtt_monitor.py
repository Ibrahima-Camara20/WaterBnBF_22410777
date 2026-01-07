"""
Moniteur MQTT pour déboguer les messages du broker
Affiche en temps réel tous les messages reçus sur le topic uca/iot/piscine
"""

import paho.mqtt.client as mqtt
import json
import sys
from datetime import datetime

# Configuration
BROKER = "test.mosquitto.org"
PORT = 1883
TOPIC = "uca/iot/piscine/22410777/access"

def on_connect(client, userdata, flags, rc):
    """Callback de connexion"""
    if rc == 0:
        print(f"\n✅ Connecté au broker MQTT: {BROKER}:{PORT}")
        print(f"📡 Souscription au topic: {TOPIC}")
        print(f"{'='*80}\n")
        client.subscribe(TOPIC)
    else:
        print(f"❌ Échec de connexion. Code: {rc}")
        sys.exit(1)

def on_message(client, userdata, msg):
    """Callback de réception de message"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    print(f"{'='*80}")
    print(f"⏰ Timestamp: {timestamp}")
    print(f"📬 Topic: {msg.topic}")
    print(f"{'='*80}")
    
    try:
        # Décoder le message
        payload = msg.payload.decode("utf-8")
        
        # Parser en JSON
        try:
            data = json.loads(payload)
            print(f"📦 Message (JSON formaté):")
            print(json.dumps(data, indent=2, ensure_ascii=False))
            
            # Extraire les infos importantes
            print(f"\n{'─'*80}")
            print(f"🔍 Informations clés:")
            print(f"{'─'*80}")
            
            # Pool ID
            if "info" in data and "ident" in data["info"]:
                ident = data["info"]["ident"]
                print(f"  🏊 Pool ID: {ident}")
            
            # Statut occupation
            if "piscine" in data:
                occuped = data["piscine"].get("occuped", "N/A")
                print(f"  🚦 Occupé: {occuped}")
                
                hotspot = data["piscine"].get("hotspot", "N/A")
                print(f"  📶 Hotspot: {hotspot}")
            
            # Température
            if "status" in data:
                temp = data["status"].get("temperature", "N/A")
                print(f"  🌡️ Température: {temp}°C")
            
            # Port cible
            if "reporthost" in data:
                target_ip = data["reporthost"].get("target_ip", "N/A")
                target_port = data["reporthost"].get("target_port", "N/A")
                print(f"  🌐 Target: {target_ip}:{target_port}")
            
        except json.JSONDecodeError:
            print(f"📦 Message (brut):")
            print(payload)
    
    except Exception as e:
        print(f"❌ Erreur lors du décodage: {e}")
        print(f"📦 Payload brut: {msg.payload}")
    
    print(f"{'='*80}\n")

def on_disconnect(client, userdata, rc):
    """Callback de déconnexion"""
    print(f"\n⚠️ Déconnecté du broker. Code: {rc}")

def main():
    print(f"\n{'='*80}")
    print(f"🔍 Moniteur MQTT WaterBnB")
    print(f"{'='*80}")
    print(f"Broker: {BROKER}:{PORT}")
    print(f"Topic: {TOPIC}")
    print(f"\nAppuyez sur Ctrl+C pour arrêter")
    print(f"{'='*80}\n")
    
    # Créer le client MQTT
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_disconnect = on_disconnect
    
    try:
        # Connexion
        print(f"🔄 Connexion en cours...")
        client.connect(BROKER, PORT, 60)
        
        # Boucle de réception
        client.loop_forever()
        
    except KeyboardInterrupt:
        print(f"\n\n👋 Arrêt du moniteur...")
        client.disconnect()
        
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
