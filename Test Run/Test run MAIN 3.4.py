import json
import csv
from collections import defaultdict
from datetime import datetime
import subprocess
import os
import sys

# Run other useful imports
subprocess.run(["python", "IMPORT_nymblup.py"], check=True)
subprocess.run(["python", "Supplier_Details.py"], check=True)
subprocess.run(["python", "inventorysupplieritemlist.py"], check=True)

# Get the current date in YYYY-MM-DD format
current_date = datetime.now().strftime("%Y-%m-%d")

# Define folders
order_data_filename = f"Nymbl Order Data/order_data_{current_date}.json"
indent_folder = "Indent Payload Log"
indent_csv_folder = "Indent CSV"

# Ensure folders exist
os.makedirs(indent_folder, exist_ok=True)
os.makedirs(indent_csv_folder, exist_ok=True)

# Load Order Data
with open(order_data_filename, "r", encoding="utf-8") as file:
    order_data = json.load(file)

# Load Supplier Items Data
with open("supplier_items.json", "r", encoding="utf-8") as file:
    supplier_items = json.load(file)

# Load Supplier Mapping Data
with open("transformed_suppliers.json", "r", encoding="utf-8") as file:
    supplier_mapping = json.load(file)

# Convert supplier_items.json into a dictionary for fast lookup using both SKU and Supplier Code
supplier_lookup = {(str(item["skuCode"]), item["supplierCode"]): item for item in supplier_items}

# Convert supplier_mapping.json into a dictionary for supplier mapping based on ConcatSUPPLIER, filtering only active suppliers
supplier_code_mapping = {item["ConcatSUPPLIER"]: item["Supplier Code"] for item in supplier_mapping if item["Status"] == "Active"}

# Ensure the data is a list and extract all buyer store orders
buyer_supplier_orders = defaultdict(lambda: defaultdict(list))

for buyer_data in order_data:
    for branch_code, branch_info in buyer_data.items():
        if "data" not in branch_info:
            continue  # Skip if no order data is present

        for order in branch_info["data"]:
            concat_supplier_key = order["ConcatNMBLPY"]
            mapped_supplier_code = supplier_code_mapping.get(concat_supplier_key, None)  # Map supplier code based on ConcatSUPPLIER
            if mapped_supplier_code:  # Only process if supplier is active
                buyer_supplier_orders[branch_code][mapped_supplier_code].append(order)

# Generate Indent Payloads in required JSON format
indent_payloads = []
csv_data = []

for branch_code, suppliers in buyer_supplier_orders.items():
    for supplier_code, items in suppliers.items():
        indent_payload = {
            "branchCode": branch_code,
            "branchName": items[0]["BRANCH NAME"],
            "supplierCode": supplier_code,
            "items": [],
            "status": "Draft",
            "sourceInfo": {"sourceIndentOrder": "Automated Order"},
            "deliveryDate": items[0]["DELIVERY DATE"],
            "notes": "Generated by script."
        }

        for item in items:
            sku_code = str(item["SUPPLIER SKU"])  # Ensure it's a string
            lookup_key = (sku_code, supplier_code)  # Match on both SKU and Supplier Code
            item_details = supplier_lookup.get(lookup_key, {})

            item_data = {
                "skuCode": sku_code,
                "itemName": item_details.get("name", item["ITEM NAME"]),
                "measuringUnit": item_details.get("measuringUnit", item["MEASURING UNIT"]),
                "quantity": item["QUANTITY"]
            }

            indent_payload["items"].append(item_data)

            # ✅ **Fix: Append data to csv_data list**
            csv_data.append([
                branch_code,
                items[0]["BRANCH NAME"],
                supplier_code,
                sku_code,
                item_data["itemName"],
                item_data["measuringUnit"],
                item_data["quantity"],
                items[0]["DELIVERY DATE"]
            ])

        indent_payloads.append(indent_payload)

# Save JSON file
json_filename = os.path.join(indent_folder, f"indent_payloads_{current_date}.json")
with open(json_filename, "w", encoding="utf-8") as jsonfile:
    json.dump(indent_payloads, jsonfile, indent=4, ensure_ascii=False)

print(f"\n🎯 JSON file '{json_filename}' generated successfully with {len(indent_payloads)} payloads!")

# Save CSV file
csv_filename = os.path.join(indent_csv_folder, f"indent_payloads_{current_date}.csv")
with open(csv_filename, "w", newline="", encoding="utf-8") as csvfile:
    writer = csv.writer(csvfile)
    # Write headers
    writer.writerow(["Branch Code", "Branch Name", "Supplier Code", "SKU Code", "Item Name", "Measuring Unit", "Quantity", "Delivery Date"])
    # Write data
    writer.writerows(csv_data)

print(f"\n📄 CSV file '{csv_filename}' generated successfully with {len(csv_data)} rows!")
