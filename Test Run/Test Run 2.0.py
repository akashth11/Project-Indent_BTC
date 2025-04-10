import json
import datetime
import requests
import jwt
import time
from collections import defaultdict

# API Endpoint for Indent Creation in Rista
INDENT_URL = "https://api.ristaapps.com/v1/inventory/indent"

# Rista API Credentials
API_KEY = "91bfe158-b7c6-4492-829d-d66fad71fcce"
SECRET_KEY = "8Wh8lSoJIzJ20aQlkk5ZovoXTOKMRKS1DuExsF5rk48"

# Generate JWT Token for Rista API
def generate_jwt(api_key, secret_key):
    payload = {
        "iss": api_key,
        "iat": int(time.time()),
        "jti": "unique_request_id"
    }
    token = jwt.encode(payload, secret_key, algorithm="HS256")
    return token

# Create Indent in Rista
def create_indent(branch_code, branch_name, supplier_code, items, delivery_date):
    api_token = generate_jwt()
    headers = {"x-api-key": API_KEY, "x-api-token": api_token, "Content-Type": "application/json"}

    payload = {
        "branchCode": branch_code,
        "branchName": branch_name,
        "supplierCode": supplier_code,
        "items": items,
        "status": "Draft",
        "notes": f"Testing automated indents at {datetime.datetime.today().strftime('%Y-%m-%d')}",
        "deliveryDate": delivery_date
    }

    # Log the payload to ensure it’s in the right format
    print("Payload for Indent Creation:")
    print(json.dumps(payload, indent=4))

    try:
        # Send the request to create the indent
        response = requests.post(INDENT_URL, headers=headers, json=payload)

        if response.status_code == 200:
            print(f"✅ Indent created successfully for Supplier {supplier_code}")
        else:
            print(f"❌ Failed to create indent for Supplier {supplier_code}: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Request error for Supplier {supplier_code}: {e}")

# Process and Create Indents
def process_and_create_indents(order_data):
    # Group the data by supplier code and delivery date
    grouped_data = defaultdict(lambda: {"items": [], "deliveryDate": "", "branchCode": "", "branchName": ""})

    for store_entry in order_data:
        store_id, store_orders = list(store_entry.items())[0]  # Extract store details
        branch_code = store_orders.get("BRANCH CODE", "")
        branch_name = store_orders.get("BRANCH NAME", "")
        delivery_date = store_orders.get("DELIVERY DATE", "")

        if "data" in store_orders:
            for item in store_orders["data"]:
                supplier_code = item.get("SUPPLIER CODE", "")
                sku_code = item.get("SUPPLIER SKU", "")
                item_name = item.get("ITEM NAME", "")
                measuring_unit = item.get("MEASURING UNIT", "")
                quantity = item.get("QUANTITY", 0)

                if not (supplier_code and sku_code and item_name and delivery_date):
                    print(f"⚠️ Skipping item due to missing data: {item}")
                    continue  # Skip if any required field is missing

                # Group the items by supplier
                grouped_data[supplier_code]["items"].append({
                    "skuCode": sku_code,
                    "itemName": item_name,
                    "measuringUnit": measuring_unit,
                    "quantity": quantity
                })

                # Ensure same branch and delivery date for all items from the same supplier
                grouped_data[supplier_code]["branchCode"] = branch_code
                grouped_data[supplier_code]["branchName"] = branch_name
                grouped_data[supplier_code]["deliveryDate"] = delivery_date

    # Now send one indent request per supplier
    for supplier_code, data in grouped_data.items():
        create_indent(data["branchCode"], data["branchName"], supplier_code, data["items"], data["deliveryDate"])

# Main Execution
def main():
    # Assuming 'order_data' is already loaded from a previous process (e.g., Nymblup fetch)
    order_data_file = f"Nymbl Order Data/order_data_{datetime.datetime.today().strftime('%Y-%m-%d')}.json"
    try:
        with open(order_data_file, 'r') as f:
            order_data = json.load(f)
        print(f"✅ Order data loaded from '{order_data_file}'")

        # Process and create indents
        process_and_create_indents(order_data)

    except FileNotFoundError:
        print(f"❌ Error: Order data file '{order_data_file}' not found!")
    except json.JSONDecodeError:
        print(f"❌ Error: Failed to parse JSON file '{order_data_file}'!")

if __name__ == "__main__":
    main()
