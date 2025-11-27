# 📁 File Structure and Description

## 📊 Project Overview

This project is a **100% Ollama-based GraphRAG system** that builds a battery industry knowledge graph and provides natural language Q&A.

## 🗂️ Directory Structure

```
251125_FalkorDB/
├── data/
│   └── csv/                          # CSV data files
│       ├── companies.csv             # Company info (name, country)
│       ├── technologies.csv          # Technology info (name, category)
│       └── relations.csv             # Relationship info (START_ID, END_ID, TYPE)
│
├── 0_FalkorDB_intro.ipynb           # FalkorDB Introduction & Tutorial
│
├── 0_generate_data.py               # Step 0: Generate Data
├── 1_load_to_falkordb.py            # Step 1: Load to DB
├── 2_enrich_graph_data.py           # Step 2: Generate Descriptions (Ollama LLM)
├── 3_create_embeddings.py           # Step 3: Create Embeddings (Ollama)
├── 4_graph-rag.py                   # Step 4: GraphRAG Query System
├── 5_analyze_network.py             # Step 5: Network Analysis
├── config.py                        # Centralized Configuration
│
├── README.md                         # Project Overview
├── README_OLLAMA.md                 # Ollama Setup Guide
├── FILE_STRUCTURE.md                # File Structure Description (This document)
│
└── __pycache__/                      # Python cache files
```

---

## 📝 Detailed File Descriptions

### 📓 Jupyter Notebook

#### `0_FalkorDB_intro.ipynb`
- **Purpose**: FalkorDB introduction and basic usage tutorial
- **Content**: 
  - FalkorDB installation and setup
  - Basic Cypher query examples
  - Introduction to graph data modeling

---

### 🐍 Python Scripts (By Execution Order)

#### `0_generate_data.py` - Generate Data
**Function**: Generates synthetic data related to the battery industry

**Generated Data**:
- **Companies**: Company info (name, country)
  - Real companies: LG Energy Solution, Tesla, CATL, etc.
  - Synthetic companies: Automatically generated company names
- **Technologies**: Technology info (name, category)
  - NCM Battery, LFP Battery, Solid-State Battery, etc.
- **Relations**: Company-Technology relationships (DEVELOPS)

**Configurable Settings**:
```python
NUM_COMPANIES = 20      # Number of companies to generate
NUM_TECHNOLOGIES = 100  # Number of technologies to generate
NUM_RELATIONS = 300     # Number of relations to generate
```

**Execution**:
```bash
python 0_generate_data.py
```

**Output**: Creates 3 CSV files in `data/csv/` directory

---

#### `1_load_to_falkordb.py` - Load to DB
**Function**: Loads CSV data into FalkorDB graph database

**Key Operations**:
1. Connect to FalkorDB (localhost:6379)
2. Delete existing graph (User confirmation required)
3. Create Company nodes
4. Create Technology nodes
5. Create DEVELOPS relationships

**Graph Used**: `EnergyGraph`

**Execution**:
```bash
python 1_load_to_falkordb.py
```

**Notes**: 
- FalkorDB must be running
- Be careful as existing data will be deleted

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
python 2_enrich_graph_data.py
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
4. No DB index created (Data storage only)

**Features**:
- Data preparation for client-side search
- Prevents 'Invalid arguments' errors

**Execution**:
```bash
python 3_create_embeddings.py
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
   - Discover technologies developed by the most companies
2. **PageRank**: Structural influence analysis
   - Uses FalkorDB GraphBLAS engine

**Execution**:
```bash
python 5_analyze_network.py
```

**Output Example**:
```
=== 1. Degree Centrality TOP 5 ===
Rank 1: NCM Battery (8 developers)
Rank 2: LFP Battery (6 developers)
...

=== 2. PageRank (Structural Influence) TOP 5 ===
Rank 1: NCM Battery (Score: 0.125432)
Rank 2: LFP Battery (Score: 0.098765)
...
```

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
