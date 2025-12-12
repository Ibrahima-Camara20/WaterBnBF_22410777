import json
import csv

from flask import request
from flask import jsonify
from flask import Flask
from flask import session
from flask import render_template
#https://python-adv-web-apps.readthedocs.io/en/latest/flask.html

#https://www.emqx.com/en/blog/how-to-use-mqtt-in-flask
from flask_mqtt import Mqtt
from flask_pymongo import PyMongo
from pymongo import MongoClient
from pymongo.server_api import ServerApi

#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
# Global State
pool_status = {}

# Initialisation :  Mongo DataBase

# Connect to Cluster Mongo : attention aux permissions "network"/MONGO  !!!!!!!!!!!!!!!!
ADMIN=True # Faut etre ADMIN/mongo pour ecrire dans la base
#client = MongoClient("mongodb+srv://menez:i.....Q@cluster0.x0zyf.mongodb.net/?retryWrites=true&w=majority")
#client = MongoClient("mongodb+srv://logincfsujet:pwdcfsujet@cluster0.x0zyf.mongodb.net/?retryWrites=true&w=majority")
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
#-----------------------------------------------------------------------------
# Looking for "WaterBnB" database in the cluster
#https://stackoverflow.com/questions/32438661/check-database-exists-in-mongodb-using-pymongo


#-----------------------------------------------------------------------------
# Looking for "users" collection in the WaterBnB database


#-----------------------------------------------------------------------------
# import authorized users .. if not already in ?
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
    

#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
# Initialisation :  Flask service
app = Flask(__name__)

# Notion de session ! .. to share between routes !
# https://flask-session.readthedocs.io/en/latest/quickstart.html
# https://testdriven.io/blog/flask-sessions/
# https://www.fullstackpython.com/flask-globals-session-examples.html
# https://stackoverflow.com/questions/49664010/using-variables-across-flask-routes
app.secret_key = 'BAD_SECRET_KEY'
  
#-----------------------------------------------------------------------------
@app.route('/')
def hello_world():
    return render_template('index.html') #'Hello, World!'

#Test with =>  curl https://waterbnbf.onrender.com/

#-----------------------------------------------------------------------------
"""
#https://stackabuse.com/how-to-get-users-ip-address-using-flask/
@app.route("/ask_for_access", methods=["POST"])
def get_my_ip():
    ip_addr = request.remote_addr
    return jsonify({'ip asking ': ip_addr}), 200

# Test/Compare with  =>curl  https://httpbin.org/ip

#Proxies can make this a little tricky, make sure to check out ProxyFix
#(Flask docs) if you are using one.
#Take a look at request.environ in your particular environment :
@app.route("/ask_for_access", methods=["POST"])
def client():
    ip_addr = request.environ['REMOTE_ADDR']
    return '<h1> Your IP address is:' + ip_addr
"""

#https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/X-Forwarded-For
#If a request goes through multiple proxies, the IP addresses of each successive proxy is listed.
# voir aussi le parsing !

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

# Test with => curl -X POST https://waterbnbf.onrender.com/open?who=gillou
# Test with => curl https://waterbnbf.onrender.com/open?who=gillou

@app.route("/users")
def lists_users(): # Liste des utilisateurs déclarés
    """
    curl https://waterbnbf.onrender.com/users
    """
    todos = userscollection.find()
    return jsonify([todo['name'] for todo in todos])

@app.route('/publish', methods=['POST'])
def publish_message():
    """
    mosquitto_sub -h test.mosquitto.org -t gillou
    mosquitto_pub -h test.mosquitto.org -t gillou -m tutu
    curl -X POST -H Content-Type:application/json -d "{\"topic\":\"gillou\",\"msg\":\"hello\"}"  https://waterbnbf.onrender.com/publish
    curl -H 'Content-Type: application/json' -d '{ "topic":"gillou","msg":"gillou"}'  -X POST       https://waterbnbf.onrender.com/publish
    """
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
    
#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%        
# Initialisation MQTT
app.config['MQTT_BROKER_URL'] =  "test.mosquitto.org"
#app.config['MQTT_BROKER_URL'] =  "broker.hivemq.com"
app.config['MQTT_BROKER_PORT'] = 1883
#app.config['MQTT_USERNAME'] = ''  # Set this item when you need to verify username and password
#app.config['MQTT_PASSWORD'] = ''  # Set this item when you need to verify username and password
#app.config['MQTT_KEEPALIVE'] = 5  # Set KeepAlive time in seconds
app.config['MQTT_TLS_ENABLED'] = False  # If your broker supports TLS, set it True

mqtt_client = Mqtt(app)
topicname = "uca/iot/piscine"

# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
# MQTT callbacks
@mqtt_client.on_connect()
def handle_connect(client, userdata, flags, rc):
   if rc == 0:
       print('Connected successfully')
       mqtt_client.subscribe(topicname) # subscribe topic
   else:
       print('Bad connection. Code:', rc)

# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
# MQTT callbacks
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



#%%%%%%%%%%%%%  main driver function
if __name__ == '__main__':
    
    # run() method of Flask class runs the application 
    # on the local development server.
    app.run(debug=False) #host='127.0.0.1', port=5000)
    
