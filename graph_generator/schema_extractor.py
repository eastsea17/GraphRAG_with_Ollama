"""
Schema Extractor
================
LLM-driven schema discovery and validation for graph structure.
"""

import json
from typing import Dict, List, Optional
from dataclasses import dataclass, field, asdict
import config
from .llm_interface import LLMClient, PromptTemplates
from .data_loader import DataLoader


@dataclass
class NodeType:
    """Definition of a node type in the graph schema."""
    type: str
    description: str
    attributes: List[str]
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class EdgeType:
    """Definition of an edge type in the graph schema."""
    type: str
    description: str
    from_node: str
    to_node: str
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class GraphSchema:
    """Complete graph schema with nodes and edges."""
    nodes: List[NodeType] = field(default_factory=list)
    edges: List[EdgeType] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'nodes': [n.to_dict() for n in self.nodes],
            'edges': [e.to_dict() for e in self.edges],
            'metadata': self.metadata
        }
    
    def save(self, file_path: str):
        """Save schema to JSON file."""
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
    
    @staticmethod
    def load(file_path: str) -> 'GraphSchema':
        """Load schema from JSON file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        schema = GraphSchema()
        schema.nodes = [NodeType(**n) for n in data.get('nodes', [])]
        schema.edges = [EdgeType(**e) for e in data.get('edges', [])]
        schema.metadata = data.get('metadata', {})
        
        return schema
    
    def get_node_type(self, type_name: str) -> Optional[NodeType]:
        """Get node type definition by name."""
        for node in self.nodes:
            if node.type == type_name:
                return node
        return None
    
    def get_edge_type(self, type_name: str) -> Optional[EdgeType]:
        """Get edge type definition by name."""
        for edge in self.edges:
            if edge.type == type_name:
                return edge
        return None


class SchemaExtractor:
    """Extract graph schema from raw data using LLM."""
    
    def __init__(self, llm_client: LLMClient = None):
        """Initialize schema extractor.
        
        Args:
            llm_client: LLM client (creates new if not provided)
        """
        self.llm = llm_client or LLMClient()
    
    def discover_schema(self, data: Dict, max_retries: int = None) -> GraphSchema:
        """Discover graph schema from raw data.
        
        Args:
            data: Data dictionary from DataLoader
            max_retries: Maximum retry attempts for valid schema
            
        Returns:
            Discovered graph schema
        """
        max_retries = max_retries or config.SCHEMA_DISCOVERY_RETRIES
        
        print("\n" + "=" * 60)
        print("🔍 Schema Discovery")
        print("=" * 60)
        
        # Step 1: Analyze topics
        print("\n📊 Step 1: Analyzing content topics...")
        content_sample = DataLoader.get_content_sample(data, max_chars=3000)
        topic_prompt = PromptTemplates.topic_analysis(content_sample)
        
        topics = None
        for attempt in range(max_retries):
            try:
                topics = self.llm.generate_json(topic_prompt)
                print(f"   ✅ Domain: {topics.get('domain', 'Unknown')}")
                print(f"   ✅ Topics: {', '.join(topics.get('main_topics', []))}")
                break
            except Exception as e:
                print(f"   ⚠️  Attempt {attempt + 1} failed: {e}")
                if attempt == max_retries - 1:
                    raise RuntimeError("Failed to analyze topics after retries")
        
        # Step 2: Analyze Data Structure
        print("\n🏗️  Step 2: Analyzing data structure...")
        columns = data.get('metadata', {}).get('columns', [])
        structure_prompt = PromptTemplates.data_structure_analysis(columns, content_sample)
        
        structure = None
        for attempt in range(max_retries):
            try:
                structure = self.llm.generate_json(structure_prompt)
                print(f"   ✅ Row represents: {structure.get('row_entity_type', 'Unknown')}")
                print(f"   ✅ Strategy: {structure.get('modeling_strategy', 'Unknown')}")
                break
            except Exception as e:
                print(f"   ⚠️  Attempt {attempt + 1} failed: {e}")
                if attempt == max_retries - 1:
                    raise RuntimeError("Failed to analyze structure after retries")
        
        # Step 3: Discover schema
        print("\n🎨 Step 3: Designing graph schema...")
        schema_prompt = PromptTemplates.schema_discovery(content_sample, topics, structure)
        
        schema_json = None
        for attempt in range(max_retries):
            try:
                schema_json = self.llm.generate_json(schema_prompt)
                
                # Validate schema structure
                if not isinstance(schema_json.get('nodes'), list):
                    raise ValueError("Schema must have 'nodes' as list")
                if not isinstance(schema_json.get('edges'), list):
                    raise ValueError("Schema must have 'edges' as list")
                
                print(f"   ✅ Discovered {len(schema_json['nodes'])} node types")
                print(f"   ✅ Discovered {len(schema_json['edges'])} edge types")
                break
                
            except Exception as e:
                print(f"   ⚠️  Attempt {attempt + 1} failed: {e}")
                if attempt == max_retries - 1:
                    raise RuntimeError("Failed to discover schema after retries")
        
        # Step 4: Build GraphSchema object
        print("\n🔨 Step 4: Building schema object...")
        schema = GraphSchema()
        
        # Add nodes
        for n in schema_json.get('nodes', []):
            attributes = n.get('attributes', [])
            # Fallback: If no attributes provided, add 'name'
            if not attributes:
                print(f"   ⚠️  Node {n['type']} has no attributes. Adding default 'name'.")
                attributes = ['name']
                
            node = NodeType(
                type=n['type'],
                description=n.get('description', ''),
                attributes=attributes
            )
            schema.nodes.append(node)
            print(f"   📦 Node: {node.type} ({len(node.attributes)} attributes)")
        
        # Add edges
        for edge_def in schema_json.get('edges', []):
            edge = EdgeType(
                type=edge_def.get('type', 'UNKNOWN'),
                description=edge_def.get('description', ''),
                from_node=edge_def.get('from_node', ''),
                to_node=edge_def.get('to_node', '')
            )
            schema.edges.append(edge)
            print(f"   🔗 Edge: {edge.type} ({edge.from_node} -> {edge.to_node})")
        
        # Add metadata
        schema.metadata = {
            'domain': topics.get('domain', 'Unknown'),
            'topics': topics.get('main_topics', []),
            'content_type': topics.get('content_type', 'Unknown'),
            'source_file': data.get('metadata', {}).get('file_name', 'Unknown')
        }
        
        # Validate schema
        self.validate_schema(schema)
        
        print("\n✅ Schema discovery complete!")
        print("=" * 60)
        
        return schema
    
    def validate_schema(self, schema: GraphSchema):
        """Validate schema consistency.
        
        Args:
            schema: Graph schema to validate
            
        Raises:
            ValueError: If schema is invalid
        """
        # Check for nodes
        if not schema.nodes:
            raise ValueError("Schema must have at least one node type")
        
        # Check for unique node types
        node_types = [n.type for n in schema.nodes]
        if len(node_types) != len(set(node_types)):
            raise ValueError("Duplicate node types found")
        
        # Validate edges
        valid_edges = []
        for edge in schema.edges:
            if not edge.from_node or not edge.to_node:
                print(f"   ⚠️  Skipping invalid edge {edge.type}: Missing endpoints ({edge.from_node} -> {edge.to_node})")
                continue
                
            if edge.from_node not in node_types:
                print(f"   ⚠️  Skipping invalid edge {edge.type}: Unknown source node {edge.from_node}")
                continue
                
            if edge.to_node not in node_types:
                print(f"   ⚠️  Skipping invalid edge {edge.type}: Unknown target node {edge.to_node}")
                continue
                
            valid_edges.append(edge)
            
        schema.edges = valid_edges
        
        # Check for attributes
        for node in schema.nodes:
            if not node.attributes:
                raise ValueError(f"Node type {node.type} must have at least one attribute")
