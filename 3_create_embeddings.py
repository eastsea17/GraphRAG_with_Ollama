"""
Step 4: Create Embeddings (Data Only)
=====================================
This script generates and stores vector embeddings for nodes (Company, Technology) in FalkorDB.

* Features:
- Does not create DB internal indexes, avoiding 'Invalid arguments' errors.
- Purely populates data (embedding attribute).
- The 'Guaranteed RAG' script will read this data for search.
"""

import time
import requests
from falkordb import FalkorDB

# ==========================================
# ⚙️ Settings (Adjust to your environment)
# ==========================================
GRAPH_NAME = 'EnergyGraph'
OLLAMA_URL = 'http://localhost:11434'
EMBED_MODEL = 'nomic-embed-text:latest'  # Installed embedding model name

class EmbeddingCreator:
    def __init__(self):
        print(f"🔌 Connecting to FalkorDB... (Graph: {GRAPH_NAME})")
        try:
            self.db = FalkorDB(host='localhost', port=6379)
            self.graph = self.db.select_graph(GRAPH_NAME)
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            exit()

    def get_nodes_without_embedding(self):
        """Retrieve nodes without embeddings"""
        query = """
        MATCH (n)
        WHERE n.embedding IS NULL
        RETURN ID(n), n.name, n.description, n.category, n.country, labels(n)
        """
        return self.graph.query(query).result_set

    def generate_embedding(self, text):
        """Convert text to vector using Ollama API"""
        try:
            res = requests.post(
                f"{OLLAMA_URL}/api/embeddings",
                json={"model": EMBED_MODEL, "prompt": text}
            )
            if res.status_code == 200:
                return res.json()['embedding']
            else:
                print(f"  ⚠️ API Error: {res.text}")
                return None
        except Exception as e:
            print(f"  ❌ Communication Error: {e}")
            return None

    def run(self):
        print("\n1. Checking target nodes...")
        nodes = self.get_nodes_without_embedding()
        
        if not nodes:
            print("✅ All nodes already have embedding data. (No work needed)")
            self.verify_status()
            return

        total = len(nodes)
        print(f"🚀 Starting embedding generation for {total} nodes.\n")

        success_count = 0
        
        for i, row in enumerate(nodes, 1):
            node_id = row[0]
            name = row[1]
            desc = row[2]
            # Use category or country info if available
            extra = row[3] if row[3] else (row[4] if row[4] else "") 
            label = row[5][0] if row[5] else "Unknown"

            # Determine text to embed (use name + info if description is missing)
            text_to_embed = desc if desc else f"{name} is a {label} related to {extra}"
            
            # Print progress
            print(f"  [{i}/{total}] Processing: {name[:30]}...", end="\r")

            # 1. Generate embedding
            vec = self.generate_embedding(text_to_embed)
            
            if vec:
                # 2. Update DB (Use Params for safe storage)
                # No index created, so no errors expected
                update_query = f"MATCH (n) WHERE ID(n) = {node_id} SET n.embedding = $vec"
                self.graph.query(update_query, {'vec': vec})
                success_count += 1
            
            # Short wait to control API load
            # time.sleep(0.01) 

        print(f"\n\n✨ Complete! Successfully updated {success_count}/{total} nodes.")
        self.verify_status()

    def verify_status(self):
        """Check final status"""
        print("\n📊 Data Status Check:")
        try:
            total = self.graph.query("MATCH (n) RETURN count(n)").result_set[0][0]
            embedded = self.graph.query("MATCH (n) WHERE n.embedding IS NOT NULL RETURN count(n)").result_set[0][0]
            print(f"   - Total nodes: {total}")
            print(f"   - Nodes with embeddings: {embedded}")
            
            if total == embedded and total > 0:
                print("   ✅ Data ready! You can now run the search script.")
            elif total > 0:
                print(f"   ⚠️ Some nodes ({total-embedded}) are missing embeddings. Try running the script again.")
        except Exception as e:
            print(f"   ❌ Check failed: {e}")

if __name__ == "__main__":
    creator = EmbeddingCreator()
    creator.run()