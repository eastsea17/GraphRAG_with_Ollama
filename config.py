"""
Centralized Configuration for FalkorDB and Ollama Scripts
"""
import os

# FalkorDB Settings
GRAPH_NAME = 'Paper_Keywords2'
FALKORDB_HOST = 'localhost'
FALKORDB_PORT = 6379

# Ollama Settings
OLLAMA_URL = 'http://localhost:11434'

# Model Settings
#GRAPH_GENERATION_MODEL = 'gpt-oss:20b'  # Used for schema discovery and entity extraction
GRAPH_GENERATION_MODEL = 'gpt-oss:20b'  # Used for schema discovery and entity extraction
LLM_MODEL = 'deepseek-r1:8b'  # Used for enrichment and chat
CHAT_MODEL = 'deepseek-r1:8b' # Used for RAG chat
EMBED_MODEL = 'nomic-embed-text:latest' # Used for embeddings

# Data Paths
CSV_DIR = 'data/csv'
EMBEDDING_DIR = 'data/embedding'
CACHE_FILE = 'embeddings_cache.json'

# Graph Generation Settings
RAWDATA_DIR = 'Rawdata'
SUPPORTED_FORMATS = ['.csv']
SCHEMA_OUTPUT = 'data/schema.json'

# LLM Prompting Settings
MAX_TOKENS = 4096  # Increased for reasoning models (e.g. deepseek-r1) = 12000
TEMPERATURE = 0.7
SCHEMA_DISCOVERY_RETRIES = 3
BATCH_SIZE = 7  # Number of rows to process at once
MAX_NODE_TYPES = 2  # Limit number of node types for faster extraction
MAX_EDGE_TYPES = 2  # Limit number of edge types for faster extraction
MAX_ROWS_FOR_EXTRACTION = None  # Only process first N rows (set to None for all)
MAX_TEXT_LENGTH = 200  # Maximum characters per field when extracting entities (longer text will be truncated)

