"""
Step 4: Create Embeddings (Data Only)
=====================================
이 스크립트는 FalkorDB의 노드(Company, Technology)에 
벡터 임베딩(Vector Embedding) 데이터를 생성하여 저장합니다.

* 특징:
- DB 내부 Index를 만들지 않으므로 'Invalid arguments' 에러가 발생하지 않습니다.
- 순수하게 데이터(embedding 속성)만 채워 넣습니다.
- 이후 'Guaranteed RAG' 스크립트가 이 데이터를 읽어서 검색합니다.
"""

import time
import requests
from falkordb import FalkorDB

# ==========================================
# ⚙️ 설정 (사용자 환경에 맞게 수정 가능)
# ==========================================
GRAPH_NAME = 'EnergyGraph'
OLLAMA_URL = 'http://localhost:11434'
EMBED_MODEL = 'nomic-embed-text:latest'  # 설치된 임베딩 모델명

class EmbeddingCreator:
    def __init__(self):
        print(f"🔌 FalkorDB 연결 중... (Graph: {GRAPH_NAME})")
        try:
            self.db = FalkorDB(host='localhost', port=6379)
            self.graph = self.db.select_graph(GRAPH_NAME)
        except Exception as e:
            print(f"❌ 연결 실패: {e}")
            exit()

    def get_nodes_without_embedding(self):
        """임베딩이 없는 노드만 조회"""
        query = """
        MATCH (n)
        WHERE n.embedding IS NULL
        RETURN ID(n), n.name, n.description, n.category, n.country, labels(n)
        """
        return self.graph.query(query).result_set

    def generate_embedding(self, text):
        """Ollama API로 텍스트 -> 벡터 변환"""
        try:
            res = requests.post(
                f"{OLLAMA_URL}/api/embeddings",
                json={"model": EMBED_MODEL, "prompt": text}
            )
            if res.status_code == 200:
                return res.json()['embedding']
            else:
                print(f"  ⚠️ API 오류: {res.text}")
                return None
        except Exception as e:
            print(f"  ❌ 통신 오류: {e}")
            return None

    def run(self):
        print("\n1. 작업 대상 확인 중...")
        nodes = self.get_nodes_without_embedding()
        
        if not nodes:
            print("✅ 모든 노드에 이미 임베딩 데이터가 있습니다. (작업 불필요)")
            self.verify_status()
            return

        total = len(nodes)
        print(f"🚀 총 {total}개 노드에 대해 임베딩 생성을 시작합니다.\n")

        success_count = 0
        
        for i, row in enumerate(nodes, 1):
            node_id = row[0]
            name = row[1]
            desc = row[2]
            # category나 country 정보가 있으면 활용
            extra = row[3] if row[3] else (row[4] if row[4] else "") 
            label = row[5][0] if row[5] else "Unknown"

            # 임베딩할 텍스트 결정 (설명이 없으면 이름+정보 조합)
            text_to_embed = desc if desc else f"{name} is a {label} related to {extra}"
            
            # 진행상황 출력
            print(f"  [{i}/{total}] 처리 중: {name[:30]}...", end="\r")

            # 1. 임베딩 생성
            vec = self.generate_embedding(text_to_embed)
            
            if vec:
                # 2. DB 업데이트 (Params 사용으로 안전하게 저장)
                # 인덱스를 안 만드니까 에러 날 일이 없음
                update_query = f"MATCH (n) WHERE ID(n) = {node_id} SET n.embedding = $vec"
                self.graph.query(update_query, {'vec': vec})
                success_count += 1
            
            # API 부하 조절을 위한 아주 짧은 대기
            # time.sleep(0.01) 

        print(f"\n\n✨ 완료! {success_count}/{total}개 노드 업데이트 성공.")
        self.verify_status()

    def verify_status(self):
        """최종 상태 확인"""
        print("\n📊 데이터 상태 점검:")
        try:
            total = self.graph.query("MATCH (n) RETURN count(n)").result_set[0][0]
            embedded = self.graph.query("MATCH (n) WHERE n.embedding IS NOT NULL RETURN count(n)").result_set[0][0]
            print(f"   - 전체 노드 수: {total}")
            print(f"   - 임베딩 보유 노드 수: {embedded}")
            
            if total == embedded and total > 0:
                print("   ✅ 데이터 준비 완료! 이제 검색 스크립트를 실행하세요.")
            elif total > 0:
                print(f"   ⚠️ 일부 노드({total-embedded}개)가 누락되었습니다. 스크립트를 재실행해보세요.")
        except Exception as e:
            print(f"   ❌ 점검 실패: {e}")

if __name__ == "__main__":
    creator = EmbeddingCreator()
    creator.run()