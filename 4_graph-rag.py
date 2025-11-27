"""
FalkorDB Guaranteed RAG (Client-Side Search)
============================================
1. Removes DB index dependency (Eliminates errors)
2. Cosine similarity calculated directly in Python memory
3. Guaranteed search results
"""

import math
import requests
from falkordb import FalkorDB

# Settings
GRAPH_NAME = 'EnergyGraph'
OLLAMA_URL = 'http://localhost:11434'
EMBED_MODEL = 'nomic-embed-text:latest'
#CHAT_MODEL = 'qwen3:8b'
#CHAT_MODEL = 'deepseek-r1:8b'
CHAT_MODEL = 'gpt-oss:20b'

class GuaranteedAgent:
    def __init__(self):
        print(f"🤖 Agent Running (Graph: {GRAPH_NAME})")
        self.db = FalkorDB(host='localhost', port=6379)
        self.graph = self.db.select_graph(GRAPH_NAME)
        
        # Cache all node data in memory (Speed optimization)
        print("📥 Loading data...", end=" ")
        query = """
        MATCH (n) 
        WHERE n.embedding IS NOT NULL 
        RETURN ID(n), n.name, n.embedding, n.description, labels(n)
        """
        self.cache = self.graph.query(query).result_set
        print(f"✅ {len(self.cache)} nodes loaded")

    def cosine_similarity(self, v1, v2):
        """Cosine similarity calculated directly in Python"""
        dot_product = sum(a*b for a,b in zip(v1, v2))
        magnitude1 = math.sqrt(sum(a*a for a in v1))
        magnitude2 = math.sqrt(sum(b*b for b in v2))
        if magnitude1 == 0 or magnitude2 == 0: return 0
        return dot_product / (magnitude1 * magnitude2)

    def search_memory(self, query_vec, k=5):
        """Search within in-memory data"""
        scores = []
        for row in self.cache:
            node_id, name, embedding, desc, labels = row
            
            # Calculate similarity
            score = self.cosine_similarity(query_vec, embedding)
            scores.append({
                'id': node_id,
                'name': name,
                'desc': desc,
                'score': score,
                'labels': labels
            })
            
        # Sort by score
        scores.sort(key=lambda x: x['score'], reverse=True)
        return scores[:k]

    def ask(self, question):
        print(f"\n💬 Question: {question}")
        
        # 1. Vectorize question
        try:
            res = requests.post(f"{OLLAMA_URL}/api/embeddings", 
                              json={"model": EMBED_MODEL, "prompt": question})
            vec = res.json()['embedding']
        except:
            print("❌ Embedding failed")
            return

        # 2. Python internal search (No DB index used)
        print("🔍 Analyzing...")
        top_nodes = self.search_memory(vec, k=5)
        
        if not top_nodes or top_nodes[0]['score'] < 0.4:
            print("⚠️ No relevant information found.")
            # Debugging: Print top score
            if top_nodes:
                print(f"   (Top similarity: {top_nodes[0]['score']:.4f} - {top_nodes[0]['name']})")
            return

        # 3. Construct Context & Expand Graph
        context = ""
        for item in top_nodes:
            context += f"\n[Search: {item['name']}] (Similarity {item['score']:.2f})\n"
            context += f" - Description: {item['desc']}\n"
            
            # Query only relationships from DB (Lightweight query)
            rel_q = f"MATCH (n)-[r]-(m) WHERE ID(n)={item['id']} RETURN type(r), m.name"
            rel_res = self.graph.query(rel_q)
            
            if rel_res.result_set:
                context += " - Relationships:\n"
                for r in rel_res.result_set:
                    context += f"   * (This) --[{r[0]}]--> {r[1]}\n"

        # 4. LLM Answer
        prompt = f"""
        You are a battery industry expert AI. Answer the question in English based on the [Context] below.
        Specifically, clearly describe relationships such as 'who COLLABORATES with whom' and 'who DEVELOPS what'.
        
        [Context]
        {context}
        
        Question: {question}
        
        Answer (English):
        """
        
        print("🧠 Generating answer...")
        try:
            final_res = requests.post(f"{OLLAMA_URL}/api/generate", 
                                    json={"model": CHAT_MODEL, "prompt": prompt, "stream": False})
            print("\n" + "="*60)
            print(f"🤖 AI Answer:\n{final_res.json()['response']}")
            print("="*60)
        except:
            print("❌ LLM Communication Failed")

if __name__ == "__main__":
    agent = GuaranteedAgent()
    
    # Question Test
    #agent.ask("Which battery companies collaborate with Ford?")
    #agent.ask("Who develops Sodium-Ion batteries?")
    #agent.ask("Which companies develop LFP batteries?")
    #agent.ask("What kind of company is CATL?")
    agent.ask("Which car companies are collaborating with CATL?")