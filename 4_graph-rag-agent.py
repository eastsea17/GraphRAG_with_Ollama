"""
FalkorDB Interactive GraphRAG Agent
===================================
1. Removes DB index dependency (100% guaranteed operation)
2. User interactive interface (Interactive CLI)
3. Type 'exit' to quit
"""

import math
import sys
import requests
from falkordb import FalkorDB
import config

class GraphRAGAgent:
    def __init__(self):
        print("=" * 60)
        print(f"🤖 Initializing Energy Solution Agent... (Graph: {config.GRAPH_NAME})")
        
        try:
            self.db = FalkorDB(host=config.FALKORDB_HOST, port=config.FALKORDB_PORT)
            self.graph = self.db.select_graph(config.GRAPH_NAME)
        except Exception as e:
            print(f"❌ DB Connection Failed: {e}")
            sys.exit(1)
        
        # Cache all node data in memory (Client-Side Search)
        print("📥 Loading knowledge data (Client-side Cache)...", end=" ")
        try:
            query = """
            MATCH (n) 
            WHERE n.embedding IS NOT NULL 
            RETURN ID(n), n.name, n.embedding, n.description, labels(n)
            """
            self.cache = self.graph.query(query).result_set
            print(f"✅ {len(self.cache)} nodes loaded")
        except Exception as e:
            print(f"\n❌ Data loading failed: {e}")
            print("💡 Hint: Run '3_create_embeddings.py' first to populate data.")
            sys.exit(1)

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
        # 1. Vectorize question
        try:
            res = requests.post(f"{config.OLLAMA_URL}/api/embeddings", 
                              json={"model": config.EMBED_MODEL, "prompt": question})
            vec = res.json()['embedding']
        except Exception as e:
            print(f"❌ Embedding generation failed: {e}")
            return

        # 2. Python internal search
        print("🔍 Analyzing knowledge graph...", end="\r")
        top_nodes = self.search_memory(vec, k=5)
        
        if not top_nodes or top_nodes[0]['score'] < 0.35:
            print("⚠️ No relevant information found in the database.")
            return

        # 3. Construct Context & Expand Graph
        context = ""
        for item in top_nodes:
            context += f"\n[Search Item: {item['name']}] (Relevance {item['score']:.2f})\n"
            context += f" - Description: {item['desc']}\n"
            
            # Query relationships in DB
            rel_q = f"MATCH (n)-[r]-(m) WHERE ID(n)={item['id']} RETURN type(r), m.name"
            rel_res = self.graph.query(rel_q)
            
            if rel_res.result_set:
                context += " - Network Relationships:\n"
                for r in rel_res.result_set:
                    # Relation name (r[0]) and target (r[1])
                    context += f"   * (This) --[{r[0]}]--> {r[1]}\n"

        # 4. LLM Answer
        prompt = f"""
        You are an 'Energy Solution Strategist' AI.
        Answer the user's question in English based on the provided [Context].
        
        Rules:
        1. Based on the 'Network Relationships' in the Context, clearly state who collaborates with whom and who develops what.
        2. Do not fabricate information not present in the Context.
        
        [Context]
        {context}
        
        Question: {question}
        
        Answer (English):
        """
        
        print("🧠 Generating answer...           ", end="\r")
        try:
            final_res = requests.post(f"{config.OLLAMA_URL}/api/generate", 
                                    json={"model": config.CHAT_MODEL, "prompt": prompt, "stream": False})
            
            print(" " * 30, end="\r") # Clear status message
            print("\n" + "="*60)
            print(f"🤖 Agent Answer:\n{final_res.json()['response'].strip()}")
            print("="*60)
        except Exception as e:
            print(f"❌ LLM communication failed: {e}")

# ==========================================
# ▶️ Main Execution (Chat Loop)
# ==========================================
if __name__ == "__main__":
    agent = GraphRAGAgent()
    
    print("\n💬 Conversation started. (Type 'exit' or 'q' to quit)")
    print("-" * 60)
    
    while True:
        try:
            user_input = input("\n>> Enter question: ").strip()
            
            if not user_input:
                continue
                
            if user_input.lower() in ['exit', 'quit', 'q']:
                print("👋 Exiting program.")
                break
            
            agent.ask(user_input)
            
        except KeyboardInterrupt:
            print("\n👋 Exiting program.")
            break