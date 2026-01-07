# WaterBnB - Système de Contrôle d'Accès de Piscine

WaterBnB est une solution IoT complète permettant de gérer l'accès sécurisé à des piscines partagées. Le système combine un serveur Web, une base de données, un broker MQTT et des microcontrôleurs ESP32 pour offrir une expérience sans clé fluide et sécurisée.

## 📝 Résumé du Projet

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

## ⚙️ Comment ça marche ?

Le flux de fonctionnement est le suivant :

1.  **Demande d'accès** :
    - L'utilisateur scanne un QR Code ou accède à l'URL `/open` avec son identifiant (`idu`) et l'identifiant de la piscine (`idswp`).
2.  **Vérification Serveur (Flask)** :

    - Le serveur vérifie si l'utilisateur existe dans la base de données **MongoDB**.
    - Il vérifie l'état de la piscine (occupé/libre) via les données reçues par **MQTT** depuis l'ESP32.

3.  **Décision & Commande** :

    - **Si Accès Autorisé** : Le serveur publie la commande `GRANTED` sur le topic MQTT de la piscine. L'ESP32 allume la LED verte (ou ouvre la gâche électrique).
    - **Si Refusé** : Le serveur publie `DENIED`. L'ESP32 signale le refus (LED rouge).

4.  **Journalisation & Analyse** :

    - Chaque requête est enregistrée dans la collection `pool_requests` de MongoDB.
    - Un tableau de bord **MongoDB Charts** permet de visualiser les statistiques (fréquentation, utilisateurs actifs, température de l'eau).

5.  **Suivi en Temps Réel** :
    - L'ESP32 publie régulièrement la température de l'eau et l'état d'occupation, permettant au serveur d'avoir une vue à jour.

---

## 🔧 Utilitaire de Validation JSON (Legacy)

To use the val.py you have to install python3 and the package: jsonschema

```bash
pip3 install jsonschema
```

Put your json into a file named test.json
You can then run the validator with the command: python3 val.py test.json
Example: `python3 val.py ./test.json`
