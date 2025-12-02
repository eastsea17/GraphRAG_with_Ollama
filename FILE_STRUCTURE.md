# 📁 File Structure and Description

## 📊 Project Overview

This project is a **100% Ollama-based GraphRAG system** that builds a battery industry knowledge graph and provides natural language Q&A.

## 🗂️ Directory Structure

```
251201_Building_GraphRAG/
├── data/
│   ├── csv/                       # CSV Data
│   │   ├── papers.csv             # Paper Hub Nodes
│   │   ├── research_purpose.csv   # Extracted Purpose Nodes
│   │   ├── research_background.csv # Extracted Background Nodes
│   │   ├── research_methodology.csv # Extracted Methodology Nodes
│   │   ├── research_resultsandeffects.csv # Extracted Results Nodes
│   │   └── relations.csv          # Edges (Structural + Semantic)
│   ├── schema.json                # Graph schema (for auto-generation)
│   └── embedding/                 # Embedding cache
│
├── Rawdata/
│   └── rawdata.csv                # Raw scientific papers
│
│
├── 0_graph_schema_discovery.py              # Step 0a: Auto Graph Generation (LLM)
├── 0_generate_research_keywords.py             # Step 0b: Paper Keyword Extraction (LLM)
├── 1_load_to_falkordb.py            # Step 1: Load to DB (--graph support)
├── 2_enrich_graph_data.py           # Step 2: Generate Descriptions (--graph support)
├── 3_create_embeddings.py           # Step 3: Create Embeddings (--graph support)
├── 4_graph-rag.py                   # Step 4a: Basic GraphRAG Query
├── 4_graph-rag-agent.py             # Step 4b: Interactive RAG Agent
├── 5_analyze_network.py             # Step 5: Network Analysis (--graph support)
├── config.py                        # Configuration
├── enrich_export.py                 # Export Utility
├── requirements.txt                 # Python Dependencies
│
├── README.md                        # Project Overview
├── README_OLLAMA.md                 # Ollama Guide
├── GRAPH_GENERATOR_README.md        # Graph Generator Guide
└── FILE_STRUCTURE.md                # This File
```

---

## 📝 Detailed File Descriptions

### 🐍 Python Scripts (By Execution Order)

#### `0_graph_schema_discovery.py` - Auto Graph Generation (LLM)
**Function**: Automatically generates graph from any raw data using LLM

**See**: `GRAPH_GENERATOR_README.md` for detailed documentation

---

#### `0_generate_research_keywords.py` - Scientific Paper Analysis
**Function**: Extracts structured keywords from scientific papers and builds a sophisticated knowledge graph.

**Key Features**:
- **Paper Hubs**: Creates a `Paper` node for each document.
- **Structural Edges**: Connects Paper to its keywords (`HAS_PURPOSE`, `HAS_METHOD`, etc.).
- **Semantic Edges**: Connects keywords of the **same type** if they are semantically similar.
- **LLM Extraction**: Extracts Purpose, Background, Methodology, Results.

**Output**:
- `papers.csv`
- `research_purpose.csv`, `research_background.csv`, etc.
- `relations.csv`

**Execution**:
```bash
python 0_generate_research_keywords.py
```

---

#### `1_load_to_falkordb.py` - Load Data to FalkorDB
**Function**: Dynamically loads ALL CSV files found in `data/csv/` into FalkorDB.

**Key Features**:
- **Dynamic Loading**: Automatically detects node files.
- **Graph Support**: Specify target graph with `--graph`.
- **Clear Option**: Clear existing graph with `--clear`.

**Execution**:
```bash
python 1_load_to_falkordb.py --clear --graph Paper_Keywords2
```

---

#### `2_enrich_graph_data.py` - Generate Descriptions (Ollama LLM)
**Function**: Adds AI-generated descriptions to graph nodes

**Model Used**: `deepseek-r1:8b` (Ollama LLM)

**Key Operations**:
1. Retrieve nodes without descriptions
2. Generate descriptions for each node using Ollama LLM
   - Technology: Technical features, uses, pros/cons
   - Company: Company info, main business, characteristics
3. Save generated descriptions as node properties

**Execution**:
```bash
# Enrich default graph
python 2_enrich_graph_data.py

# Enrich specific graph
python 2_enrich_graph_data.py --graph Paper_Keywords

# Sample mode (10 nodes)
python 2_enrich_graph_data.py --sample 10

# Full mode
python 2_enrich_graph_data.py --full
```

**Configuration**:
```python
# Modify config.py
LLM_MODEL = 'deepseek-r1:8b'
```

---

#### `3_create_embeddings.py` - Create Embeddings (Ollama)
**Function**: Converts node descriptions into vector embeddings

**Model Used**: `nomic-embed-text:latest` (Ollama Embedding)

**Key Operations**:
1. Retrieve nodes without embeddings
2. Convert text → vector using Ollama API
3. Save vector as node property `embedding`
4. Persistent caching in `data/embedding/embeddings_cache.json`

**Features**:
- Data preparation for client-side search
- Prevents 'Invalid arguments' errors
- Caches embeddings for reuse

**Execution**:
```bash
# Create embeddings for default graph
python 3_create_embeddings.py

# Create embeddings for specific graph
python 3_create_embeddings.py --graph Paper_Keywords
```

---

#### `4_graph-rag.py` - GraphRAG Query System
**Function**: Natural Language Q&A System (Guaranteed RAG)

**Models Used**:
- Embedding: `nomic-embed-text:latest`
- LLM: `deepseek-r1:8b`

**Key Operations**:
1. Cache all node data in memory
2. Convert user question to vector
3. Calculate cosine similarity within Python (No DB index used)
4. Select Top-K similar nodes
5. Expand graph relationship information
6. Generate LLM answer based on context

**Features**:
- **Guaranteed RAG**: Removes DB index dependency
- Guaranteed accuracy with in-memory search

**Execution**:
```bash
python 4_graph-rag.py
```

**Example Questions**:
- "Who develops Sodium-Ion batteries?"
- "Which battery companies collaborate with Ford?"

---

#### `5_analyze_network.py` - Network Analysis
**Function**: Analyze graph network and discover important nodes

**Analysis Algorithms**:
1. **Degree Centrality**: Popularity based on connection count
   - Discover nodes with the most connections
2. **Influence Score**: Structural influence analysis
   - Based on incoming edge count
3. **Clustering Coefficient**: Local clustering analysis
   - Measures triangle density around nodes

**Execution**:
```bash
# Analyze default graph
python 5_analyze_network.py

# Analyze specific graph
python 5_analyze_network.py --graph Paper_Keywords
```

**Output Example**:
```
=== Graph Statistics ===
Total Nodes: 1315
Total Edges: 101967

=== 1. Degree Centrality TOP 10 ===
Rank 1: [Keyword] technology classification (Degree: 735)
...

=== 2. PageRank (Structural Influence) TOP 10 ===
Rank 1: [Keyword] patent data analysis... (Influence: 446)
...
```

**Features**:
- Works with any graph schema
- Generic node/edge queries
- Multiple centrality metrics

---

## 🔄 Overall Execution Order

### Step 1: Environment Setup

```bash
# Download Ollama models
ollama pull deepseek-r1:8b
ollama pull nomic-embed-text

# Run FalkorDB
docker run -p 6379:6379 -p 3001:3000 -it --rm \
  -v ./data:/var/lib/falkordb/data \
  falkordb/falkordb
```

### Step 2: Data Preparation

```bash
# Step 0: Generate Data
python 0_generate_data.py

# Step 1: Load to DB
python 1_load_to_falkordb.py
```

### Step 3: AI Processing

```bash
# Step 2: Generate Descriptions (Ollama LLM)
python 2_enrich_graph_data.py

# Step 3: Create Embeddings (Ollama Embedding)
python 3_create_embeddings.py
```

### Step 4: Utilization

```bash
# Step 4: GraphRAG Query
python 4_graph-rag.py

# Step 5: Network Analysis
python 5_analyze_network.py
```

---

## 📋 CSV File Format

### `companies.csv`
```csv
name,country
LG Energy Solution,Korea
Tesla,USA
CATL,China
...
```

### `technologies.csv`
```csv
name,category
NCM Battery,Battery
LFP Battery,Battery
BMS,Software
...
```

### `relations.csv`
```csv
START_ID,END_ID,TYPE
LG Energy Solution,NCM Battery,DEVELOPS
Tesla,LFP Battery,DEVELOPS
CATL,LFP Battery,DEVELOPS
...
```

---

## ⚙️ Key Configuration File Locations

| Setting Item | File | Default Value |
|---------|------|--------|
| Data Count | `0_generate_data.py` | 20/100/300 |
| LLM Model | `config.py` | `deepseek-r1:8b` |
| Embedding Model | `config.py` | `nomic-embed-text:latest` |
| Chat Model | `config.py` | `deepseek-r1:8b` |
| Graph Name | `config.py` | `EnergyGraph` |

---

## 🎯 Next Steps

Once you understand the file structure:

1. ✅ Check **README_OLLAMA.md** - Detailed Ollama setup guide
2. ✅ Check **README.md** - Overall project overview
3. 🚀 **Run Scripts Step-by-Step** - Refer to the execution order above
4. 🎬 **Use GraphRAG** - Test the Q&A system

---

**All set! Now enjoy your 100% free GraphRAG system!** 🎉
