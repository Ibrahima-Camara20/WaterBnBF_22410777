from datetime import datetime

def format_pool_id(pool_id):

    if pool_id and not pool_id.startswith("P_"):
        return f"P_{pool_id}"
    return pool_id

def create_access_document(username, pool_id, granted, temperature):
    document = {
        "username": username,
        "pool": format_pool_id(pool_id),
        "granted": granted,
        "date": datetime.now(),
        "data": {
            "temp": float(temperature) if temperature is not None else 25.0
        }
    }    
    return document

def log_access_request(db_manager, temp_manager, username, pool_id, granted):
    temperature = temp_manager.get_temperature(pool_id)
    document = create_access_document(username, pool_id, granted, temperature)
    try:
        doc_id = db_manager.log_access_request(document)
        print(f"Logged access request: {username} -> {format_pool_id(pool_id)} [{granted}] @ {temperature}°C")
        return doc_id
    except Exception as e:
        print(f"Error logging access request: {e}")
        return None
