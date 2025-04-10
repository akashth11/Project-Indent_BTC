import requests
import jwt
import time
import json

def generate_jwt(api_key, secret_key):
    payload = {
        "iss": api_key,
        "iat": int(time.time()),
        "jti": "unique_request_id"
    }
    token = jwt.encode(payload, secret_key, algorithm="HS256")
    return token

def fetch_all_records():
    api_key = "91bfe158-b7c6-4492-829d-d66fad71fcce"
    secret_key = "8Wh8lSoJIzJ20aQlkk5ZovoXTOKMRKS1DuExsF5rk48"
    jwt_token = generate_jwt(api_key, secret_key)
    
    url = "https://api.ristaapps.com/v1/inventory/supplieritem/list"
    headers = {
        "x-api-key": api_key,
        "x-api-token": jwt_token
    }
    
    all_records = []
    params = {}

    while True:
        response = requests.get(url, headers=headers, params=params)
        
        # Log response
        try:
            data = response.json()
            
        except json.JSONDecodeError:
            print("Failed to decode JSON response")
            break
        
        # Ensure 'data' key exists
        if "data" in data and isinstance(data["data"], list):
            all_records.extend(data["data"])
        else:
            print("'data' key not found or not a list")
            break

       # Check for pagination
        last_key = data.get("lastKey")
        if last_key:
            print(f"Response Code: {response.status_code} Using lastKey: {last_key}")  # Log lastKey
            params["lastKey"] = last_key
        else:
            print("No more records to fetch.")
            break
    
    return all_records

def save_to_json(records, filename="supplier_items.json"):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=4)
    
    print(f"Data saved to {filename}")

if __name__ == "__main__":
    records = fetch_all_records()
    save_to_json(records)
