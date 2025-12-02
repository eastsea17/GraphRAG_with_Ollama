"""
0_generate_research_keywords.py
===============================
Advanced Keyword Extraction & Graph Generation for Scientific Papers.

This script processes scientific papers to build a high-quality knowledge graph.
It uses a Local LLM to extract structured keywords across research dimensions
and connects them based on semantic similarity.

Features:
- 🧠 LLM-based Extraction: Extracts Purpose, Background, Methodology, Results.
- � Paper Hubs: Creates 'Paper' nodes to structurally bind keywords from the same source.
- 🔗 Structural Edges: Connects Paper -> Keywords (e.g., HAS_PURPOSE).
- 🤝 Contextual Similarity: Connects keywords of the SAME TYPE based on cosine similarity.
- 💾 Structured Output: Saves nodes by category and edges with weights.

Usage:
    python 0_generate_research_keywords.py
"""

import pandas as pd
import requests
import json
import os
import time
import re
import numpy as np
import logging
from typing import Dict, List, Set, Any, Optional
from sklearn.metrics.pairwise import cosine_similarity
import config

# --- Configuration & Setup ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

INPUT_FILE = os.path.join(config.RAWDATA_DIR, 'rawdata.csv')
EDGES_OUTPUT = os.path.join(config.CSV_DIR, 'relations.csv')

# Output filenames mapped to JSON keys
CATEGORY_FILES = {
    "Paper": os.path.join(config.CSV_DIR, 'papers.csv'), # New Paper Node File
    "Purpose": os.path.join(config.CSV_DIR, 'research_purpose.csv'),
    "Background": os.path.join(config.CSV_DIR, 'research_background.csv'),
    "Methodology": os.path.join(config.CSV_DIR, 'research_methodology.csv'),
    "Results": os.path.join(config.CSV_DIR, 'research_resultsandeffects.csv')
}

# Ensure output directory exists
os.makedirs(config.CSV_DIR, exist_ok=True)

class LLMClient:
    """Handles communication with Ollama LLM with robustness features."""
    
    def __init__(self, base_url: str, model: str, embed_model: str):
        self.base_url = base_url
        self.model = model
        self.embed_model = embed_model

    def generate(self, prompt: str, retries: int = 3) -> Optional[str]:
        """Generate text with retry logic."""
        for attempt in range(retries):
            try:
                response = requests.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                        "format": "json",
                        "options": {
                            "temperature": 0.1,
                            "num_ctx": 4096
                        }
                    },
                    timeout=120
                )
                response.raise_for_status()
                return response.json()['response']
            except requests.RequestException as e:
                logger.warning(f"LLM generation failed (attempt {attempt+1}/{retries}): {e}")
                time.sleep(2 * (attempt + 1))
        
        logger.error("LLM generation failed after all retries.")
        return None

    def get_embedding(self, text: str) -> Optional[List[float]]:
        """Get vector embedding for text."""
        try:
            response = requests.post(
                f"{self.base_url}/api/embeddings",
                json={
                    "model": self.embed_model,
                    "prompt": text
                },
                timeout=30
            )
            response.raise_for_status()
            return response.json()['embedding']
        except requests.RequestException as e:
            logger.error(f"Embedding generation failed for text '{text[:30]}...': {e}")
            return None

class KeywordExtractor:
    """Main logic for extracting and processing keywords."""
    
    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client
        self.nodes_by_category: Dict[str, List[Dict]] = {key: [] for key in CATEGORY_FILES.keys()}
        self.seen_by_category: Dict[str, Set[str]] = {key: set() for key in CATEGORY_FILES.keys()}
        self.all_unique_nodes: Dict[str, Dict] = {} # Map keyword -> node_data
        self.paper_edges: List[Dict] = [] # Structural edges (Paper -> Keyword)

    def clean_keyword(self, keyword: str) -> str:
        """Normalize keyword: remove extra spaces, special chars, etc."""
        cleaned = keyword.strip().strip('.,;-:').strip()
        if len(cleaned) < 2 or cleaned.isdigit():
            return ""
        return cleaned

    def extract_from_abstract(self, abstract: str) -> Dict[str, List[str]]:
        """Extract categorized keywords from a single abstract."""
        prompt = f"""
        Analyze the following scientific paper abstract and extract key terms (2-5 word n-grams) for each category.
        Focus on specific technical terms, methodologies, and findings.
        
        Categories:
        1. Purpose: What is the main goal or objective?
        2. Background: What is the context, problem, or previous work?
        3. Methodology: What methods, algorithms, or techniques were used?
        4. Results: What are the key findings, effects, or conclusions?

        Return strictly valid JSON with keys: "Purpose", "Background", "Methodology", "Results".
        Values must be lists of strings.
        
        Abstract:
        {abstract}
        """
        
        response_text = self.llm.generate(prompt)
        if not response_text:
            return {}

        try:
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0]
            elif "```" in response_text:
                response_text = response_text.split("```")[0]
            
            data = json.loads(response_text)
            return data
        except json.JSONDecodeError:
            logger.error(f"Failed to parse JSON. Raw response: {response_text[:100]}...")
            return {}

    def process_dataframe(self, df: pd.DataFrame):
        """Process all rows in the dataframe."""
        total = len(df)
        logger.info(f"Starting extraction for {total} papers...")
        
        for index, row in df.iterrows():
            abstract = row.get('abstract', '')
            if not isinstance(abstract, str) or len(abstract) < 20:
                continue
                
            logger.info(f"[{index+1}/{total}] Processing paper...")
            
            # 1. Create Paper Node
            paper_id = f"Paper_{index+1}"
            paper_title = abstract[:50] + "..." # Use first 50 chars as title/label if no title column
            
            self.nodes_by_category["Paper"].append({
                'Id': paper_id,
                'Label': paper_title,
                'Type': 'Paper',
                'Full_Text': abstract[:200] # Store snippet
            })
            
            # 2. Extract Keywords
            extracted_data = self.extract_from_abstract(abstract)
            
            for category, keywords in extracted_data.items():
                if category not in CATEGORY_FILES or not isinstance(keywords, list):
                    continue
                    
                for kw in keywords:
                    if not isinstance(kw, str): continue
                    
                    clean_kw = self.clean_keyword(kw)
                    if not clean_kw: continue
                    
                    # Add to Category List (if unique for this category)
                    if clean_kw not in self.seen_by_category[category]:
                        self.seen_by_category[category].add(clean_kw)
                        self.nodes_by_category[category].append({
                            'Id': clean_kw,
                            'Label': clean_kw,
                            'Type': category
                        })
                    
                    # Add to Master List (for embeddings)
                    if clean_kw not in self.all_unique_nodes:
                        self.all_unique_nodes[clean_kw] = {
                            'Id': clean_kw,
                            'Label': clean_kw,
                            'Type': category
                        }
                        
                    # 3. Create Structural Edge (Paper -> Keyword)
                    # Relationship type depends on category (e.g., HAS_PURPOSE)
                    rel_type = f"HAS_{category.upper()}"
                    self.paper_edges.append({
                        'Source': paper_id,
                        'Target': clean_kw,
                        'Type': rel_type,
                        'Weight': 1.0
                    })

    def save_nodes(self):
        """Save node CSVs."""
        logger.info("Saving node CSV files...")
        for category, filepath in CATEGORY_FILES.items():
            nodes = self.nodes_by_category[category]
            if nodes:
                pd.DataFrame(nodes).to_csv(filepath, index=False)
                logger.info(f"  - Saved {len(nodes)} {category} nodes to {os.path.basename(filepath)}")
            else:
                logger.warning(f"  - No nodes found for {category}")

    def generate_edges(self, threshold: float = 0.5):
        """Generate similarity edges (Inter-paper) and combine with structural edges."""
        
        # 1. Structural Edges (Already collected)
        all_edges = self.paper_edges.copy()
        logger.info(f"Collected {len(all_edges)} structural edges (Paper -> Keyword).")
        
        # 2. Similarity Edges (Keyword <-> Keyword, SAME TYPE ONLY)
        # We process each category separately to ensure type constraints
        
        categories_to_process = ["Purpose", "Background", "Methodology", "Results"]
        
        for category in categories_to_process:
            nodes = self.nodes_by_category[category]
            count = len(nodes)
            
            if count < 2:
                continue
                
            logger.info(f"Generating embeddings for {count} {category} nodes...")
            
            embeddings = []
            valid_nodes = []
            
            # Generate Embeddings
            for i, node in enumerate(nodes):
                if i % 50 == 0:
                    print(f"  {category} embedding: {i}/{count}", end='\r')
                
                # Check cache or generate? (For now, generate fresh or rely on LLMClient caching if implemented)
                # To be efficient, we should use the cache from previous runs if possible, 
                # but here we just generate.
                emb = self.llm.get_embedding(node['Id'])
                if emb:
                    embeddings.append(emb)
                    valid_nodes.append(node)
            
            print(f"  {category} embedding: {count}/{count}")
            
            if len(embeddings) < 2:
                continue
                
            # Calculate Similarity
            matrix = np.array(embeddings)
            sim_matrix = cosine_similarity(matrix)
            
            # Create Edges
            sim_edges_count = 0
            for i in range(len(valid_nodes)):
                for j in range(i + 1, len(valid_nodes)):
                    sim = sim_matrix[i][j]
                    if sim >= threshold:
                        all_edges.append({
                            'Source': valid_nodes[i]['Id'],
                            'Target': valid_nodes[j]['Id'],
                            'Weight': float(sim),
                            'Type': 'RELATED_TO' # Or SIMILAR_PURPOSE, etc.
                        })
                        sim_edges_count += 1
            
            logger.info(f"  - Generated {sim_edges_count} similarity edges for {category}")

        # Save All Edges
        logger.info(f"Total edges to save: {len(all_edges)}")
        pd.DataFrame(all_edges).to_csv(EDGES_OUTPUT, index=False)
        logger.info(f"Saved edges to {os.path.basename(EDGES_OUTPUT)}")

def main():
    # 1. Load Data
    if not os.path.exists(INPUT_FILE):
        logger.error(f"Input file not found: {INPUT_FILE}")
        return

    df = pd.read_csv(INPUT_FILE)
    
    # Optional: Limit rows for testing
    if config.MAX_ROWS_FOR_EXTRACTION:
        df = df.head(config.MAX_ROWS_FOR_EXTRACTION)
        logger.info(f"Limiting processing to first {config.MAX_ROWS_FOR_EXTRACTION} rows.")

    # 2. Initialize Components
    llm_client = LLMClient(config.OLLAMA_URL, config.LLM_MODEL, config.EMBED_MODEL)
    extractor = KeywordExtractor(llm_client)
    
    # 3. Run Pipeline
    extractor.process_dataframe(df)
    extractor.save_nodes()
    extractor.generate_edges(threshold=0.5)
    
    logger.info("✅ Graph generation complete!")

if __name__ == "__main__":
    main()
