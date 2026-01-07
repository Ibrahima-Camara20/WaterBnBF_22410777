import json
import os

from flask import request
from flask import jsonify
from flask import Flask
from flask import session
from flask import render_template

from flask_mqtt import Mqtt

# Import custom modules
from db_config import init_database
from mqtt_handler import temp_manager
import access_logger

# Global state
pool_status = {}

# Initialize database
ADMIN = False  # Faut etre ADMIN/mongo pour ecrire dans la base
uri = "mongodb+srv://ibrahima_camara:Ibra0617262640@waterbnb.n0btamn.mongodb.net/?appName=WaterBnB"
db_manager = init_database(uri, admin_mode=ADMIN)

app = Flask(__name__)
app.secret_key = 'BAD_SECRET_KEY'

@app.route('/')
def hello_world():
    return 'Welcome to Ibrahima and Mamadou Swimming Pool Access Control System!'
@app.route("/open", methods= ['GET', 'POST'])
def openthedoor():
    idu = request.args.get('idu') # idu : clientid of the service
    idswp = request.args.get('idswp')  #idswp : id of the swimming pool
    session['idu'] = idu
    session['idswp'] = idswp
    print("\n Peer = {}".format(idu))

    granted = "NO"
    # 1. Check if user exists
    if db_manager.user_exists(idu):
        # 2. Check if pool exists and is available (NOT occupied)
        # Use .get() to avoid KeyError if pool not in status dict
        is_occupied = pool_status.get(idswp, False)  # Default to False (available) if unknown
        
        if not is_occupied:
            granted = "YES"
            print(f"Access GRANTED for {idu} to {idswp}")
            # Send Green command
            topic = f"uca/iot/piscine/{idswp}/access"
            message = json.dumps({"command": "GRANTED", "user": idu})
            mqtt_client.publish(topic, message, qos=1)
        else:
            print(f"Access REFUSED: {idswp} is OCCUPIED")
            # Send Red command (Occupied)
            topic = f"uca/iot/piscine/{idswp}/access"
            message = json.dumps({"command": "DENIED", "reason": "Occupied"})
            mqtt_client.publish(topic, message, qos=1) 
    else:
        print(f"Access REFUSED: User {idu} not found")
        # Send Red command (Invalid User)
        if idswp:
            topic = f"uca/iot/piscine/{idswp}/access"
            message = json.dumps({"command": "DENIED", "reason": "Invalid User"})
            mqtt_client.publish(topic, message, qos=1)

    # 📝 LOG ACCESS REQUEST TO MONGODB
    if idu and idswp:
        access_logger.log_access_request(db_manager, temp_manager, idu, idswp, granted)

    return  jsonify({'idu' : session['idu'], 'idswp' : session['idswp'], "granted" : granted}), 200

@app.route("/users")
def lists_users(): # Liste des utilisateurs déclarés
    todos = db_manager.users_collection.find()
    return jsonify([todo['name'] for todo in todos])

@app.route('/publish', methods=['POST'])
def publish_message():
    content_type = request.headers.get('Content-Type')
    print("\n Content type = {}".format(content_type))

    request_data = request.get_json()
    msg_fromreq =  request_data['msg']
    topic_fromreq = request_data['topic']
    print(f"\n Now we will publish msg = {msg_fromreq}")
    print(f"\n on topic = {topic_fromreq}")
    
    publish_result = mqtt_client.publish(topic_fromreq, msg_fromreq, qos=2) 

    print(f"\n publish_result is {publish_result}\n") 
    return  jsonify({'code': publish_result[0]})
    
app.config['MQTT_BROKER_URL'] =  "test.mosquitto.org"
app.config['MQTT_BROKER_PORT'] = 1883
app.config['MQTT_TLS_ENABLED'] = False  # If your broker supports TLS, set it True

# Initialize MQTT - REQUIRED for application to run
topicname = "uca/iot/piscine"

try:
    mqtt_client = Mqtt(app)
    print("MQTT client initialized")
    
    @mqtt_client.on_connect()
    def handle_connect(client, userdata, flags, rc):
       if rc == 0:
           print('MQTT connected successfully')
           mqtt_client.subscribe(topicname) # subscribe topic
       else:
           print('Bad MQTT connection. Code:', rc)
except Exception as e:
    print(f"\nERROR: MQTT connection failed: {e}")
    print(f"Broker: {app.config['MQTT_BROKER_URL']}:{app.config['MQTT_BROKER_PORT']}")
    exit(1)

@mqtt_client.on_message()
def handle_mqtt_message(client, userdata, msg):
    global topicname
    
    print("\n msg.topic = {}".format(msg.topic))
    print("\n topicname = {}".format(topicname))
    
    if (msg.topic == topicname) : # cf https://stackoverflow.com/questions/63580034/paho-updating-userdata-from-on-message-callback
        decoded_message =str(msg.payload.decode("utf-8"))
        #print("\ndecoded message received = {}".format(decoded_message))
        dic =json.loads(decoded_message) # from string to dict
        print("\n Dictionnary  received = {}".format(dic))

    #-----------------------------------------------------------------------------
    # Update pool status and temperature
    try:
        ident = dic["info"]["ident"]
        occuped = dic["piscine"]["occuped"] # Boolean: True if occupied (Yellow), False if free (Green)
        # ident = P__22410777 how to get just the number ?
        ident = ident.split("_")[2] 
        # Update global state

        pool_status[ident] = occuped
        print(f"\n Updated status for {ident}: Occupied={occuped}")
        
        # 🌡️ Update temperature data
        temp_manager.process_mqtt_message(dic)
        
    except KeyError as e:
        print(f"KeyError processing MQTT message: {e}")


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 1200)))
    
