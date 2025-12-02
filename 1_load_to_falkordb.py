"""
Load Data to FalkorDB
=====================
Dynamically load ALL generated CSV files from the data directory into FalkorDB.
Supports multiple node files and dynamic labeling.

Usage:
    python 1_load_to_falkordb.py
    python 1_load_to_falkordb.py --clear
"""

import os
import sys
import csv
import argparse
import glob
from typing import List, Dict, Any
from falkordb import FalkorDB
import config

def connect_to_falkordb(host=config.FALKORDB_HOST, port=config.FALKORDB_PORT):
    """Connect to FalkorDB instance."""
    try:
        db = FalkorDB(host=host, port=port)
        return db
    except Exception as e:
        print(f"❌ Failed to connect to FalkorDB: {e}")
        sys.exit(1)

def clean_value(value: Any) -> str:
    """Escape special characters for Cypher queries."""
    if value is None:
        return ""
    return str(value).replace("'", "\\'").replace('"', '\\"').strip()

def sanitize_label(label: str) -> str:
    """Convert raw type string to valid Cypher label."""
    if not label:
        return "Entity"
    # Replace spaces and hyphens with underscores, remove other special chars if needed
    return label.strip().replace(" ", "_").replace("-", "_")

def get_node_files(data_dir: str) -> List[str]:
    """Get list of all CSV files representing nodes (excluding edge files)."""
    all_csvs = glob.glob(os.path.join(data_dir, "*.csv"))
    # Exclude files known to contain edges/relations or raw data
    exclude_list = ['edges.csv', 'relations.csv', 'rawdata.csv']
    
    node_files = []
    for f_path in all_csvs:
        filename = os.path.basename(f_path)
        if filename not in exclude_list:
            node_files.append(f_path)
    
    return node_files

def load_nodes(g, data_dir: str):
    """Load all node CSV files found in the directory."""
    print("\n📦 Loading Nodes...")
    
    node_files = get_node_files(data_dir)
    
    if not node_files:
        print(f"   ⚠️  No node CSV files found in {data_dir}")
        return 0

    total_nodes_loaded = 0
    
    for file_path in node_files:
        filename = os.path.basename(file_path)
        print(f"   Processing file: {filename}...")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                
            if not rows:
                print(f"      ⚠️  No data in file")
                continue

            count = 0
            for row in rows:
                # 1. Determine Label
                # Priority 1: 'Type' column in CSV
                # Priority 2: Filename (e.g., 'research_purpose.csv' -> 'Purpose')
                dynamic_type = row.get('Type') or row.get('type')
                
                if dynamic_type:
                    node_label = sanitize_label(dynamic_type)
                else:
                    # Fallback: Extract label from filename
                    # e.g., "research_purpose.csv" -> "Purpose"
                    name_part = filename.replace('.csv', '').replace('research_', '')
                    node_label = sanitize_label(name_part.capitalize())
                
                # 2. Build Properties
                props = []
                
                # Identify ID (Id, id, ID, Label, name)
                # Note: In 0_generate...py, we saved 'Id' and 'Label'.
                node_id = row.get('Id') or row.get('id') or row.get('ID')
                
                if node_id:
                     props.append(f"id: '{clean_value(node_id)}'")
                
                for key, value in row.items():
                    if key and value:
                        clean_val = clean_value(value)
                        clean_key = key.replace(" ", "_")
                        props.append(f"{clean_key}: '{clean_val}'")
                
                props_str = ", ".join(props)
                
                # 3. Execute Query (MERGE to prevent duplicates)
                if node_id:
                    # Indexing hint (optional, execute once ideally)
                    # g.query(f"CREATE INDEX FOR (n:{node_label}) ON (n.id)")
                    
                    query = f"MERGE (n:{node_label} {{id: '{clean_value(node_id)}'}}) SET n += {{{props_str}}}"
                else:
                    query = f"CREATE (:{node_label} {{{props_str}}})"
                
                g.query(query)
                count += 1
                
            print(f"      ✅ Loaded {count} nodes from {filename}")
            total_nodes_loaded += count
            
        except Exception as e:
            print(f"      ❌ Error loading {filename}: {e}")
            
    return total_nodes_loaded

def load_edges(g, data_dir: str):
    """Load relationships from edges.csv or relations.csv."""
    print("\n🔗 Loading Relationships...")
    
    # Check for likely edge filenames
    possible_files = ['edges.csv', 'relations.csv']
    file_path = None
    
    for fname in possible_files:
        path = os.path.join(data_dir, fname)
        if os.path.exists(path):
            file_path = path
            print(f"   Found edge file: {fname}")
            break
            
    if not file_path:
        print(f"   ⚠️  No edge file found (checked: {possible_files}). Skipping edges.")
        return 0
        
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
        if not rows:
            print("   ⚠️  No relationships found")
            return 0
            
        count = 0
        skipped = 0
        
        print(f"   Processing {len(rows)} relationships...")
        
        for i, row in enumerate(rows):
            # Support multiple header formats
            # 0_generate...py uses: Source, Target, Type
            # Standard GraphRAG uses: START_ID, END_ID, TYPE
            start_id = clean_value(row.get('Source') or row.get('START_ID'))
            end_id = clean_value(row.get('Target') or row.get('END_ID'))
            rel_type = row.get('Type') or row.get('TYPE') or 'RELATED_TO'
            
            # Additional properties (e.g., Weight)
            weight = row.get('Weight')
            
            # Sanitize relationship type
            rel_type = sanitize_label(rel_type).upper()
            
            if not (start_id and end_id):
                skipped += 1
                continue
            
            # Universal Match based on ID
            # Assuming nodes are already loaded with 'id' property
            query = f"""
            MATCH (a), (b)
            WHERE a.id = '{start_id}' AND b.id = '{end_id}'
            MERGE (a)-[r:{rel_type}]->(b)
            """
            
            # Add weight if exists
            if weight:
                query += f" SET r.weight = {weight}"

            g.query(query)
            count += 1
            
            if i > 0 and i % 100 == 0:
                print(f"      Progress: {i}/{len(rows)}...", end="\r")
                
        print(f"   ✅ Loaded {count} relationships (Skipped {skipped})")
        return count
        
    except Exception as e:
        print(f"   ❌ Error loading edges: {e}")
        return 0

def main():
    parser = argparse.ArgumentParser(description='Load GraphRAG data into FalkorDB')
    parser.add_argument('--graph', type=str, default=config.GRAPH_NAME,
                       help=f'Graph name (default: {config.GRAPH_NAME})')
    parser.add_argument('--clear', action='store_true',
                       help='Clear graph before loading')
    args = parser.parse_args()
    
    print("=" * 60)
    print(f"🚀 Loading Data to FalkorDB: {args.graph}")
    print("=" * 60)
    
    # 1. Connect
    db = connect_to_falkordb()
    g = db.select_graph(args.graph)
    
    # 2. Clear if requested
    if args.clear:
        print("\n🧹 Clearing existing graph data...")
        try:
            g.query("MATCH (n) DETACH DELETE n")
            print("   ✅ Graph cleared")
        except Exception as e:
            print(f"   ⚠️  Could not clear graph (might be empty): {e}")
    
    # 3. Load Nodes (from all CSVs in directory)
    total_nodes = load_nodes(g, config.CSV_DIR)
    
    # 4. Load Edges
    total_edges = load_edges(g, config.CSV_DIR)
    
    print("\n" + "=" * 60)
    print("✅ Loading Complete!")
    print(f"   - Nodes: {total_nodes}")
    print(f"   - Edges: {total_edges}")
    print("=" * 60)
    print(f"\nNext Step: Enrich graph with descriptions (if needed)")
    print(f"python 2_enrich_graph_data.py --graph {args.graph} --full")

if __name__ == "__main__":
    main()