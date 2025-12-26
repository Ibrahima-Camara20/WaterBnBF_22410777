import json
import csv
import os

from flask import request
from flask import jsonify
from flask import Flask
from flask import session
from flask import render_template

from flask_mqtt import Mqtt
from flask_pymongo import PyMongo
from pymongo import MongoClient
from pymongo.server_api import ServerApi

pool_status = {}

ADMIN=True # Faut etre ADMIN/mongo pour ecrire dans la base
uri = "mongodb+srv://ibrahima_camara:Ibra0617262640@waterbnb.n0btamn.mongodb.net/?appName=WaterBnB"
try:
    client = MongoClient(uri, server_api=ServerApi('1'))
    db = client["WaterBnB"]
    collname= 'users'
    userscollection = db[collname]
    print("Connected to collection")
except Exception as e:
    print(f"Error connecting to MongoDB: {e}")
    exit(1)

if ADMIN :
    print("Importing authorized users")
    userscollection.delete_many({})  # empty collection
    excel = csv.reader(open("usersM1_2026.csv")) # list of authorized users
    for l in excel : #import in mongodb
        if not l or len(l) == 0: # Skip empty lines
            continue
        ls = (l[0].split(';'))
        if userscollection.find_one({"name" : ls[0]}) ==  None :
            userscollection.insert_one({"name": ls[0], "num": ls[1]})

app = Flask(__name__)
app.secret_key = 'BAD_SECRET_KEY'

@app.route('/')
def hello_world():
    return render_template('index.html') #'Hello, World!'

@app.route("/open", methods= ['GET', 'POST'])
# @app.route('/open') # ou en GET seulement
def openthedoor():
    idu = request.args.get('idu') # idu : clientid of the service
    idswp = request.args.get('idswp')  #idswp : id of the swimming pool
    session['idu'] = idu
    session['idswp'] = idswp
    print("\n Peer = {}".format(idu))

    # ip addresses of the machine asking for opening
    ip_addr = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)

    granted = "NO"
    
    # 1. Check if user exists
    if userscollection.find_one({"name" : idu}) !=  None:
        # 2. Check if pool exists and is available (NOT occupied)
        if idswp in pool_status:
           is_occupied = pool_status[idswp]
           if not is_occupied:
               granted = "YES"
               print(f"Access GRANTED for {idu} to {idswp}")
               # Send Green command
               mqtt_client.publish(f"uca/iot/piscine/{idswp}/access", json.dumps({"command": "GRANTED", "user": idu}))
           else:
               print(f"Access REFUSED: {idswp} is OCCUPIED")
               # Send Red command (Occupied) - Optional, maybe just stay Yellow?
               # Instruction says: "Si rouge alors l'accès est refusé"
               mqtt_client.publish(f"uca/iot/piscine/{idswp}/access", json.dumps({"command": "DENIED", "reason": "Occupied"}))
        else:
            print(f"Access REFUSED: {idswp} unknown or no status received yet")
            # Send Red command (Unknown pool)
            mqtt_client.publish(f"uca/iot/piscine/{idswp}/access", json.dumps({"command": "DENIED", "reason": "Unknown"}))
            
    else:
        print(f"Access REFUSED: User {idu} not found")
        # Send Red command (Invalid User)
        if idswp:
            mqtt_client.publish(f"uca/iot/piscine/{idswp}/access", json.dumps({"command": "DENIED", "reason": "Invalid User"}))

    return  jsonify({'idu' : session['idu'], 'idswp' : session['idswp'], "granted" : granted}), 200

@app.route("/users")
def lists_users(): # Liste des utilisateurs déclarés
    todos = userscollection.find()
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
    
    publish_result = mqtt_client.publish(topic_fromreq, msg_fromreq, qos=2) # Ce depend un peu beauooup de la forme du brooker !

    print(f"\n publish_result is {publish_result}\n") # j'ai l'impression que le publish se fait .... mais apres ???? 
    return  jsonify({'code': publish_result[0]})
    
app.config['MQTT_BROKER_URL'] =  "test.mosquitto.org"
app.config['MQTT_BROKER_PORT'] = 1883
app.config['MQTT_TLS_ENABLED'] = False  # If your broker supports TLS, set it True

mqtt_client = Mqtt(app)
topicname = "uca/iot/piscine"

@mqtt_client.on_connect()
def handle_connect(client, userdata, flags, rc):
   if rc == 0:
       print('Connected successfully')
       mqtt_client.subscribe(topicname) # subscribe topic
   else:
       print('Bad connection. Code:', rc)

@mqtt_client.on_message()
def handle_mqtt_message(client, userdata, msg):
    global topicname
    
    #    print(f'Received message on topic: {msg.topic} 
    print("\n msg.topic = {}".format(msg.topic))
    print("\n topicname = {}".format(topicname))
    
    if (msg.topic == topicname) : # cf https://stackoverflow.com/questions/63580034/paho-updating-userdata-from-on-message-callback
        decoded_message =str(msg.payload.decode("utf-8"))
        #print("\ndecoded message received = {}".format(decoded_message))
        dic =json.loads(decoded_message) # from string to dict
        print("\n Dictionnary  received = {}".format(dic))

    #-----------------------------------------------------------------------------
    # Update pool status
    try:
        ident = dic["info"]["ident"]
        occuped = dic["piscine"]["occuped"] # Boolean: True if occupied (Yellow), False if free (Green)
        
        # Update global state
        pool_status[ident] = occuped
        print(f"\n Updated status for {ident}: Occupied={occuped}")
        
    except KeyError as e:
        print(f"KeyError processing MQTT message: {e}")


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 1200)))
    
