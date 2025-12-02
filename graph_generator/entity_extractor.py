"""
Entity Extractor
================
Extract nodes and edges from raw data using discovered schema.
"""

import json
from typing import Dict, List, Tuple
from collections import defaultdict
import config
from .llm_interface import LLMClient, PromptTemplates
from .schema_extractor import GraphSchema, NodeType, EdgeType


class EntityExtractor:
    """Extract entities and relationships from raw data."""
    
    def __init__(self, llm_client: LLMClient = None):
        """Initialize entity extractor.
        
        Args:
            llm_client: LLM client (creates new if not provided)
        """
        self.llm = llm_client or LLMClient()
    
    def extract_all(self, data: Dict, schema: GraphSchema) -> Tuple[Dict[str, List[Dict]], List[Dict]]:
        """Extract all nodes and edges from data.
        
        Args:
            data: Data dictionary from DataLoader
            schema: Graph schema
            
        Returns:
            Tuple of (nodes_by_type, edges)
            - nodes_by_type: Dict mapping node type to list of nodes
            - edges: List of edge dictionaries
        """
        print("\n" + "=" * 60)
        print("🔎 Entity Extraction (Row-based)")
        print("=" * 60)
        
        # Get structured data
        structured = data.get('structured', [])
        
        # Limit rows
        if config.MAX_ROWS_FOR_EXTRACTION:
            structured = structured[:config.MAX_ROWS_FOR_EXTRACTION]
            if len(data.get('structured', [])) > config.MAX_ROWS_FOR_EXTRACTION:
                print(f"   ℹ️  Processing first {config.MAX_ROWS_FOR_EXTRACTION} rows")
        
        if not structured:
            print("   ⚠️  No structured data found.")
            return {}, []

        all_nodes = []
        all_edges = []
        
        # Process in batches
        batch_size = config.BATCH_SIZE
        total_batches = (len(structured) + batch_size - 1) // batch_size
        print(f"   📦 Processing {len(structured)} rows in {total_batches} batches (batch size: {batch_size})")
        
        for i in range(0, len(structured), batch_size):
            batch = structured[i:i + batch_size]
            batch_num = i // batch_size + 1
            
            print(f"   ⏳ Batch {batch_num}/{total_batches}...", end=" ", flush=True)
            
            try:
                # Generate prompt for simultaneous extraction
                prompt = PromptTemplates.row_extraction(batch, schema.to_dict())
                
                # Call LLM
                result = self.llm.generate_json(prompt)
                
                # Parse result
                nodes = result.get('nodes', [])
                edges = result.get('edges', [])
                
                if isinstance(nodes, list):
                    all_nodes.extend(nodes)
                if isinstance(edges, list):
                    all_edges.extend(edges)
                    
                print(f"✅ ({len(nodes)} nodes, {len(edges)} edges)")
                
            except Exception as e:
                print(f"❌ Failed: {str(e)[:100]}")
                continue
        
        # Post-process results
        print(f"\n🧹 Post-processing {len(all_nodes)} nodes and {len(all_edges)} edges...")
        nodes_by_type = self.organize_nodes(all_nodes, schema)
        clean_edges = self.clean_edges(all_edges, schema, nodes_by_type)
        
        print("\n✅ Entity extraction complete!")
        print("=" * 60)
        
        return nodes_by_type, clean_edges
    
    def organize_nodes(self, nodes: List[Dict], schema: GraphSchema) -> Dict[str, List[Dict]]:
        """Organize nodes by type and remove duplicates."""
        nodes_by_type = defaultdict(list)
        seen = set()
        
        for node in nodes:
            node_type = node.get('type')
            attrs = node.get('attributes', {})
            
            if not node_type or not attrs:
                continue
                
            # Find primary key (first attribute)
            node_def = schema.get_node_type(node_type)
            if not node_def:
                continue
                
            key_attr = node_def.attributes[0]
            key_val = attrs.get(key_attr)
            
            if not key_val:
                continue
                
            # Create unique ID
            unique_id = f"{node_type}:{key_val}"
            
            if unique_id not in seen:
                seen.add(unique_id)
                # Flatten structure: {'type': 'A', 'attributes': {'name': 'X'}} -> {'name': 'X'}
                flat_node = attrs.copy()
                nodes_by_type[node_type].append(flat_node)
                
        return dict(nodes_by_type)
    
    def clean_edges(self, edges: List[Dict], schema: GraphSchema, nodes_by_type: Dict) -> List[Dict]:
        """Validate and format edges."""
        valid_edges = []
        
        # Build lookup for existence check
        node_keys = defaultdict(set)
        for n_type, n_list in nodes_by_type.items():
            node_def = schema.get_node_type(n_type)
            if node_def:
                key_attr = node_def.attributes[0]
                for n in n_list:
                    if n.get(key_attr):
                        node_keys[n_type].add(n[key_attr])
        
        for edge in edges:
            rel_type = edge.get('type')
            src = edge.get('from')
            dst = edge.get('to')
            src_type = edge.get('from_type')
            dst_type = edge.get('to_type')
            
            if not (rel_type and src and dst):
                continue
                
            # If types are missing, try to infer from schema (if unique)
            if not src_type or not dst_type:
                edge_def = schema.get_edge_type(rel_type)
                if edge_def:
                    src_type = src_type or edge_def.from_node
                    dst_type = dst_type or edge_def.to_node
            
            # Validate existence
            if src_type in node_keys and src in node_keys[src_type] and \
               dst_type in node_keys and dst in node_keys[dst_type]:
                
                valid_edges.append({
                    'START_ID': src,
                    'END_ID': dst,
                    'TYPE': rel_type
                })
                
        return valid_edges
