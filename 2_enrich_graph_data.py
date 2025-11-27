"""
FalkorDB Graph Data Enrichment Script (Fixed)
=============================================
1. Added --force option (overwrite existing data)
2. Detects and regenerates empty strings ("")
3. Increased LLM response length (num_predict) to prevent truncation
4. Real-time terminal summary output
"""

# ========================================
# 🤖 LLM Model Settings
# ========================================
#LLM_MODEL = 'qwen2.5:14b'
#LLM_MODEL = 'qwen3:8b'
LLM_MODEL = 'deepseek-r1:8b'

import argparse
import time
import requests
from typing import List, Dict
from falkordb import FalkorDB

class GraphEnricher:
    def __init__(self, graph_name: str = 'EnergyGraph', ollama_url: str = 'http://localhost:11434'):
        self.db = FalkorDB(host='localhost', port=6379)
        self.graph = self.db.select_graph(graph_name)
        self.ollama_url = ollama_url
        self.model = LLM_MODEL
        self.processed_count = 0
        
        # Check Ollama connection
        try:
            response = requests.get(f"{ollama_url}/api/tags")
            if response.status_code != 200:
                raise ConnectionError(f"Ollama unreachable: {ollama_url}")
        except Exception as e:
            raise ConnectionError(f"Failed to connect to Ollama server: {e}")
        
    def get_nodes_to_process(self, label: str, limit: int = None, force: bool = False) -> List[Dict]:
        """
        Select nodes to process.
        - force=True: Fetch all nodes.
        - force=False: Fetch nodes where description is NULL or empty string ('').
        """
        if force:
            # Force mode: Fetch all nodes unconditionally
            query = f"""
            MATCH (n:{label})
            RETURN ID(n) as id, n.name as name, n.{('category' if label == 'Technology' else 'country')} as extra
            """
        else:
            # Normal mode: Fetch only missing or empty descriptions
            query = f"""
            MATCH (n:{label})
            WHERE n.description IS NULL OR n.description = ''
            RETURN ID(n) as id, n.name as name, n.{('category' if label == 'Technology' else 'country')} as extra
            """
        
        if limit:
            query += f" LIMIT {limit}"
        
        result = self.graph.query(query)
        nodes = []
        for row in result.result_set:
            nodes.append({'id': row[0], 'name': row[1], 'extra': row[2]})
        return nodes
    
    def generate_description(self, name: str, extra: str, node_type: str) -> str:
        if node_type == 'technology':
            prompt = f"""You are a battery technology expert. Provide a concise description:
Technology Name: {name}, Category: {extra}.
Explain what it is, its advantages, and applications.
Answer in plain text without markdown formatting. Keep it under 100 words."""
        else:
            prompt = f"""You are a battery industry analyst. Provide a concise description:
Company Name: {name}, Country: {extra}.
Explain their role, key products, and market position.
Answer in plain text without markdown formatting. Keep it under 100 words."""
        
        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "num_predict": 300  # [Modified] Increased length to prevent truncation
                    }
                }
            )
            if response.status_code != 200: return ""
            return response.json()['response'].strip()
        except Exception:
            return ""

    def update_node_description(self, node_id: int, description: str):
        # Escape single/double quotes
        escaped_desc = description.replace("'", "\\'").replace('"', '\\"')
        
        # Do not save if description is too short or empty (retry later)
        if len(escaped_desc) < 5:
            return False

        query = f"MATCH (n) WHERE ID(n) = {node_id} SET n.description = '{escaped_desc}'"
        self.graph.query(query)
        self.processed_count += 1
        return True
    
    def process_nodes(self, label: str, limit: int = None, force: bool = False):
        print(f"\n🚀 Starting {label} node processing (Force={force})...")
        nodes = self.get_nodes_to_process(label, limit, force)
        total = len(nodes)
        
        if total == 0:
            print(f"  ✅ No {label} nodes to update.")
            return
        
        print(f"  📊 Target: {total} nodes")
        
        for i, node in enumerate(nodes, 1):
            name = node['name']
            print(f"  [{i}/{total}] {name}...", end=" ", flush=True)
            
            # Generate description
            description = self.generate_description(name, node['extra'], label.lower())
            
            # Update DB
            success = self.update_node_description(node['id'], description)
            
            if success:
                # Print summary
                clean_desc = description.replace('\n', ' ')
                snippet = " ".join(clean_desc.split()[:8])
                print(f"✓ -> {snippet}...")
            else:
                print("❌ Generation failed (empty response)")
            
    def run(self, limit: int = None, force: bool = False):
        print("=" * 60)
        print("FalkorDB Graph Data Enrichment (Fixed)")
        print("=" * 60)
        
        start_time = time.time()
        self.process_nodes('Technology', limit, force)
        self.process_nodes('Company', limit, force)
        elapsed = time.time() - start_time
        
        print("=" * 60)
        print(f"✅ All done! ({self.processed_count} updated, {elapsed:.1f}s)")
        print("=" * 60)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--graph', default='EnergyGraph')
    parser.add_argument('--sample', type=int)
    parser.add_argument('--full', action='store_true')
    parser.add_argument('--force', action='store_true', help='Force overwrite existing descriptions')
    parser.add_argument('--ollama-url', default='http://localhost:11434')
    args = parser.parse_args()
    
    if not args.sample and not args.full:
        print("❌ Usage: python 2_enrich_graph_data.py --full --force")
        return
    
    enricher = GraphEnricher(graph_name=args.graph, ollama_url=args.ollama_url)
    enricher.run(limit=args.sample if args.sample else None, force=args.force)

if __name__ == "__main__":
    main()