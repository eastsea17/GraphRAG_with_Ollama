"""
FalkorDB Export Script
======================
Retrieves graph data (nodes) stored in FalkorDB and exports it to CSV files,
including the generated descriptions.

Output:
  - data/enriched_companies.csv
  - data/enriched_technologies.csv
"""

import csv
import os
from falkordb import FalkorDB

# Settings
GRAPH_NAME = 'EnergyGraph'
OUTPUT_DIR = 'data'

def export_to_csv():
    print("=" * 60)
    print("📂 Export Enriched Data from FalkorDB")
    print("=" * 60)

    # 1. Connect to DB
    try:
        db = FalkorDB(host='localhost', port=6379)
        g = db.select_graph(GRAPH_NAME)
        print(f"🔌 Connected to graph '{GRAPH_NAME}'")
    except Exception as e:
        print(f"❌ DB Connection Failed: {e}")
        return

    # 2. Check and create output directory
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        print(f"📁 Created directory '{OUTPUT_DIR}'")

    # ---------------------------------------------------------
    # 3. Export Company Data
    # ---------------------------------------------------------
    print("\n🏢 Extracting Company data...", end=" ")
    
    # Query required attributes (handle missing description as empty string)
    query_company = """
    MATCH (n:Company)
    RETURN n.name, n.country, n.type, n.description
    """
    res_company = g.query(query_company)
    
    csv_file_comp = os.path.join(OUTPUT_DIR, 'enriched_companies.csv')
    
    try:
        with open(csv_file_comp, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            # Write header
            writer.writerow(['name', 'country', 'type', 'description'])
            
            count = 0
            for row in res_company.result_set:
                # Handle None data (convert to empty string)
                clean_row = [str(item) if item is not None else "" for item in row]
                writer.writerow(clean_row)
                count += 1
                
        print(f"✅ Done")
        print(f"   -> Saved to: {csv_file_comp}")
        print(f"   -> Count: {count}")
        
    except Exception as e:
        print(f"\n❌ Failed to save Company file: {e}")

    # ---------------------------------------------------------
    # 4. Export Technology Data
    # ---------------------------------------------------------
    print("\n🔋 Extracting Technology data...", end=" ")
    
    query_tech = """
    MATCH (n:Technology)
    RETURN n.name, n.category, n.description
    """
    res_tech = g.query(query_tech)
    
    csv_file_tech = os.path.join(OUTPUT_DIR, 'enriched_technologies.csv')
    
    try:
        with open(csv_file_tech, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            # Write header
            writer.writerow(['name', 'category', 'description'])
            
            count = 0
            for row in res_tech.result_set:
                clean_row = [str(item) if item is not None else "" for item in row]
                writer.writerow(clean_row)
                count += 1
                
        print(f"✅ Done")
        print(f"   -> Saved to: {csv_file_tech}")
        print(f"   -> Count: {count}")
        
    except Exception as e:
        print(f"\n❌ Failed to save Technology file: {e}")

    print("\n" + "=" * 60)
    print("✨ All export tasks completed.")
    print("=" * 60)

if __name__ == "__main__":
    export_to_csv()