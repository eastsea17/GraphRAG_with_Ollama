"""
FalkorDB Graph Data Enrichment
==============================
Dynamically enriches nodes with descriptions using LLM.
Supports any graph schema by automatically detecting node types and attributes.

Usage:
    python 2_enrich_graph_data.py --full
    python 2_enrich_graph_data.py --sample 10
    python 2_enrich_graph_data.py --force
"""

import argparse
import time
import json
import os
import requests
from typing import List, Dict, Any
from falkordb import FalkorDB
import config

class GraphEnricher:
    def __init__(self, graph_name: str = config.GRAPH_NAME, ollama_url: str = config.OLLAMA_URL):
        self.db = FalkorDB(host=config.FALKORDB_HOST, port=config.FALKORDB_PORT)
        self.graph = self.db.select_graph(graph_name)
        self.ollama_url = ollama_url
        self.model = config.LLM_MODEL
        self.processed_count = 0
        self.schema = self.load_schema()
        
        # Check Ollama connection
        try:
            response = requests.get(f"{ollama_url}/api/tags")
            if response.status_code != 200:
                raise ConnectionError(f"Ollama unreachable: {ollama_url}")
        except Exception as e:
            raise ConnectionError(f"Failed to connect to Ollama server: {e}")

    def load_schema(self) -> Dict:
        """Load schema definition from JSON if available."""
        schema_path = config.SCHEMA_OUTPUT
        if os.path.exists(schema_path):
            try:
                with open(schema_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return {}
        
    def get_all_labels(self) -> List[str]:
        """Get all node labels in the graph."""
        query = "MATCH (n) RETURN distinct labels(n)"
        result = self.graph.query(query)
        labels = set()
        for row in result.result_set:
            if row[0]:
                labels.add(row[0][0])
        return list(labels)

    def get_nodes_to_process(self, label: str, limit: int = None, force: bool = False) -> List[Dict]:
        """Select nodes to process."""
        if force:
            query = f"MATCH (n:{label}) RETURN ID(n), properties(n)"
        else:
            query = f"MATCH (n:{label}) WHERE n.description IS NULL OR n.description = '' RETURN ID(n), properties(n)"
        
        if limit:
            query += f" LIMIT {limit}"
        
        result = self.graph.query(query)
        nodes = []
        for row in result.result_set:
            nodes.append({'id': row[0], 'props': row[1]})
        return nodes
    
    def generate_description(self, props: Dict, label: str) -> str:
        """Generate description using LLM based on node properties."""
        # Construct context from properties
        context_parts = []
        for k, v in props.items():
            if k != 'description' and k != 'embedding' and v:
                context_parts.append(f"{k}: {v}")
        context_str = ", ".join(context_parts)
        
        # Get domain from schema if available
        domain = "general knowledge"
        if self.schema and 'domain' in self.schema:
            domain = self.schema['domain']
            
        prompt = f"""Context: {domain}
Entity Type: {label}
Attributes: {context_str}

Task: Write a concise, informative description of this {label}.
- Focus on what it is and its significance in the context of {domain}.
- Do not mention "this entity" or "the data".
- Keep it under 3 sentences.
- Output ONLY the description text."""
        
        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "num_predict": 150
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
        
        if len(escaped_desc) < 5:
            return False

        query = f"MATCH (n) WHERE ID(n) = {node_id} SET n.description = '{escaped_desc}'"
        self.graph.query(query)
        self.processed_count += 1
        return True
    
    def process_label(self, label: str, limit: int = None, force: bool = False):
        print(f"\n🚀 Processing {label} nodes (Force={force})...")
        nodes = self.get_nodes_to_process(label, limit, force)
        total = len(nodes)
        
        if total == 0:
            print(f"  ✅ No {label} nodes to update.")
            return
        
        print(f"  📊 Target: {total} nodes")
        
        for i, node in enumerate(nodes, 1):
            props = node['props']
            # Find a display name
            name = props.get('name') or props.get('title') or props.get('id') or str(props.values())[:20]
            
            print(f"  [{i}/{total}] {name[:30]}...", end=" ", flush=True)
            
            # Generate description
            description = self.generate_description(props, label)
            
            # Update DB
            success = self.update_node_description(node['id'], description)
            
            if success:
                snippet = description[:50].replace('\n', ' ')
                print(f"✓ -> {snippet}...")
            else:
                print("❌ Generation failed")
            
    def run(self, limit: int = None, force: bool = False):
        print("=" * 60)
        print(f"FalkorDB Graph Data Enrichment: {config.GRAPH_NAME}")
        print("=" * 60)
        
        start_time = time.time()
        
        # Dynamically get all labels
        labels = self.get_all_labels()
        print(f"Found Node Types: {', '.join(labels)}")
        
        for label in labels:
            self.process_label(label, limit, force)
            
        elapsed = time.time() - start_time
        
        print("=" * 60)
        print(f"✅ All done! ({self.processed_count} updated, {elapsed:.1f}s)")
        print("=" * 60)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--graph', default=config.GRAPH_NAME)
    parser.add_argument('--sample', type=int)
    parser.add_argument('--full', action='store_true')
    parser.add_argument('--force', action='store_true', help='Force overwrite existing descriptions')
    parser.add_argument('--ollama-url', default=config.OLLAMA_URL)
    args = parser.parse_args()
    
    if not args.sample and not args.full:
        print("❌ Usage: python 2_enrich_graph_data.py --full [--force]")
        print("          python 2_enrich_graph_data.py --sample 10")
        return
    
    enricher = GraphEnricher(graph_name=args.graph, ollama_url=args.ollama_url)
    enricher.run(limit=args.sample if args.sample else None, force=args.force)

if __name__ == "__main__":
    main()