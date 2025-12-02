"""
CSV Generator
=============
Generate CSV files compatible with FalkorDB pipeline.
"""

import csv
import os
from typing import Dict, List
from pathlib import Path
import config


class CSVGenerator:
    """Generate CSV files for graph data."""
    
    @staticmethod
    def generate_all(nodes_by_type: Dict[str, List[Dict]], edges: List[Dict], 
                    output_dir: str = None) -> Dict[str, str]:
        """Generate all CSV files.
        
        Args:
            nodes_by_type: Dict mapping node type to list of nodes
            edges: List of edge dictionaries
            output_dir: Output directory (defaults to config.CSV_DIR)
            
        Returns:
            Dict mapping file purpose to file path
        """
        output_dir = output_dir or config.CSV_DIR
        os.makedirs(output_dir, exist_ok=True)
        
        print("\n" + "=" * 60)
        print("💾 CSV Generation")
        print("=" * 60)
        
        generated_files = {}
        
        # Generate node CSVs
        print("\n📦 Generating node CSV files...")
        for node_type, nodes in nodes_by_type.items():
            if nodes:
                file_path = CSVGenerator.generate_node_csv(
                    nodes, 
                    node_type, 
                    output_dir
                )
                generated_files[node_type] = file_path
                print(f"   ✅ {node_type}: {file_path} ({len(nodes)} nodes)")
        
        # Generate edge CSV
        if edges:
            print("\n🔗 Generating relationships CSV...")
            file_path = CSVGenerator.generate_edge_csv(edges, output_dir)
            generated_files['relations'] = file_path
            print(f"   ✅ Relations: {file_path} ({len(edges)} edges)")
        
        print("\n✅ CSV generation complete!")
        print(f"📁 Output directory: {output_dir}")
        print("=" * 60)
        
        return generated_files
    
    @staticmethod
    def generate_node_csv(nodes: List[Dict], node_type: str, output_dir: str) -> str:
        """Generate CSV file for a node type.
        
        Args:
            nodes: List of node dictionaries
            node_type: Type of nodes
            output_dir: Output directory
            
        Returns:
            Path to generated file
        """
        if not nodes:
            raise ValueError(f"No nodes provided for type: {node_type}")
        
        # Create filename (lowercase, replace spaces with underscores)
        filename = f"{node_type.lower().replace(' ', '_')}.csv"
        file_path = os.path.join(output_dir, filename)
        
        # Get all unique keys from nodes
        all_keys = set()
        for node in nodes:
            all_keys.update(node.keys())
        
        # Sort keys for consistent output
        headers = sorted(all_keys)
        
        # Write CSV
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=headers, extrasaction='ignore')
            writer.writeheader()
            
            for node in nodes:
                # Fill missing keys with empty strings
                row = {key: node.get(key, '') for key in headers}
                writer.writerow(row)
        
        return file_path
    
    @staticmethod
    def generate_edge_csv(edges: List[Dict], output_dir: str) -> str:
        """Generate CSV file for relationships.
        
        Args:
            edges: List of edge dictionaries
            output_dir: Output directory
            
        Returns:
            Path to generated file
        """
        if not edges:
            raise ValueError("No edges provided")
        
        file_path = os.path.join(output_dir, 'relations.csv')
        
        # Standard format: START_ID, END_ID, TYPE
        headers = ['START_ID', 'END_ID', 'TYPE']
        
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            
            for edge in edges:
                row = {
                    'START_ID': edge.get('START_ID', ''),
                    'END_ID': edge.get('END_ID', ''),
                    'TYPE': edge.get('TYPE', 'RELATED_TO')
                }
                writer.writerow(row)
        
        return file_path
    
    @staticmethod
    def validate_csv_format(csv_path: str) -> bool:
        """Validate that CSV file is properly formatted.
        
        Args:
            csv_path: Path to CSV file
            
        Returns:
            True if valid, False otherwise
        """
        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                headers = reader.fieldnames
                
                # Check for headers
                if not headers:
                    return False
                
                # Try to read first row
                first_row = next(reader, None)
                if first_row is None:
                    return False
                
                return True
                
        except Exception as e:
            print(f"Validation failed: {e}")
            return False
