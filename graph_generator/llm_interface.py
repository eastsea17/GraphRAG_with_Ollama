"""
LLM Interface for Graph Generation
===================================
Handles communication with Ollama and prompt management.
"""

import json
import requests
from typing import Dict, List, Any, Optional
import config


class LLMClient:
    """Client for interacting with Ollama LLM."""
    
    def __init__(self, model: str = None, url: str = None):
        """Initialize LLM client.
        
        Args:
            model: Model name (defaults to config.GRAPH_GENERATION_MODEL)
            url: Ollama API URL (defaults to config.OLLAMA_URL)
        """
        self.model = model or config.GRAPH_GENERATION_MODEL
        self.url = url or config.OLLAMA_URL
        self.api_endpoint = f"{self.url}/api/generate"
        
    def generate(self, prompt: str, temperature: float = None, max_tokens: int = None) -> str:
        """Generate text from prompt.
        
        Args:
            prompt: Input prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated text
        """
        temperature = temperature or config.TEMPERATURE
        max_tokens = max_tokens or config.MAX_TOKENS
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens
            }
        }
        
        try:
            print(f"   🤖 Calling {self.model}...", end=" ", flush=True)
            response = requests.post(self.api_endpoint, json=payload, timeout=300)
            response.raise_for_status()
            result = response.json()
            generated_text = result.get('response', '').strip()
            
            if not generated_text:
                print(f"❌")
                raise RuntimeError(f"LLM returned empty response. Model: {self.model}, Result: {result}")
            
            print(f"✅ ({len(generated_text)} chars)")
            return generated_text
            
        except requests.exceptions.Timeout:
            print(f"❌")
            raise RuntimeError(f"LLM API timeout after 300s. Model {self.model} might be too slow or not responding.")
        except requests.exceptions.RequestException as e:
            print(f"❌")
            raise RuntimeError(f"LLM API error: {e}\nModel: {self.model}\nURL: {self.api_endpoint}")
        except Exception as e:
            print(f"❌")
            raise RuntimeError(f"Unexpected error: {e}")
    
    def generate_json(self, prompt: str, temperature: float = 0.3) -> Dict:
        """Generate JSON output from prompt.
        
        Args:
            prompt: Input prompt requesting JSON output
            temperature: Lower temperature for more consistent JSON
            
        Returns:
            Parsed JSON dictionary
        """
        response = self.generate(prompt, temperature=temperature)
        
        if not response:
            raise ValueError("LLM returned empty response (no content generated)")
        
        # Try to extract JSON from response
        try:
            # Clean up response (remove <think>...</think> blocks for DeepSeek models)
            import re
            clean_response = re.sub(r'<think>.*?</think>', '', response, flags=re.DOTALL).strip()
            
            # Look for JSON block in markdown
            if "```json" in clean_response:
                json_str = clean_response.split("```json")[1].split("```")[0].strip()
            elif "```" in clean_response:
                json_str = clean_response.split("```")[1].split("```")[0].strip()
            else:
                json_str = clean_response.strip()
            
            return json.loads(json_str)
        except (json.JSONDecodeError, IndexError) as e:
            # Show more context for debugging
            preview = response[:1000] if len(response) > 1000 else response
            raise ValueError(
                f"Failed to parse JSON from LLM response.\n"
                f"Error: {e}\n"
                f"Model: {self.model}\n"
                f"Response preview (first 1000 chars):\n{preview}\n"
                f"Response length: {len(response)} chars"
            )


class PromptTemplates:
    """Collection of prompts for different analysis stages."""
    
    @staticmethod
    def topic_analysis(content_sample: str) -> str:
        """Prompt for topic and domain identification.
        
        Args:
            content_sample: Sample of raw data content
            
        Returns:
            Prompt string
        """
        return f"""Analyze the following dataset and identify the main topics and domain.

Dataset sample:
{content_sample}

Provide your analysis in JSON format:
{{
    "domain": "Brief description of the domain (e.g., 'Computer Science - Knowledge Graphs')",
    "main_topics": ["topic1", "topic2", "topic3"],
    "content_type": "Type of content (e.g., 'academic papers', 'business data', 'research articles')",
    "key_entities": ["key entity types that appear in the data"]
}}

Output only valid JSON, no additional text."""
    
    @staticmethod
    def data_structure_analysis(columns: List[str], content_sample: str) -> str:
        """Prompt for analyzing the structure of the data.
        
        Args:
            columns: List of column names
            content_sample: Sample of raw data content
            
        Returns:
            Prompt string
        """
        return f"""Analyze the STRUCTURE of this tabular dataset (CSV/Excel).

Columns: {', '.join(columns)}

Dataset sample:
{content_sample}

Analyze the following:
1. Row Definition: What does a single row represent? (e.g., "A scientific paper", "A transaction", "A company profile")
2. Key Entities: Which columns represent distinct entities? (e.g., 'author' column -> Author entity, 'company' column -> Company entity)
3. Relationships: What relationships are implied by the columns? (e.g., Row is Paper, 'author' column implies Paper HAS_AUTHOR Author)
4. Cardinality: Are columns single-value or multi-value (lists)?

Provide your analysis in JSON format:
{{
    "row_entity_type": "The main entity type represented by a row",
    "column_mapping": {{
        "column_name": "Suggested Node Type or Attribute"
    }},
    "potential_relationships": [
        "Description of relationship 1",
        "Description of relationship 2"
    ],
    "modeling_strategy": "Brief advice on how to model this as a graph"
}}

Output only valid JSON, no additional text."""

    @staticmethod
    def schema_discovery(content_sample: str, topics: Dict, structure: Dict) -> str:
        """Prompt for Node and Edge schema generation.
        
        Args:
            content_sample: Sample of raw data content
            topics: Topic analysis results
            structure: Data structure analysis results
            
        Returns:
            Prompt string
        """
        max_nodes = config.MAX_NODE_TYPES
        max_edges = config.MAX_EDGE_TYPES
        
        return f"""Based on the data structure analysis, design a SIMPLE knowledge graph schema.

Domain: {topics.get('domain', 'Unknown')}
Row Represents: {structure.get('row_entity_type', 'Unknown')}
Modeling Strategy: {structure.get('modeling_strategy', '')}

Structure Analysis:
- Potential Relationships: {', '.join(structure.get('potential_relationships', []))}
- Column Mapping: {json.dumps(structure.get('column_mapping', {}))}

Dataset sample:
{content_sample}

IMPORTANT CONSTRAINTS:
- Create EXACTLY {max_nodes} Node types
- Create EXACTLY {max_edges} Edge types
- Use the "Row Represents" entity as the central Node type
- Convert columns representing other entities into separate Nodes, connected by Edges
- Keep attributes simple

Provide the schema in JSON format:
{{
    "nodes": [
        {{
            "type": "NodeTypeName",
            "description": "Brief description",
            "attributes": ["attr1", "attr2"]
        }}
    ],
    "edges": [
        {{
            "type": "EDGE_TYPE_NAME",
            "description": "Brief description",
            "from_node": "SourceNodeType",
            "to_node": "TargetNodeType"
        }}
    ]
}}

Output only valid JSON, no additional text."""
    
    @staticmethod
    def entity_extraction(data_rows: List[Dict], node_schema: Dict, node_type: str) -> str:
        """Prompt for extracting nodes from data.
        
        Args:
            data_rows: Batch of data rows
            node_schema: Node type definition
            node_type: Type of node to extract
            
        Returns:
            Prompt string
        """
        attrs = node_schema.get('attributes', [])
        desc = node_schema.get('description', '')
        
        # Limit data shown to LLM for faster processing
        batch_size = min(config.BATCH_SIZE, len(data_rows))
        sample_rows = data_rows[:batch_size]
        
        # Simplify data - only show essential fields
        simplified_data = []
        for row in sample_rows:
            # Only include non-empty values and truncate long text
            simplified_row = {k: str(v)[:config.MAX_TEXT_LENGTH] for k, v in row.items() if v}
            simplified_data.append(simplified_row)
        
        data_str = json.dumps(simplified_data, indent=2, ensure_ascii=False)
        
        return f"""Extract {node_type} entities from this data.

Node Type: {node_type}
Required Attributes: {', '.join(attrs)}

Data ({len(simplified_data)} rows):
{data_str}

Extract entities as a JSON array. Be concise:
[
    {{{', '.join([f'"{attr}": "..."' for attr in attrs])}}},
    ...
]

IMPORTANT:
- Output ONLY the JSON array
- No markdown, no explanation
- Use empty string "" for missing values"""
    
    @staticmethod
    def row_extraction(data_rows: List[Dict], schema: Dict) -> str:
        """Prompt for extracting nodes and edges from data rows.
        
        Args:
            data_rows: Batch of data rows
            schema: Graph schema definition
            
        Returns:
            Prompt string
        """
        # Simplify data
        simplified_data = []
        for row in data_rows:
            simplified_row = {k: str(v)[:config.MAX_TEXT_LENGTH] for k, v in row.items() if v}
            simplified_data.append(simplified_row)
            
        data_str = json.dumps(simplified_data, indent=2, ensure_ascii=False)
        
        # Schema summary
        node_types = [f"{n['type']} (attrs: {', '.join(n['attributes'])})" for n in schema['nodes']]
        edge_types = [f"{e['type']} ({e['from_node']} -> {e['to_node']})" for e in schema['edges']]
        
        return f"""Extract Knowledge Graph entities and relationships from this data.

Schema:
- Nodes: {', '.join(node_types)}
- Edges: {', '.join(edge_types)}

Data ({len(simplified_data)} rows):
{data_str}

For EACH row, extract all relevant Nodes and Edges defined in the Schema.
- If a column contains a list (e.g. "Author1, Author2"), create multiple Nodes and Edges.
- Use the exact attribute names from the Schema.

Output as a JSON object with "nodes" and "edges" arrays:
{{
    "nodes": [
        {{ "type": "NodeType", "attributes": {{ "attr1": "val1" }} }},
        ...
    ],
    "edges": [
        {{ "type": "EDGE_TYPE", "from": "source_id", "to": "target_id", "from_type": "SourceType", "to_type": "TargetType" }},
        ...
    ]
}}

IMPORTANT:
- "from" and "to" in edges must match the first attribute of the corresponding nodes.
- Output ONLY valid JSON.
"""
