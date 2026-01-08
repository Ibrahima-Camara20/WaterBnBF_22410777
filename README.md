## Résumé du Projet

Ce projet implémente un système de contrôle d'accès intelligent où :

1.  Les utilisateurs sont authentifiés via une interface Web.
2.  L'accès est vérifié en temps réel (utilisateurs autorisés + disponibilité de la piscine).
3.  L'ouverture de la porte est déclenchée à distance via MQTT.
4.  Toutes les tentatives d'accès sont journalisées pour analyse.

Les technologies clés utilisées sont :

- **Backend** : Python Flask
- **Base de données** : MongoDB (Atlas)
- **Communication** : MQTT (Mosquitto)
- **Matériel** : ESP32 (avec capteurs et LEDs)

## Configuration

1. **Broker** : Hivemq : brokerhivemq.com
2. **Topic** : uca/iot/piscine/ pour la souscription et uca/iot/piscine/{idswp}/access pour la publication (pour le retour vers l'ESP32)
3. **MQTT** : Mosquitto
4. **Base de données** : MongoDB Atlas
5. **Backend** : Flask sur Render avec l'url : https://waterbnbf-22410777.onrender.com/
6. **Frontend** : Node-RED avec le fichier 'src/data/flows.json'
7. **Tableau de bord** : MongoDB Charts avec le lien public : https://charts.mongodb.com/charts-waterbnb-yijuviu/public/dashboards/024950d0-fa64-4236-841c-35d2700befc4

Le flux de fonctionnement est le suivant :

1.  **Demande d'accès** :
    - L'utilisateur accède depuis Node-RED et entre son nom et clique sur une piscine pour démander l'accès. Ensuite Node-RED envoie une requête GET à l'URL `https://waterbnbf-22410777.onrender.com/open?idu={idu}&idswp={idswp}` avec son identifiant (`idu`) et l'identifiant de la piscine (`idswp`).
2.  **Vérification Serveur (Flask) sur Render** :

    - Le serveur vérifie si l'utilisateur existe dans la base de données **MongoDB**.
    - Il vérifie l'état de la piscine (occupé/libre) via les données reçues par **MQTT** depuis l'ESP32.

3.  **Décision & Commande** :

    - **Au début** : La LED est verte tant que la piscine est libre.
    - **Si Accès Autorisé** : Le serveur publie la commande `GRANTED` sur le topic uca/iot/piscine/{idswp}/access. L'ESP32 allume la LED jaune. Elle reste allumé pendant 3 si il y'a de le capteur de lumière reçoit un signal superieur a 2000 elle reste jaune.
    - **Si Refusé** : Le serveur publie `DENIED`. L'ESP32 signale le refus (LED rouge). Elle reste rouge pendant 30 secondes.

4.  **Journalisation & Analyse** :

    - Chaque requête est enregistrée dans la collection `pool_requests` de MongoDB.
    - Un tableau de bord **MongoDB Charts** permet de visualiser les statistiques (fréquentation, utilisateurs actifs, température de l'eau). Voici le lien public : https://charts.mongodb.com/charts-waterbnb-yijuviu/public/dashboards/024950d0-fa64-4236-841c-35d2700befc4

5.  **Suivi en Temps Réel** :
    - L'ESP32 publie régulièrement la température de l'eau et l'état d'occupation, permettant au serveur d'avoir une vue à jour.
