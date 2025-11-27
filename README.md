# FalkorDB GraphRAG System

This directory contains a Battery Industry GraphRAG system using FalkorDB.

## 📁 File Structure

### Data Files
- `companies.csv` - Battery company data (1,200 entries)
- `technologies.csv` - Battery technology data (12,000 entries)
- `relations.csv` - Company-Technology relationship data (20,000 entries)

### GraphRAG System
1. **`enrich_graph_data.py`** - Add descriptions to nodes
   - Automatically generates descriptions for each node using LLM
   
2. **`create_embeddings.py`** - Create vector embeddings
   - Converts descriptions to vectors and creates indexes
   
3. **`graphrag_query.py`** - GraphRAG Query System
   - Vector Search + Graph Traversal + LLM Answer Generation
   
4. **`demo_graphrag.py`** - Demo Script
   - Test the system with sample questions

### Others
- `analyze_network.py` - Network Analysis (PageRank, etc.)
- `FalkorDB.ipynb` - Jupyter Notebook
- `generate_data.py` - Data Generation Script

## 🚀 Quick Start Guide

### 1. Environment Setup

```bash
# Install required packages
pip install falkordb

# Install Ollama (if not already installed)
# Visit https://ollama.com/download
```

### 2. Run FalkorDB

```bash
# Run FalkorDB with Docker
docker run -p 6379:6379 -p 3001:3000 -it --rm -v ./data:/var/lib/falkordb/data falkordb/falkordb
```

### 3. Load Data (Skip if already done)

```bash
# Run bulk insert in terminal
falkordb-bulk-insert EnergyGraph \
  --nodes-with-label Company companies.csv \
  --nodes-with-label Technology technologies.csv \
  --relations-with-type DEVELOPS relations.csv
```

### 4. Build GraphRAG System

**Step 1: Add Descriptions to Nodes** (Test)
```bash
# Process only 10 samples
python enrich_graph_data.py --sample 10
```

If everything looks good, process all:
```bash
# Process all nodes (Takes time, incurs API costs)
python enrich_graph_data.py --full
```

**Step 2: Create Vector Embeddings** (Test)
```bash
# Process only 10 samples
python create_embeddings.py --sample 10
```

Process all:
```bash
# Create embeddings for all nodes
python create_embeddings.py --full
```

**Step 3: Test GraphRAG**
```bash
# Run demo
python demo_graphrag.py

# Or interactive mode
python graphrag_query.py
```

## 💡 Usage Examples

### Using in Python Code

```python
from graphrag_query import GraphRAG

# Initialize GraphRAG
rag = GraphRAG(graph_name='EnergyGraph')

# Ask a question
answer = rag.query("Which Korean company develops high-energy density batteries?")
print(answer)

# Ask with details
answer = rag.query(
    "Which companies develop Solid-State Batteries?",
    top_k=5,           # Search top 5 nodes
    verbose=True       # Print search process
)
```

### Interactive Mode

```bash
python graphrag_query.py
```

```
💬 Question: What battery technologies does Tesla develop?
🔍 Question: What battery technologies does Tesla develop?
...
✅ Answer:
Tesla develops LFP Battery and BMS technologies...
```

## 🔍 System Architecture

```
User Question
    ↓
1. Query Embedding (Ollama)
    ↓
2. Vector Search (FalkorDB)
   - Search Technology nodes
   - Search Company nodes
    ↓
3. Graph Traversal (Cypher)
   - Technology → DEVELOPS ← Company
   - Traverse relationship network
    ↓
4. Context Assembly
   - Collect searched node info
   - Add graph relationship info
    ↓
5. LLM Answer Generation (Ollama - DeepSeek/Llama3)
    ↓
Final Answer
```

## ⚙️ Configuration Options

### enrich_graph_data.py
- `--graph`: Graph name (Default: EnergyGraph)
- `--sample N`: Sample mode (Process only N items per type)
- `--full`: Process all nodes
- `--ollama-url`: Ollama URL (Default: http://localhost:11434)

### create_embeddings.py
Supports same options

### graphrag_query.py
```python
rag = GraphRAG(
    graph_name='EnergyGraph',  # Graph name
    ollama_url='http://localhost:11434' # Ollama URL
)

answer = rag.query(
    question,
    top_k=3,        # Number of top nodes to search
    verbose=False   # Whether to print detailed logs
)
```

## 📊 Check Data

### Using FalkorDB UI
Access `http://localhost:3001` in your browser

```cypher
// Check Technology nodes with descriptions
MATCH (t:Technology) 
WHERE t.description IS NOT NULL 
RETURN t LIMIT 5

// Check nodes with embeddings
MATCH (t:Technology) 
WHERE t.embedding IS NOT NULL 
RETURN t.name, t.description LIMIT 5

// Vector search test
CALL db.idx.vector.queryNodes('Technology', 'embedding', 3, [vector...]) 
YIELD node RETURN node
```

## 🐛 Troubleshooting

### "Ollama Connection Failed"
Ensure Ollama is running:
```bash
ollama serve
```

### "FalkorDB Connection Failed"
Check if FalkorDB Docker container is running:
```bash
docker ps | grep falkordb
```

### "No vector index found"
Run `create_embeddings.py` first.

## 💰 Estimated Costs

- **Free**: When using local Ollama models.
- **Hardware**: Requires sufficient RAM (16GB+ recommended) for running LLMs locally.

## 📚 Additional Info

- [FalkorDB Documentation](https://docs.falkordb.com/)
- [Ollama Documentation](https://ollama.com/)
- [GraphRAG Concept](https://www.microsoft.com/en-us/research/project/graphrag/)

## 🤝 Contribution

Please report bugs or suggest improvements via Issues!
