# GraphRAG Auto-Generation System

## 📖 Overview

The `0_graph_schema_discovery.py` script automatically analyzes raw data files and generates Node/Edge CSV files for GraphRAG construction using LLM intelligence.

## 🌟 Key Features

- **LLM-Driven Analysis**: Automatic topic identification and domain understanding
- **Schema Discovery**: Intelligent Node/Edge type generation
- **Entity Extraction**: Automated extraction of entities and relationships
- **Pipeline Integration**: Generates CSV files compatible with existing FalkorDB pipeline

## 🏗️ Architecture

```
0_graph_schema_discovery.py (Main Orchestrator)
    ├── graph_generator/
    │   ├── data_loader.py        # Multi-format file loading
    │   ├── llm_interface.py      # Ollama LLM communication
    │   ├── schema_extractor.py   # Schema discovery & validation
    │   ├── entity_extractor.py   # Entity & relationship extraction
    │   └── csv_generator.py      # CSV file generation
    └── config.py                  # Configuration settings
```

## 🚀 Usage

### Basic Usage

Process the first file found in `Rawdata/`:

```bash
python 0_graph_schema_discovery.py
```

### Process Specific File

```bash
python 0_graph_schema_discovery.py --file Rawdata/mycustom_data.csv
```

### Validate Existing Schema

```bash
python 0_graph_schema_discovery.py --validate-schema
```

### Use Existing Schema

Skip schema discovery and use a previously saved schema:

```bash
python 0_graph_schema_discovery.py --use-schema data/schema.json
```

### Custom Output Directory

```bash
python 0_graph_schema_discovery.py --output-dir custom_output/
```

## 📊 Workflow

### 1. Data Loading
- Loads raw data from supported formats
- Extracts both structured and unstructured content
- Generates metadata about the source

### 2. Schema Discovery
- **Topic Analysis**: LLM identifies domain and main topics
- **Structure Analysis**: Analyzes columns and row meanings (New!)
- **Node Type Generation**: Creates 2-5 Node types with attributes
- **Edge Type Generation**: Defines relationships between Node types
- **Schema Validation**: Ensures consistency and completeness

### 3. Entity Extraction
- **Batch Processing**: Processes data in configurable batches
- **Node Extraction**: Extracts entities for each Node type
- **Deduplication**: Removes duplicate entities
- **Relationship Inference**: Discovers edges between nodes

### 4. CSV Generation
- **Node CSVs**: One file per Node type (e.g., `papers.csv`, `concepts.csv`)
- **Relations CSV**: Single `relations.csv` with edges (START_ID, END_ID, TYPE format)
- **Validation**: Ensures FalkorDB compatibility

## 📁 Output Structure

```
data/
├── schema.json           # Discovered graph schema
└── csv/
    ├── node_type_1.csv  # Node CSV files
    ├── node_type_2.csv
    └── relations.csv    # Edge relationships
```

## ⚙️ Configuration

Edit `config.py` to customize:

```python
# Graph Generation Settings
RAWDATA_DIR = 'Rawdata'
SUPPORTED_FORMATS = ['.csv', '.xlsx', '.docx', '.pdf', '.txt']
SCHEMA_OUTPUT = 'data/schema.json'

# Model Settings
GRAPH_GENERATION_MODEL = 'gpt-oss:20b'  # LLM model for graph generation

# LLM Prompting Settings
MAX_TOKENS = 4096
TEMPERATURE = 0.7
SCHEMA_DISCOVERY_RETRIES = 3

# Performance Optimization Settings
BATCH_SIZE = 10                      # Number of rows to process at once
MAX_NODE_TYPES = 3                   # Limit number of node types
MAX_EDGE_TYPES = 3                   # Limit number of edge types
MAX_ROWS_FOR_EXTRACTION = None       # Process first N rows (None = all rows)
MAX_TEXT_LENGTH = 200                # Truncate long text fields to N characters
```

### Key Settings Explained

- **BATCH_SIZE**: Larger = faster but more memory usage
- **MAX_NODE_TYPES**: Smaller = simpler schema, faster extraction
- **MAX_EDGE_TYPES**: Smaller = fewer relationships, faster processing
- **MAX_ROWS_FOR_EXTRACTION**: Set to small number (e.g., 20) for quick testing
- **MAX_TEXT_LENGTH**: Truncate abstracts/long text to speed up LLM processing

## 🔗 Integration with Existing Pipeline

After generating CSVs:

```bash
# 1. Generate graph from raw data
python 0_graph_schema_discovery.py

# 2. Load into FalkorDB
python 1_load_to_falkordb.py

# 3. Enrich with LLM
python 2_enrich_graph_data.py --full

# 4. Create embeddings
python 3_create_embeddings.py

# 5. Query with RAG
python 4_graph_rag.py --query "What are the main concepts?"
```

## 📋 Example: Academic Papers

Given `Rawdata/rawdata.csv` containing academic papers about ontologies:

### Schema Discovery Output
```json
{
  "nodes": [
    {
      "type": "Paper",
      "description": "Academic research paper",
      "attributes": ["title", "year", "authors", "url"]
    },
    {
      "type": "Concept",
      "description": "Key technical concept or method",
      "attributes": ["name", "category"]
    },
    {
      "type": "Author",
      "description": "Researcher or author",
      "attributes": ["name", "institution"]
    }
  ],
  "edges": [
    {
      "type": "MENTIONS",
      "description": "Paper discusses concept",
      "from_node": "Paper",
      "to_node": "Concept"
    },
    {
      "type": "AUTHORED_BY",
      "description": "Paper written by author",
      "from_node": "Paper",
      "to_node": "Author"
    }
  ]
}
```

### Generated Files
- `data/csv/paper.csv` - 162 papers
- `data/csv/concept.csv` - 45 unique concepts
- `data/csv/author.csv` - 320 unique authors
- `data/csv/relations.csv` - 1,754 relationships

## 🛠️ Dependencies

Required Python packages:

```bash
pip install requests falkordb openpyxl python-docx PyPDF2
```

## 🐛 Troubleshooting

### LLM Connection Issues
```
❌ LLM API error: Connection refused
```
**Solution**: Ensure Ollama is running:
```bash
ollama serve
ollama pull gpt-oss:20b
```

### Schema Discovery Fails
```
❌ Failed to discover schema after retries
```
**Solution**: 
- Check LLM model is loaded: `ollama list`
- Increase retries in `config.py`: `SCHEMA_DISCOVERY_RETRIES = 5`
- Use higher capability model
- Reduce data complexity: `MAX_TEXT_LENGTH = 100`

### No Entities Extracted
```
⚠️ Warning: Expected list, got dict
```
**Solution**: 
- LLM output format issue
- Try smaller `BATCH_SIZE` in `config.py` (try 5)
- Simplify schema (fewer attributes)
- Reduce `MAX_TEXT_LENGTH` to 150

### Processing Too Slow
```
Batch processing taking too long...
```
**Solution**:
- Reduce `MAX_ROWS_FOR_EXTRACTION` to 20-50 for testing
- Decrease `MAX_TEXT_LENGTH` to 100-150
- Use smaller, faster model (e.g., `llama3.2:3b`)
- Reduce `BATCH_SIZE` to 5

### Out of Memory
```
❌ Error: OutOfMemoryError
```
**Solution**:
- Reduce `BATCH_SIZE` to 3-5
- Set `MAX_ROWS_FOR_EXTRACTION = 50`
- Use smaller model
- Reduce `MAX_TEXT_LENGTH` to 100

## 📝 Schema File Format

The `data/schema.json` file stores the discovered schema:

```json
{
  "nodes": [
    {
      "type": "NodeTypeName",
      "description": "What this represents",
      "attributes": ["attr1", "attr2", "attr3"]
    }
  ],
  "edges": [
    {
      "type": "EDGE_TYPE",
      "description": "Relationship meaning",
      "from_node": "SourceType",
      "to_node": "TargetType"
    }
  ],
  "metadata": {
    "domain": "Domain description",
    "topics": ["topic1", "topic2"],
    "source_file": "filename.csv"
  }
}
```

## 🎯 Tips for Best Results

1. **Start Small**: Set `MAX_ROWS_FOR_EXTRACTION = 20` for initial testing
2. **Clean Data**: Remove unnecessary columns/rows from raw data
3. **Descriptive Headers**: Use clear column names in CSV/Excel files
4. **Tune Text Length**: Adjust `MAX_TEXT_LENGTH` based on your data
   - Short summaries (100-150): Faster processing
   - Full abstracts (300-500): Better accuracy
5. **Schema Simplicity**: Keep `MAX_NODE_TYPES` and `MAX_EDGE_TYPES` at 3 initially
6. **Review Schema**: Always review `data/schema.json` before full extraction
7. **Batch Size**: Smaller batch size (5-10) = more stable, larger (15-20) = faster
8. **Model Selection**: Larger models (20b+) are more accurate but slower

## 🔮 Future Enhancements

- [ ] Multi-file batch processing
- [ ] Interactive schema refinement
- [ ] Schema templates for common domains
- [ ] Quality metrics and validation
- [ ] Incremental graph updates

## 📚 Related Files

- **Auto Generation**: `0_graph_schema_discovery.py` - LLM-driven automatic generation (any domain)
- **Keyword Extraction**: `0_generate_research_keywords.py` - Scientific Paper Analysis
  - **Sophisticated Graph Structure**: Paper Hubs + Structural Edges + Constrained Similarity
  - Extracts Purpose, Background, Methodology, Results
  - Creates `(Paper)-[:HAS_PURPOSE]->(Purpose)` structural edges
  - Creates `(Purpose)-[:RELATED_TO]->(Purpose)` semantic edges (Same-type only)
  - See `README.md` for usage details
