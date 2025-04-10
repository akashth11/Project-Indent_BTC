import json
import datetime
import requests
import jwt  # PyJWT for JWT token generation
from collections import defaultdict
from IMPORT_nymblup import get_branch_codes, get_auth_token, fetch_orders  # Importing functions
from inventorysupplieritemlist import fetch_all_records  # Importing function
import os  # Import os module

# API Endpoint for Indent Creation in Rista
INDENT_URL = "https://api.ristaapps.com/v1/inventory/indent"

# Rista API Credentials
API_KEY = "91bfe158-b7c6-4492-829d-d66fad71fcce"
SECRET_KEY = "8Wh8lSoJIzJ20aQlkk5ZovoXTOKMRKS1DuExsF5rk48"

# Generate JWT Token for Rista API
def generate_jwt_token():
    token_creation_time = int(datetime.datetime.now(datetime.timezone.utc).timestamp())
    payload = {"iss": API_KEY, "iat": token_creation_time}
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    return token

# Create Indent in Rista
def create_indent(branch_code, branch_name, supplier_code, items, delivery_date):
    api_token = generate_jwt_token()
    headers = {"x-api-key": API_KEY, "x-api-token": api_token, "Content-Type": "application/json"}

    payload = {
        "branchCode": branch_code,
        "branchName": branch_name,
        "supplierCode": supplier_code,
        "items": items,
        "status": "Draft",
        "notes": "Auto-generated indent",
        "deliveryDate": delivery_date
    }

    try:
        response = requests.post(INDENT_URL, headers=headers, json=payload)
        if response.status_code == 200:
            print(f"✅ Indent created successfully for Supplier {supplier_code}")
        else:
            print(f"❌ Failed to create indent for Supplier {supplier_code}: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Request error for Supplier {supplier_code}: {e}")

# Process and Create Indents
def process_and_create_indents(order_data, supplier_items):
    grouped_data = defaultdict(lambda: {"items": [], "deliveryDate": "", "branchCode": "", "branchName": ""})

    # Convert supplier_items list into a dictionary using skuCode as the key
    sku_map = {item["skuCode"]: item for item in supplier_items} if isinstance(supplier_items, list) else {}

    for store_entry in order_data:
        store_id, store_orders = list(store_entry.items())[0]  # Extract store details
        delivery_date = store_orders.get("DELIVERY DATE", "")  # Extract delivery date at store level
        branch_code = store_orders.get("BRANCH CODE", "")  # Assuming branch code is available
        branch_name = store_orders.get("BRANCH NAME", "")  # Assuming branch name is available

        if "data" in store_orders:
            for item in store_orders["data"]:
                buyer_code = item.get("BUYER STORE CODE", "")
                supplier_code = item.get("SUPPLIER CODE", "")
                sku_code = item.get("SUPPLIER SKU", "")

                if not (buyer_code and supplier_code and sku_code and delivery_date):
                    print(f"⚠️ Skipping item due to missing data: {item}")
                    continue  # Skip if any required field is missing

                # Fetch supplier item details
                supplier_item = sku_map.get(sku_code, {})

                # Group items by supplier
                grouped_data[supplier_code]["items"].append({
                    "skuCode": sku_code,
                    "itemName": supplier_item.get("name", ""),
                    "measuringUnit": supplier_item.get("measuringUnit", ""),
                    "quantity": item.get("QUANTITY", 0)
                })
                grouped_data[supplier_code]["deliveryDate"] = delivery_date  # Ensure same delivery date for all
                grouped_data[supplier_code]["branchCode"] = branch_code
                grouped_data[supplier_code]["branchName"] = branch_name

    # Now send one indent request per supplier
    for supplier_code, data in grouped_data.items():
        create_indent(data["branchCode"], data["branchName"], supplier_code, data["items"], data["deliveryDate"])

# Main Execution
def main():
    # Fetch branch codes
    store_ids = get_branch_codes()
    if store_ids:
        token = get_auth_token()
        if token:
            # Fetch order data directly (always fetch fresh data)
            fetch_orders(token, store_ids)  # Fetch the order data using the token and store IDs
            
            # Load the order data immediately after fetching it
            order_data_file = f"Nymbl Order Data/order_data_{datetime.datetime.today().strftime('%Y-%m-%d')}.json"
            try:
                with open(order_data_file, 'r') as f:
                    order_data = json.load(f)
                print(f"✅ Order data loaded from '{order_data_file}'")
            except json.JSONDecodeError:
                print(f"❌ Error: Failed to parse JSON file '{order_data_file}'!")
                return

            # Fetch supplier items
            supplier_items = fetch_all_records()

            # Process and create indents
            process_and_create_indents(order_data, supplier_items)

        else:
            print("❌ Authentication failed. Cannot fetch orders.")
    else:
        print("❌ No store IDs found. Cannot fetch orders.")

if __name__ == "__main__":
    main()
