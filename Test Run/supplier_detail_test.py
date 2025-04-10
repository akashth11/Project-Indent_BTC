import requests
import json
import jwt
import time
import csv

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
    
    # API Endpoint
    url = "https://api.ristaapps.com/v1/inventory/supplier/list?supplierType=Internal"
    
    # Headers
    headers = {
        "x-api-key": api_key,
        "x-api-token": jwt_token
    }
    
    # Fetch data from API
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json().get("data", [])
    else:
        print(f"Error: {response.status_code}, {response.text}")
        exit()
    
    # Supplier Status Mapping
    active_suppliers = {
        "BK-003", "BK-004", "BK001BKI", "BK001SAB", "BK001SN", "BK001tst",
        "BK002BKI", "BK002BTC", "BK002SAB", "BK002SN", "BK003SN", "BKGT-001",
        "BKGT-002", "BLR2HYD", "PD-001", "RO-002", "RO-002GT", "RO-003",
        "RO-004", "RO-004GT", "RTOWH-01", "RTOWH-02", "RTOWH-03", "Test1234",
        "UV2CHD", "UV2KK", "WH-001", "WH-002", "WH-002V", "WH-003", "WH-004",
        "WH-005", "WH-006", "WH-007", "WH-009", "WH-010", "WH-010T", "WH001E",
        "WH001GT", "WH001TST", "WH003GT", "WH003KGT", "WH007A", "WH007BTC",
        "WH007GT", "WH007K", "WH007SAB", "WH008BTC", "WH008SAB", "WH009GT"
    }
    
    # Supplier Type Mapping
    supplier_type_mapping = {
        "BK-003": "Base Kitchen",
        "BK-004": "Base Kitchen",
        "BK-001": "Base Kitchen",
        "BK-002": "Base Kitchen",
        "WH-003": "Bakery",
        "GTK-001": "Got Tea Kitchen",
        "PD-001": "Production",
        "PD-002": "Production",
        "PD-003": "Production",
        "RO-002": "Roastery",
        "RO-003": "Roastery",
        "RO-004": "Roastery",
        "RTOWH-01": "return",
        "RTOWH-02": "return",
        "RTOWH-03": "return",
        "WH-007": "3 PL",
        "WH-001": "Bakery",
        "WH-002": "Bakery",
        "WH-004": "Bakery",
        "WH-005": "Bakery",
        "WH-006": "Bakery",
        "WH-009": "3 PL",
        "WH-008": "3 PL",
        "BKGT-001": "Got Tea Kitchen",
        "BKGT-002": "Got Tea Kitchen",
        "WH-010": "CPU"
    }
    
    # Process data
    transformed_data = []
    for supplier in data:
        supplier_code = supplier.get("supplierCode")
        supplier_name = supplier.get("supplierName", "")
        supplier_type = supplier.get("supplierType", "")
        supplier_store_code = supplier.get("sourceStoreCode", "")
        status = "Active" if supplier_code in active_suppliers else "Inactive"
        managing_branch = supplier_store_code 
        buyer_store_codes = supplier.get("buyerStoreCodes", [])
        supplier_category = supplier_type_mapping.get(supplier_store_code, "Unknown")
        
        for index, buyer_store in enumerate(buyer_store_codes, start=1):
            transformed_data.append({
                "Supplier Code": supplier_code,
                "Supplier Name": supplier_name,
                "Supplier Type": supplier_type,
                "Status": status,
                "Managing Branch": managing_branch,
                "Attribute": f"Buyer Branches.{index}",
                "Value": buyer_store,
                "Branch Code": buyer_store,
                "ConcatSUPPLIER": f"{buyer_store}{supplier_store_code}",
                "Type": supplier_category
            })
    
    # Save to JSON file
    output_file = "transformed_suppliers.json"
    with open(output_file, "w") as f:
        json.dump(transformed_data, f, indent=4)
    
    # Save to CSV file
    csv_file = "transformed_suppliers.csv"
    fieldnames = ["Supplier Code", "Supplier Name", "Supplier Type", "Status", "Managing Branch", "Attribute", "Value", "Branch Code", "ConcatSUPPLIER", "Type"]
    with open(csv_file, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(transformed_data)
    
    print(f"Transformed data saved to {output_file} and {csv_file}")

# Execute function
fetch_all_records()