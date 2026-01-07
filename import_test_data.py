"""
Script pour importer les données de test dans MongoDB
Insère des requêtes d'accès fictives dans la collection pool_requests
"""

import csv
from datetime import datetime
from pymongo import MongoClient
from pymongo.server_api import ServerApi

# Configuration MongoDB
uri = "mongodb+srv://ibrahima_camara:Ibra0617262640@waterbnb.n0btamn.mongodb.net/?appName=WaterBnB"

print("="*80)
print("📥 Import des données de test dans MongoDB")
print("="*80)

try:
    # Connexion à MongoDB
    print("\n🔄 Connexion à MongoDB...")
    client = MongoClient(uri, server_api=ServerApi('1'))
    db = client["WaterBnB"]
    collection = db["pool_requests"]
    print("✅ Connecté à MongoDB")
    
    # Lire le fichier CSV
    print("\n📖 Lecture du fichier test_pool_requests.csv...")
    with open("test_pool_requests.csv", "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=';')
        
        imported_count = 0
        for row in reader:
            # Créer le document
            document = {
                "username": row["username"],
                "pool": row["pool"],
                "granted": row["granted"],
                "date": datetime.fromisoformat(row["date"]),
                "data": {
                    "temp": float(row["temperature"])
                }
            }
            
            # Insérer dans MongoDB
            collection.insert_one(document)
            imported_count += 1
            print(f"  ✓ {row['username']} -> {row['pool']} [{row['granted']}] @ {row['temperature']}°C")
    
    print(f"\n✅ {imported_count} requêtes importées avec succès!")
    
    # Statistiques
    print("\n" + "="*80)
    print("📊 Statistiques de la collection pool_requests")
    print("="*80)
    
    total = collection.count_documents({})
    print(f"Total de documents: {total}")
    
    granted_count = collection.count_documents({"granted": "YES"})
    denied_count = collection.count_documents({"granted": "NO"})
    print(f"Accès accordés: {granted_count}")
    print(f"Accès refusés: {denied_count}")
    
    pools = collection.distinct("pool")
    print(f"Piscines uniques: {', '.join(pools)}")
    
    print("\n✅ Import terminé!")
    print("\n💡 Vous pouvez maintenant créer vos charts MongoDB avec ces données")
    
except FileNotFoundError:
    print("❌ Fichier test_pool_requests.csv introuvable")
    print("   Assurez-vous que le fichier existe dans le même dossier")
except Exception as e:
    print(f"❌ Erreur: {e}")
finally:
    if 'client' in locals():
        client.close()
        print("\n🔌 Déconnexion de MongoDB")
