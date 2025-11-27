"""
Load CSV Data to FalkorDB
==========================

Script to read CSV files and load them into FalkorDB graph.

Usage:
    python 1_load_to_falkordb.py
"""

import csv
import os
from falkordb import FalkorDB

# Settings
GRAPH_NAME = 'EnergyGraph'
CSV_DIR = 'data/csv'

def load_data_to_falkordb():
    """Load CSV data into FalkorDB."""
    
    print("=" * 60)
    print("FalkorDB Data Loading")
    print("=" * 60)
    
    # Connect to FalkorDB
    print("\n🔌 Connecting to FalkorDB...")
    try:
        db = FalkorDB(host='localhost', port=6379)
        g = db.select_graph(GRAPH_NAME)
        print(f"✅ Connected to graph '{GRAPH_NAME}'")
    except Exception as e:
        print(f"❌ Failed to connect to FalkorDB: {e}")
        print("\n💡 Check if FalkorDB is running:")
        print("   docker ps | grep falkordb")
        return
    
    # Confirm deletion of existing graph
    print(f"\n⚠️  Existing data in '{GRAPH_NAME}' will be deleted and reloaded.")
    confirm = input("Continue? (y/N): ").strip().lower()
    if confirm != 'y':
        print("Cancelled.")
        return
    
    # Delete graph
    try:
        g = db.select_graph(GRAPH_NAME)
        g.delete()
        print("✅ Existing data deleted")
    except Exception as e:
        # Error may occur if graph does not exist (ignore)
        # print(f"⚠️  Error deleting existing data (ignored): {e}")
        pass
    
    # Select graph again (create)
    g = db.select_graph(GRAPH_NAME)
    
    # 1. Load Companies
    print("\n🏢 Loading Companies...")
    companies_path = os.path.join(CSV_DIR, 'companies.csv')
    
    try:
        with open(companies_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            companies = list(reader)
            
        for i, row in enumerate(companies, 1):
            # Escape single quotes
            name = row['name'].replace("'", "\\'")
            country = row['country'].replace("'", "\\'")
            comp_type = row.get('type', 'Unknown').replace("'", "\\'")
            
            query = f"CREATE (:Company {{name: '{name}', country: '{country}', type: '{comp_type}'}})"
            g.query(query)
            
            if i % 20 == 0:
                print(f"   Processing {i}/{len(companies)}...", end="\r")
        
        print(f"   ✅ {len(companies)} companies loaded")
        
    except FileNotFoundError:
        print(f"   ❌ File not found: {companies_path}")
        return
    except Exception as e:
        print(f"   ❌ Failed to load Companies: {e}")
        return
    
    # 2. Load Technologies
    print("\n🔋 Loading Technologies...")
    technologies_path = os.path.join(CSV_DIR, 'technologies.csv')
    
    try:
        with open(technologies_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            technologies = list(reader)
            
        for i, row in enumerate(technologies, 1):
            name = row['name'].replace("'", "\\'")
            category = row['category'].replace("'", "\\'")
            
            query = f"CREATE (:Technology {{name: '{name}', category: '{category}'}})"
            g.query(query)
            
            if i % 100 == 0:
                print(f"   Processing {i}/{len(technologies)}...", end="\r")
        
        print(f"   ✅ {len(technologies)} technologies loaded")
        
    except FileNotFoundError:
        print(f"   ❌ File not found: {technologies_path}")
        return
    except Exception as e:
        print(f"   ❌ Failed to load Technologies: {e}")
        return
    
    # 3. Load Relations
    print("\n🔗 Loading Relations...")
    relations_path = os.path.join(CSV_DIR, 'relations.csv')
    
    try:
        with open(relations_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            relations = list(reader)
        
        for i, row in enumerate(relations, 1):
            start_id = row['START_ID'].replace("'", "\\'")
            end_id = row['END_ID'].replace("'", "\\'")
            rel_type = row['TYPE'].upper() # Unify relation types to uppercase
            
            # Create relation by matching name regardless of node label
            query = f"""
            MATCH (a {{name: '{start_id}'}}), (b {{name: '{end_id}'}})
            CREATE (a)-[:{rel_type}]->(b)
            """
            g.query(query)
            
            if i % 100 == 0:
                print(f"   Processing {i}/{len(relations)}...", end="\r")
        
        print(f"   ✅ {len(relations)} relations loaded")
        
    except FileNotFoundError:
        print(f"   ❌ File not found: {relations_path}")
        return
    except Exception as e:
        print(f"   ❌ Failed to load Relations: {e}")
        return
    
    # Complete
    print("\n" + "=" * 60)
    print("✅ Data loading complete!")
    print(f"📊 Graph '{GRAPH_NAME}':")
    print(f"   - Companies: {len(companies)}")
    print(f"   - Technologies: {len(technologies)}")
    print(f"   - Relations: {len(relations)}")
    print("=" * 60)
    print("\n💡 Next step:")
    print("   python 2_enrich_graph_data.py --full")
    print("=" * 60)


if __name__ == "__main__":
    load_data_to_falkordb()
