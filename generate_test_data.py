"""
Générateur de données de test pour pool_requests
Génère 50+ requêtes basées sur les vrais utilisateurs
"""

import csv
import random
from datetime import datetime, timedelta

# Lire les utilisateurs réels
print("📖 Lecture des utilisateurs de usersM1_2026.csv...")
users = []
with open("usersM1_2026.csv", "r", encoding="utf-8") as f:
    # Lecture ligne par ligne simple pour éviter les problèmes de formatage
    lines = f.readlines()
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Découpage manuel par point-virgule
        parts = line.split(';')
        if len(parts) >= 1 and parts[0].strip():
            users.append(parts[0].strip())  # Nom de l'utilisateur

print(f"✅ {len(users)} utilisateurs trouvés : {users[:5]}...")

if not users:
    print("❌ ERREUR: Aucun utilisateur trouvé !")
    exit(1)

# Piscines (numéros étudiants fictifs)
pools = [
    "P_22410777",  # Mamadou et Ibrahima
    "P_12345678",
    "P_23456789",
    "P_34567890",
    "P_45678901"
]

# Générer les données de test
count = 150  # Demande utilisateur: "100 50" -> on met 150
print(f"\n🔄 Génération de {count} requêtes de test...")
test_data = []

# Date de départ: il y a 7 jours
start_date = datetime.now() - timedelta(days=7)

for i in range(count):
    # Sélectionner un utilisateur aléatoire
    user = random.choice(users)
    
    # Sélectionner une piscine aléatoire
    pool = random.choice(pools)
    
    # Décider si accordé ou refusé (70% accordé, 30% refusé)
    granted = "YES" if random.random() < 0.7 else "NO"
    
    # Date aléatoire sur les 7 derniers jours
    random_hours = random.randint(0, 7*24)  # 0 à 168 heures
    date = start_date + timedelta(hours=random_hours)
    
    # Température aléatoire entre 22 et 30°C
    temp = round(random.uniform(22.0, 30.0), 2)
    
    test_data.append({
        "username": user,
        "pool": pool,
        "granted": granted,
        "date": date.isoformat(),
        "temperature": temp
    })

# Trier par date
test_data.sort(key=lambda x: x["date"])

# Écrire dans le fichier CSV
print("\n💾 Écriture dans test_pool_requests.csv...")
with open("test_pool_requests.csv", "w", encoding="utf-8", newline='') as f:
    writer = csv.DictWriter(f, fieldnames=["username", "pool", "granted", "date", "temperature"], delimiter=';')
    writer.writeheader()
    writer.writerows(test_data)

print(f"✅ {len(test_data)} requêtes générées!")

# Statistiques
print("\n" + "="*60)
print("📊 Statistiques des données générées")
print("="*60)

granted_count = sum(1 for d in test_data if d["granted"] == "YES")
denied_count = len(test_data) - granted_count

print(f"Total: {len(test_data)} requêtes")
print(f"Accordées (YES): {granted_count} ({granted_count/len(test_data)*100:.1f}%)")
print(f"Refusées (NO): {denied_count} ({denied_count/len(test_data)*100:.1f}%)")
print(f"\nPériode: {test_data[0]['date'][:10]} à {test_data[-1]['date'][:10]}")
print(f"Piscines: {len(pools)} ({', '.join(pools)})")
print(f"Utilisateurs uniques: {len(set(d['username'] for d in test_data))}")

# Top 3 utilisateurs les plus actifs
user_counts = {}
for d in test_data:
    user_counts[d['username']] = user_counts.get(d['username'], 0) + 1

top_users = sorted(user_counts.items(), key=lambda x: x[1], reverse=True)[:3]
print(f"\n🏆 Top 3 utilisateurs:")
for i, (user, count) in enumerate(top_users, 1):
    print(f"  {i}. {user}: {count} requêtes")

# Top 3 piscines les plus demandées
pool_counts = {}
for d in test_data:
    pool_counts[d['pool']] = pool_counts.get(d['pool'], 0) + 1

top_pools = sorted(pool_counts.items(), key=lambda x: x[1], reverse=True)[:3]
print(f"\n🏊 Top 3 piscines:")
for i, (pool, count) in enumerate(top_pools, 1):
    print(f"  {i}. {pool}: {count} requêtes")

print("\n✅ Fichier prêt pour l'import!")
print("💡 Lancez: python import_test_data.py")
