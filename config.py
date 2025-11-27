"""
Centralized Configuration for FalkorDB and Ollama Scripts
"""
import os

# FalkorDB Settings
GRAPH_NAME = 'EnergyGraph'
FALKORDB_HOST = 'localhost'
FALKORDB_PORT = 6379

# Ollama Settings
OLLAMA_URL = 'http://localhost:11434'

# Model Settings
LLM_MODEL = 'deepseek-r1:8b'  # Used for enrichment and chat
CHAT_MODEL = 'deepseek-r1:8b' # Used for RAG chat
EMBED_MODEL = 'nomic-embed-text:latest' # Used for embeddings

# Data Paths
CSV_DIR = 'data/csv'
EMBEDDING_DIR = 'data/embedding'
CACHE_FILE = 'embeddings_cache.json'
