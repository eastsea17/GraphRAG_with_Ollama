"""
GraphRAG Auto-Generation System
================================
Automatically analyze raw data files and generate Node/Edge CSV files using LLM.

This script:
1. Loads raw data from the Rawdata folder
2. Uses LLM to analyze content and identify topics
3. Discovers appropriate Node and Edge types
4. Extracts entities and relationships
5. Generates CSV files for FalkorDB loading

"""

import os
import sys
import argparse
from pathlib import Path
import config
from graph_generator import (
    DataLoader,
    LLMClient,
    SchemaExtractor,
    EntityExtractor,
    CSVGenerator,
    GraphSchema
)


def find_raw_data_files(directory: str = None) -> list:
    """Find all supported raw data files in directory.
    
    Args:
        directory: Directory to search (defaults to config.RAWDATA_DIR)
        
    Returns:
        List of file paths
    """
    directory = directory or config.RAWDATA_DIR
    
    if not os.path.exists(directory):
        raise FileNotFoundError(f"Rawdata directory not found: {directory}")
    
    files = []
    for ext in config.SUPPORTED_FORMATS:
        files.extend(Path(directory).glob(f"*{ext}"))
    
    return [str(f) for f in files]


def main():
    """Main execution flow."""
    
    # Parse arguments
    parser = argparse.ArgumentParser(description='Generate graph from raw data using LLM')
    parser.add_argument('--file', type=str, help='Specific file to process')
    parser.add_argument('--validate-schema', action='store_true', 
                       help='Validate schema file without extraction')
    parser.add_argument('--use-schema', type=str, 
                       help='Use existing schema file instead of discovering')
    parser.add_argument('--output-dir', type=str, default=config.CSV_DIR,
                       help='Output directory for CSV files')
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("  🤖 GraphRAG Auto-Generation System")
    print("=" * 70)
    print(f"📊 Graph Generation Model: {config.GRAPH_GENERATION_MODEL}")
    print(f"📁 Raw Data Dir: {config.RAWDATA_DIR}")
    print(f"💾 Output Dir: {args.output_dir}")
    print("=" * 70)
    
    # Validate schema mode
    if args.validate_schema:
        if os.path.exists(config.SCHEMA_OUTPUT):
            try:
                schema = GraphSchema.load(config.SCHEMA_OUTPUT)
                print(f"\n✅ Schema is valid!")
                print(f"   - Node types: {len(schema.nodes)}")
                print(f"   - Edge types: {len(schema.edges)}")
                for node in schema.nodes:
                    print(f"     📦 {node.type}: {node.attributes}")
                for edge in schema.edges:
                    print(f"     🔗 {edge.type}: {edge.from_node} -> {edge.to_node}")
                return
            except Exception as e:
                print(f"\n❌ Schema validation failed: {e}")
                sys.exit(1)
        else:
            print(f"\n❌ Schema file not found: {config.SCHEMA_OUTPUT}")
            sys.exit(1)
    
    # Find files to process
    if args.file:
        if not os.path.exists(args.file):
            print(f"\n❌ File not found: {args.file}")
            sys.exit(1)
        files_to_process = [args.file]
    else:
        files_to_process = find_raw_data_files()
        
        if not files_to_process:
            print(f"\n❌ No data files found in {config.RAWDATA_DIR}")
            print(f"   Supported formats: {', '.join(config.SUPPORTED_FORMATS)}")
            sys.exit(1)
    
    print(f"\n📂 Files to process: {len(files_to_process)}")
    for f in files_to_process:
        print(f"   - {f}")
    
    # For now, process only the first file
    # TODO: Support batch processing
    target_file = files_to_process[0]
    print(f"\n🎯 Processing: {target_file}")
    
    try:
        # Step 1: Load Data
        print("\n" + "=" * 70)
        print("Step 1: Loading Data")
        print("=" * 70)
        
        loader = DataLoader()
        data = loader.load(target_file)
        
        print(f"✅ Loaded {data['format'].upper()} file")
        print(f"   - File: {data['metadata']['file_name']}")
        
        if data['format'] == 'csv' or data['format'] == 'excel':
            print(f"   - Rows: {data['metadata']['rows']}")
            print(f"   - Columns: {len(data['metadata']['columns'])}")
        
        # Step 2: Discover or Load Schema
        print("\n" + "=" * 70)
        print("Step 2: Schema Discovery")
        print("=" * 70)
        
        llm_client = LLMClient()
        
        if args.use_schema and os.path.exists(args.use_schema):
            print(f"📖 Loading existing schema: {args.use_schema}")
            schema = GraphSchema.load(args.use_schema)
        else:
            extractor = SchemaExtractor(llm_client)
            schema = extractor.discover_schema(data)
            
            # Save schema
            os.makedirs(os.path.dirname(config.SCHEMA_OUTPUT) or '.', exist_ok=True)
            schema.save(config.SCHEMA_OUTPUT)
            print(f"\n💾 Schema saved to: {config.SCHEMA_OUTPUT}")
        
        # Print schema summary
        print(f"\n📋 Schema Summary:")
        print(f"   Domain: {schema.metadata.get('domain', 'Unknown')}")
        print(f"   Node Types: {len(schema.nodes)}")
        for node in schema.nodes:
            print(f"      📦 {node.type}: [{', '.join(node.attributes)}]")
        print(f"   Edge Types: {len(schema.edges)}")
        for edge in schema.edges:
            print(f"      🔗 {edge.type}: {edge.from_node} -> {edge.to_node}")
        
        # Confirm before extraction
        print("\n" + "=" * 70)
        confirm = input("➡️  Proceed with entity extraction? (y/N): ").strip().lower()
        if confirm != 'y':
            print("Cancelled. You can rerun with --use-schema to use the saved schema.")
            sys.exit(0)
        
        # Step 3: Extract Entities
        print("\n" + "=" * 70)
        print("Step 3: Entity Extraction")
        print("=" * 70)
        
        entity_extractor = EntityExtractor(llm_client)
        nodes_by_type, edges = entity_extractor.extract_all(data, schema)
        
        # Print extraction summary
        total_nodes = sum(len(nodes) for nodes in nodes_by_type.values())
        print(f"\n📊 Extraction Summary:")
        print(f"   Total Nodes: {total_nodes}")
        for node_type, nodes in nodes_by_type.items():
            print(f"      📦 {node_type}: {len(nodes)}")
        print(f"   Total Edges: {len(edges)}")
        
        # Step 4: Generate CSVs
        print("\n" + "=" * 70)
        print("Step 4: CSV Generation")
        print("=" * 70)
        
        generated_files = CSVGenerator.generate_all(
            nodes_by_type, 
            edges, 
            args.output_dir
        )
        
        # Final summary
        print("\n" + "=" * 70)
        print("✅ Graph Generation Complete!")
        print("=" * 70)
        print(f"\n📁 Generated Files:")
        for purpose, filepath in generated_files.items():
            print(f"   - {filepath}")
        
        print(f"\n📋 Schema File:")
        print(f"   - {config.SCHEMA_OUTPUT}")
        
        print(f"\n🚀 Next Steps:")
        print(f"   1. Review the generated schema: {config.SCHEMA_OUTPUT}")
        print(f"   2. Review the generated CSV files in: {args.output_dir}")
        print(f"   3. Load into FalkorDB:")
        print(f"      python 1_load_to_falkordb.py")
        print(f"   4. Enrich graph:")
        print(f"      python 2_enrich_graph_data.py --full")
        print(f"   5. Create embeddings:")
        print(f"      python 3_create_embeddings.py")
        print(f"   6. Test RAG queries:")
        print(f"      python 4_graph_rag.py --query 'Your question here'")
        
        print("\n" + "=" * 70)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
