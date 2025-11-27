"""
FalkorDB Guaranteed RAG (Client-Side Search)
============================================
1. DB 인덱스 기능 의존성 제거 (오류 원천 차단)
2. Python 메모리에서 직접 코사인 유사도 계산
3. 확실한 검색 결과 보장
"""

import math
import requests
from falkordb import FalkorDB

# 설정
GRAPH_NAME = 'EnergyGraph'
OLLAMA_URL = 'http://localhost:11434'
EMBED_MODEL = 'nomic-embed-text:latest'
CHAT_MODEL = 'qwen3:8b'

class GuaranteedAgent:
    def __init__(self):
        print(f"🤖 Agent 가동 (Graph: {GRAPH_NAME})")
        self.db = FalkorDB(host='localhost', port=6379)
        self.graph = self.db.select_graph(GRAPH_NAME)
        
        # 전체 노드 데이터 메모리에 캐싱 (속도 최적화)
        print("📥 데이터 로딩 중...", end=" ")
        query = """
        MATCH (n) 
        WHERE n.embedding IS NOT NULL 
        RETURN ID(n), n.name, n.embedding, n.description, labels(n)
        """
        self.cache = self.graph.query(query).result_set
        print(f"✅ {len(self.cache)}개 노드 로드 완료")

    def cosine_similarity(self, v1, v2):
        """Python에서 직접 계산하는 코사인 유사도"""
        dot_product = sum(a*b for a,b in zip(v1, v2))
        magnitude1 = math.sqrt(sum(a*a for a in v1))
        magnitude2 = math.sqrt(sum(b*b for b in v2))
        if magnitude1 == 0 or magnitude2 == 0: return 0
        return dot_product / (magnitude1 * magnitude2)

    def search_memory(self, query_vec, k=5):
        """메모리 내 데이터에서 검색"""
        scores = []
        for row in self.cache:
            node_id, name, embedding, desc, labels = row
            
            # 유사도 계산
            score = self.cosine_similarity(query_vec, embedding)
            scores.append({
                'id': node_id,
                'name': name,
                'desc': desc,
                'score': score,
                'labels': labels
            })
            
        # 점수순 정렬
        scores.sort(key=lambda x: x['score'], reverse=True)
        return scores[:k]

    def ask(self, question):
        print(f"\n💬 질문: {question}")
        
        # 1. 질문 벡터화
        try:
            res = requests.post(f"{OLLAMA_URL}/api/embeddings", 
                              json={"model": EMBED_MODEL, "prompt": question})
            vec = res.json()['embedding']
        except:
            print("❌ 임베딩 실패")
            return

        # 2. Python 내부 검색 (DB 인덱스 안 씀)
        print("🔍 분석 중...")
        top_nodes = self.search_memory(vec, k=5)
        
        if not top_nodes or top_nodes[0]['score'] < 0.4:
            print("⚠️ 관련된 정보를 찾지 못했습니다.")
            # 디버깅용: 1등 점수가 몇 점인지 출력
            if top_nodes:
                print(f"   (최고 유사도: {top_nodes[0]['score']:.4f} - {top_nodes[0]['name']})")
            return

        # 3. 맥락 구성 & 그래프 확장
        context = ""
        for item in top_nodes:
            context += f"\n[검색: {item['name']}] (유사도 {item['score']:.2f})\n"
            context += f" - 설명: {item['desc']}\n"
            
            # DB에 연결 관계만 물어봄 (이건 가벼운 쿼리)
            rel_q = f"MATCH (n)-[r]-(m) WHERE ID(n)={item['id']} RETURN type(r), m.name"
            rel_res = self.graph.query(rel_q)
            
            if rel_res.result_set:
                context += " - 관계 정보:\n"
                for r in rel_res.result_set:
                    context += f"   * (이 항목) --[{r[0]}]--> {r[1]}\n"

        # 4. LLM 답변
        prompt = f"""
        당신은 배터리 산업 전문가 AI입니다. 아래 [Context]를 바탕으로 질문에 한국어로 답변하세요.
        특히 '누가 누구와 협력(COLLABORATES)하는지', '누가 무엇을 개발(DEVELOPS)하는지' 관계를 명확히 서술하세요.
        
        [Context]
        {context}
        
        Question: {question}
        
        Answer (Korean):
        """
        
        print("🧠 답변 생성 중...")
        try:
            final_res = requests.post(f"{OLLAMA_URL}/api/generate", 
                                    json={"model": CHAT_MODEL, "prompt": prompt, "stream": False})
            print("\n" + "="*60)
            print(f"🤖 AI 답변:\n{final_res.json()['response']}")
            print("="*60)
        except:
            print("❌ LLM 통신 실패")

if __name__ == "__main__":
    agent = GuaranteedAgent()
    
    # 질문 테스트
    #agent.ask("Ford와 협력(Collaborate)하는 배터리 회사는?")
    agent.ask("Sodium-Ion 배터리를 개발하는 곳은?")