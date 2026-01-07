import csv
from pymongo import MongoClient
from pymongo.server_api import ServerApi


class DatabaseManager:    
    def __init__(self, uri, admin_mode=True, csv_file="usersM1_2026.csv"):
        self.uri = uri
        self.admin_mode = admin_mode
        self.csv_file = csv_file
        try:
            self.client = MongoClient(uri, server_api=ServerApi('1'))
            self.db = self.client["WaterBnB"]
            print("Connected to MongoDB")
        except Exception as e:
            print(f"Error connecting to MongoDB: {e}")
            raise
        
        self.users_collection = self.db['users']
        self.pool_requests_collection = self.db['pool_requests']
        
        if self.admin_mode:
            self._import_users()
    
    def _import_users(self):
        print("Importing authorized users...")
        try:
            self.users_collection.delete_many({})
            
            with open(self.csv_file, 'r', encoding='utf-8') as f:
                excel = csv.reader(f)
                imported_count = 0
                
                for line in excel:
                    if not line or len(line) == 0:
                        continue  
                    fields = line[0].split(';')
                    if len(fields) >= 2:
                        name = fields[0]
                        num = fields[1]
                        if self.users_collection.find_one({"name": name}) is None:
                            self.users_collection.insert_one({
                                "name": name,
                                "num": num
                            })
                            imported_count += 1
                
                print(f"Imported {imported_count} users")
        except FileNotFoundError:
            print(f"Warning: User file '{self.csv_file}' not found")
        except Exception as e:
            print(f"Error importing users: {e}")
    
    def user_exists(self, username):
        return self.users_collection.find_one({"name": username}) is not None
    
    def log_access_request(self, document):
        result = self.pool_requests_collection.insert_one(document)
        return result.inserted_id


# Global database instance (to be initialized by app.py)
db_manager = None


def init_database(uri="mongodb+srv://ibrahima_camara:Ibra0617262640@waterbnb.n0btamn.mongodb.net/?appName=WaterBnB", 
        admin_mode=True):

    global db_manager
    db_manager = DatabaseManager(uri, admin_mode)
    return db_manager
