import requests
import json
import time
import hmac
import hashlib
import base64
import datetime
import jwt  # PyJWT library for JWT token generation
import os  # For handling file directories

# API Endpoints
LOGIN_URL = "https://bluetokai.api.nymbleup.com/api/v1/users/login/"
API_URL = "https://bluetokai.api.nymbleup.com/api/v1/orders/integration/order-detail-report/"
BRANCH_LIST_URL = "https://api.ristaapps.com/v1/branch/list"

# Credentials
EMAIL = "admin@nymbleup.com"
PASSWORD = "testpass"
API_KEY = "91bfe158-b7c6-4492-829d-d66fad71fcce"
SECRET_KEY = "8Wh8lSoJIzJ20aQlkk5ZovoXTOKMRKS1DuExsF5rk48"

# Get current date
DATE = datetime.datetime.today().strftime("%Y-%m-%d")

# Define the folder to save JSON files
SAVE_FOLDER = "Nymbl Order Data"

# Ensure the folder exists
if not os.path.exists(SAVE_FOLDER):
    os.makedirs(SAVE_FOLDER)

# Generate JWT Token for Rista API
def generate_jwt_token():
    token_creation_time = int(datetime.datetime.now(datetime.UTC).timestamp())
    payload = {"iss": API_KEY, "iat": token_creation_time}
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    #print(f"Generated Token: {token}")
    return token

# Fetch branch codes
def get_branch_codes():
    api_token = generate_jwt_token()
    headers = {"x-api-key": API_KEY, "x-api-token": api_token}
    response = requests.get(BRANCH_LIST_URL, headers=headers)
    
    if response.status_code == 200:
        branches = response.json()
        return [branch["branchCode"] for branch in branches if "branchCode" in branch]
    else:
        print(f"❌ Failed to fetch branch codes: {response.text}")
        return []

# Login and Token Generation
def get_auth_token():
    payload = {"email": EMAIL, "password": PASSWORD}
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    
    response = requests.post(LOGIN_URL, headers=headers, json=payload)
    if response.status_code == 200:
        token = response.json().get("access")  # Extract access token
        print("✅ Authentication successful!")
        return token
    else:
        print(f"❌ Authentication failed: {response.text}")
        return None

# Fetch Orders
def fetch_orders(token, store_ids):
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    all_data = []
    
    for store_id in store_ids:
        payload = {"store_id": store_id, "date": DATE}
        
        try:
            response = requests.post(API_URL, headers=headers, json=payload)
            if response.status_code == 200:
                data = response.json()
                
                if data and "data" in data:  # Ensure 'data' key exists
                    for item in data["data"]:
                        # Add "concat" without modifying existing attributes
                        item["ConcatNMBLPY"] = f"{item['BUYER STORE CODE']}{item['SUPPLIER CODE']}"
                    
                    all_data.append({store_id: {"message": data["message"], "data": data["data"]}})
                    print(f"✅ Data fetched for {store_id}")
                else:
                    print(f"⚠️ No data returned for {store_id}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Error fetching data for {store_id}: {str(e)}")
        
        # time.sleep(1)  # Pause between requests to avoid rate limiting

    if all_data:
        filename = os.path.join(SAVE_FOLDER, f"order_data_{DATE}.json")
        with open(filename, "w") as f:
            json.dump(all_data, f, indent=4)
        print(f"\n🎯 Data saved to '{filename}'")
    else:
        print("\n⚠️ No data to save!")

# Main Execution
store_ids = get_branch_codes()
if store_ids:
    token = get_auth_token()
    if token:
        fetch_orders(token, store_ids)
