# 🎉 100% Ollama-based GraphRAG System

## ✅ Final Configuration

**A completely free system where every step operates 100% on Ollama!**

| Step | Script | Model Used | Cost |
|-----|---------|----------|------|
| 1️⃣ Load to DB | `1_load_to_falkordb.py` | - | Free |
| 2️⃣ **Generate Descriptions** | `2_enrich_graph_data.py` | **deepseek-r1:8b** | **Free** ✨ |
| 3️⃣ **Create Embeddings** | `3_create_embeddings.py` | **nomic-embed-text** | **Free** ✨ |
| 4️⃣ **GraphRAG Query** | `4_graph-rag.py` | **nomic-embed-text + deepseek-r1:8b** | **Free** ✨ |
| 5️⃣ Network Analysis | `5_analyze_network.py` | - | Free |

## 🚀 Completely Free Execution Guide

### 1. Install Ollama and Download Models

```bash
# Install Ollama (macOS)
brew install ollama

# Start Ollama Server
ollama serve

# Download required models
ollama pull deepseek-r1:8b             # LLM (4.9GB)
ollama pull nomic-embed-text     # Embedding (274MB)
```

### 2. Run FalkorDB

```bash
docker run -p 6379:6379 -p 3001:3000 -it --rm \
  -v ./data:/var/lib/falkordb/data \
  falkordb/falkordb
```

### 3. Run Full Pipeline

```bash
# Step 1: Load to FalkorDB (default: EnergyGraph)
python 1_load_to_falkordb.py
# Or specify graph name:
# python 1_load_to_falkordb.py --graph Paper_Keywords

# Step 2: Generate Node Descriptions (Ollama LLM - Free!)
python 2_enrich_graph_data.py
# Or for specific graph:
# python 2_enrich_graph_data.py --graph Paper_Keywords

# Step 3: Create Vector Embeddings (Ollama Embedding - Free!)
python 3_create_embeddings.py
# Or for specific graph:
# python 3_create_embeddings.py --graph Paper_Keywords

# Step 4: GraphRAG Query System (Ollama - Free!)
python 4_graph-rag.py

# Step 5: Network Analysis (PageRank, Degree Centrality)
python 5_analyze_network.py
# Or for specific graph:
# python 5_analyze_network.py --graph Paper_Keywords
```

## 💰 Cost Analysis

| Item | Cost |
|------|------|
| LLM Description Generation | **Free** |
| Embedding Generation | **Free** |
| Cost per Query | **Free** |
| **Total Cost** | **$0** 🎉 |

## 🎯 System Features

### Advantages
- ✅ **Completely Free** - No API costs at all
- ✅ **Data Privacy** - All data remains local
- ✅ **Offline Execution** - No internet required (after model download)
- ✅ **Excellent Korean Support** - qwen3 has excellent Korean performance
- ✅ **Customizable** - Easily swap with desired models
- ✅ **Graph Analysis** - Network analysis features like PageRank, Centrality

### System Requirements
- **RAM**: 16GB or more (24GB recommended)
- **Disk**: Approx. 5-6GB (Models)
- **CPU/GPU**: Automatically utilizes M4 Pro's Metal GPU
- **Docker**: Required to run FalkorDB

## 📊 Performance

### Speed (Based on M4 Pro)
- **Data Generation**: ~1 sec (20 companies, 100 technologies, 300 relations)
- **DB Load**: ~5-10 sec
- **Description Generation**: ~2-3 sec/node
- **Embedding Generation**: ~0.1-0.5 sec/node
- **GraphRAG Query**: ~3-5 sec/question

### Quality
- **Description Accuracy**: Generates descriptions suitable for the industrial domain
- **Search Accuracy**: Accurate search based on cosine similarity
- **Answer Quality**: Faithfully reflects the battery industry context

## 🔧 Changing Models

Easily switch to any desired Ollama model by modifying `config.py`:

**`config.py`:**
```python
# LLM Model (Description & Answer Generation)
LLM_MODEL = 'deepseek-r1:8b'  # Default
# LLM_MODEL = 'llama3.1:8b'   # Strong in English
# LLM_MODEL = 'gemma2:9b'     # Google model
# LLM_MODEL = 'qwen2.5:14b'   # Better performance (Requires more RAM)

# Chat Model (RAG Chat)
CHAT_MODEL = 'deepseek-r1:8b'

# Embedding Model
EMBED_MODEL = 'nomic-embed-text:latest'  # Default
# EMBED_MODEL = 'mxbai-embed-large'  # 1024 dimensions
# EMBED_MODEL = 'all-minilm'         # 384 dimensions, fast
```

## 📝 File Structure

```
251125_FalkorDB/
├── data/
│   ├── csv/                       # CSV Data
│   │   ├── companies.csv          # Company info (name, country)
│   │   ├── technologies.csv       # Technology info (name, category)
│   │   ├── keyword.csv            # Keyword nodes (from papers)
│   │   └── relations.csv          # Relationship info (START_ID, END_ID, TYPE)
│   ├── schema.json                # Graph schema
│   └── embedding/                 # Embedding cache
│
├── Rawdata/
│   └── rawdata.csv                # Raw scientific papers
│
├── 0_FalkorDB_intro.ipynb        # FalkorDB Intro & Tutorial
│
├── 0_graph_schema_discovery.py           # Auto Graph Generation (LLM)
├── 0_generate_research_keywords.py          # Paper Keyword Extraction (LLM)
├── 1_load_to_falkordb.py         # CSV → Load to FalkorDB (--graph support)
├── 2_enrich_graph_data.py        # Generate Node Descriptions with LLM (--graph support)
├── 3_create_embeddings.py        # Create Vector Embeddings (--graph support)
├── 4_graph-rag.py                # GraphRAG Query System (Ollama)
├── 5_analyze_network.py          # Network Analysis (--graph support)
├── config.py                     # Centralized Configuration
│
├── README.md                      # Project Overview
├── README_OLLAMA.md              # Ollama Guide (This Document)
├── GRAPH_GENERATOR_README.md     # Graph Generator Guide
└── FILE_STRUCTURE.md             # File Structure Description
```

## 🎬 Usage Examples

### GraphRAG Query (4_graph-rag-agent.py)
 
 ```bash
 $ python 4_graph-rag-agent.py
 
 🤖 Initializing Research Agent... (Graph: Paper_Keywords2)
 📥 Loading knowledge data (Client-side Cache)... ✅ 1495 nodes loaded
 
 💬 Question: what purposes are for patent citation analysis?
 🔍 Analyzing...
 🧠 Generating answer...
 
 ============================================================
 🤖 Agent Answer:
 Patent citation analysis serves several key purposes:
 1. **Identifying Key Players**: Finding influential companies or institutions.
 2. **Technology Forecasting**: Predicting future technology trends.
 ...
 ------------------------------------------------------------
 🔍 Source Context (Top 3 Nodes & Edges):
 
 1. Node: Patent Citation Analysis (Score: 0.85)
    Edges:
    - [HAS_PURPOSE] -> Identifying Key Players
    - [RELATED_TO] -> Technology Forecasting
 
 2. Node: Technology Intelligence (Score: 0.78)
 ...
 ============================================================
 ```

### Network Analysis (5_analyze_network.py)

```bash
$ python 5_analyze_network.py

=== 1. Degree Centrality TOP 5 ===
Finding technologies with the most developing companies.
Rank 1: NCM Battery (8 developers)
Rank 2: LFP Battery (6 developers)
...

=== 2. PageRank (Structural Influence) TOP 5 ===
Calculating PageRank using FalkorDB's algorithm engine (GraphBLAS).
Rank 1: NCM Battery (Score: 0.125432)
Rank 2: LFP Battery (Score: 0.098765)
...
```

## 🚨 Troubleshooting

### Ollama Server Connection Failed
```bash
# Start Server
ollama serve

# Run in Background
nohup ollama serve &

# Check Server Status
curl http://localhost:11434/api/tags
```

### Model Not Found Error
```bash
# Download Models
ollama pull deepseek-r1:8b
ollama pull nomic-embed-text

# Check Installed Models
ollama list
```

### FalkorDB Connection Failed
```bash
# Check FalkorDB Execution
docker ps | grep falkordb

# Restart FalkorDB
docker run -p 6379:6379 -p 3001:3000 -it --rm \
  -v ./data:/var/lib/falkordb/data \
  falkordb/falkordb
```

### Out of Memory
- Use smaller models: `deepseek-r1:1.5b` or `llama3.2:1b`
- Close other programs
- Reduce number of nodes (Modify settings in 0_generate_data.py)

### Slow Speed
- Check GPU: `ollama ps` (Check if Metal is being used)
- Reduce model size
- Increase batch size (Modify scripts)

## 📚 References

- [Ollama Official Site](https://ollama.ai/)
- [DeepSeek Model Documentation](https://github.com/deepseek-ai/DeepSeek-LLM)
- [Nomic Embed Text](https://www.nomic.ai/blog/posts/nomic-embed-text-v1)
- [FalkorDB Documentation](https://docs.falkordb.com/)
- [GraphBLAS Algorithms](https://docs.falkordb.com/graph_algorithms.html)

## 🔍 Key Features Detail

### 1. Graph Data Enrichment (2_enrich_graph_data.py)
- Automatically generates descriptions for each node using Ollama LLM
- Technology: Technical features, uses, pros/cons description
- Company: Company info, main business, characteristics description

### 2. Vector Embeddings (3_create_embeddings.py)
- Converts text → vector using Ollama embedding API
- No DB index required (Stores data only)
- Memory-efficient processing

### 3. GraphRAG (4_graph-rag.py / 4_graph-rag-agent.py)
- **Guaranteed RAG**: Removes DB index dependency
- **Transparent Agent**: Explicitly displays **Source Context** (Top 3 Nodes & Edges)
- Direct cosine similarity calculation within Python
- Automatic expansion of graph relationship information
- Accurate answer generation based on context

### 4. Network Analysis (5_analyze_network.py)
- Degree Centrality: Importance based on connection count
- PageRank: Structural influence analysis (GraphBLAS)

---

**Use a powerful GraphRAG system completely for free!** 🚀
