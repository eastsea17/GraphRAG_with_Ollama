"""
FalkorDB Graph Data Enrichment Script
======================================

이 스크립트는 FalkorDB의 그래프 노드(Technology, Company)에 
Ollama LLM을 사용하여 자동으로 설명(description)을 생성하고 추가합니다.

100% 무료 로컬 실행!

Usage:
    python 3_enrich_graph_data.py --sample 10  # 테스트용, 10개만 처리
    python 3_enrich_graph_data.py --full       # 전체 노드 처리
"""

# ========================================
# 🤖 LLM 모델 설정 (여기서 모델 변경)
# ========================================
LLM_MODEL = 'qwen3:8b'  # 사용할 Ollama 모델
# 다른 옵션: 'llama3.1:8b', 'gemma2:9b', 'qwen2.5:14b', 'phi3'

import argparse
import time
import requests
from typing import List, Dict
from falkordb import FalkorDB


class GraphEnricher:
    """FalkorDB 그래프에 설명을 자동 생성하여 추가하는 클래스 (Ollama 사용)"""
    
    def __init__(self, graph_name: str = 'EnergyGraph', ollama_url: str = 'http://localhost:11434'):
        """
        Args:
            graph_name: FalkorDB 그래프 이름
            ollama_url: Ollama API 엔드포인트
        """
        self.db = FalkorDB(host='localhost', port=6379)
        self.graph = self.db.select_graph(graph_name)
        
        # Ollama 설정
        self.ollama_url = ollama_url
        self.model = LLM_MODEL  # 설정 변수 사용
        self.processed_count = 0
        
        # Ollama 연결 확인
        try:
            response = requests.get(f"{ollama_url}/api/tags")
            if response.status_code != 200:
                raise ConnectionError(f"Ollama 서버에 연결할 수 없습니다: {ollama_url}")
            
            # 모델 확인
            models = response.json().get('models', [])
            model_names = [m['name'] for m in models]
            
            if not any(self.model in m for m in model_names):
                print(f"⚠️  {self.model} 모델이 없습니다. 'ollama pull {self.model}'로 다운로드하세요.")
                
        except Exception as e:
            raise ConnectionError(f"Ollama 서버 연결 실패: {e}\n'ollama serve'를 실행하고 'ollama pull {self.model}'로 모델을 다운로드하세요.")
        
    def get_nodes_without_description(self, label: str, limit: int = None) -> List[Dict]:
        """
        설명이 없는 노드들을 조회합니다.
        
        Args:
            label: 노드 레이블 ('Technology' or 'Company')
            limit: 조회할 최대 개수 (None이면 전체)
        
        Returns:
            노드 정보 리스트
        """
        query = f"""
        MATCH (n:{label})
        WHERE n.description IS NULL
        RETURN ID(n) as id, n.name as name, n.{('category' if label == 'Technology' else 'country')} as extra
        """
        
        if limit:
            query += f" LIMIT {limit}"
        
        result = self.graph.query(query)
        
        nodes = []
        for row in result.result_set:
            nodes.append({
                'id': row[0],
                'name': row[1],
                'extra': row[2]  # category for Technology, country for Company
            })
        
        return nodes
    
    def generate_description(self, name: str, extra: str, node_type: str) -> str:
        """
        Ollama LLM을 사용하여 노드에 대한 설명을 생성합니다.
        
        Args:
            name: 노드 이름
            extra: 추가 정보 (category or country)
            node_type: 'technology' or 'company'
        
        Returns:
            생성된 설명 텍스트
        """
        if node_type == 'technology':
            prompt = f"""You are a battery technology expert. Provide a concise 2-3 sentence description of the following battery technology:

Technology Name: {name}
Category: {extra}

Focus on:
- What this technology is
- Its key characteristics or advantages
- Its typical applications

Keep it factual and concise (max 100 words)."""
        
        else:  # company
            prompt = f"""You are a battery industry analyst. Provide a concise 2-3 sentence description of the following company:

Company Name: {name}
Country: {extra}

Focus on:
- What this company does in the battery industry
- Their specialization or key products
- Their market position if well-known

Keep it factual and concise (max 100 words). If this is a generated/fictional company name, provide a generic description based on the name pattern."""
        
        try:
            # Ollama API 호출
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "num_predict": 150
                    }
                }
            )
            
            if response.status_code != 200:
                raise Exception(f"Ollama API 오류: {response.status_code}")
            
            description = response.json()['response'].strip()
            return description
            
        except Exception as e:
            print(f"  ⚠️  설명 생성 실패: {e}")
            # 폴백: 간단한 설명
            if node_type == 'technology':
                return f"{name} is a {extra.lower()} technology used in battery systems."
            else:
                return f"{name} is a battery industry company based in {extra}."
    
    def update_node_description(self, node_id: int, description: str):
        """
        노드에 설명을 업데이트합니다.
        
        Args:
            node_id: 노드 ID
            description: 저장할 설명
        """
        # Cypher에서 문자열 이스케이프 처리
        escaped_desc = description.replace("'", "\\'").replace('"', '\\"')
        
        query = f"""
        MATCH (n) WHERE ID(n) = {node_id}
        SET n.description = '{escaped_desc}'
        """
        
        self.graph.query(query)
        self.processed_count += 1
    
    def enrich_technologies(self, limit: int = None):
        """Technology 노드들에 설명을 추가합니다."""
        print("\n🔋 Technology 노드 enrichment 시작...")
        
        nodes = self.get_nodes_without_description('Technology', limit)
        total = len(nodes)
        
        if total == 0:
            print("  ✅ 모든 Technology 노드에 이미 설명이 있습니다.")
            return
        
        print(f"  📊 처리할 노드: {total}개")
        
        for i, node in enumerate(nodes, 1):
            print(f"  [{i}/{total}] {node['name']} ({node['extra']})...", end=" ")
            
            description = self.generate_description(
                node['name'], 
                node['extra'], 
                'technology'
            )
            
            self.update_node_description(node['id'], description)
            print("✓")
            
            # API Rate limit 방지 (필요시)
            if i % 10 == 0:
                time.sleep(1)
        
        print(f"  ✅ {total}개 Technology 노드 처리 완료\n")
    
    def enrich_companies(self, limit: int = None):
        """Company 노드들에 설명을 추가합니다."""
        print("\n🏢 Company 노드 enrichment 시작...")
        
        nodes = self.get_nodes_without_description('Company', limit)
        total = len(nodes)
        
        if total == 0:
            print("  ✅ 모든 Company 노드에 이미 설명이 있습니다.")
            return
        
        print(f"  📊 처리할 노드: {total}개")
        
        for i, node in enumerate(nodes, 1):
            print(f"  [{i}/{total}] {node['name']} ({node['extra']})...", end=" ")
            
            description = self.generate_description(
                node['name'], 
                node['extra'], 
                'company'
            )
            
            self.update_node_description(node['id'], description)
            print("✓")
            
            # API Rate limit 방지
            if i % 10 == 0:
                time.sleep(1)
        
        print(f"  ✅ {total}개 Company 노드 처리 완료\n")
    
    def run(self, limit: int = None):
        """전체 enrichment 프로세스를 실행합니다."""
        print("=" * 60)
        print("FalkorDB Graph Data Enrichment")
        print("=" * 60)
        
        start_time = time.time()
        
        self.enrich_technologies(limit)
        self.enrich_companies(limit)
        
        elapsed = time.time() - start_time
        
        print("=" * 60)
        print(f"✅ 전체 처리 완료!")
        print(f"   처리된 노드: {self.processed_count}개")
        print(f"   소요 시간: {elapsed:.1f}초")
        print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description='FalkorDB 그래프에 설명을 자동 생성합니다 (Ollama 사용).')
    parser.add_argument('--graph', default='EnergyGraph', help='그래프 이름 (default: EnergyGraph)')
    parser.add_argument('--sample', type=int, help='샘플 모드: 각 타입별로 N개만 처리')
    parser.add_argument('--full', action='store_true', help='전체 노드 처리')
    parser.add_argument('--ollama-url', default='http://localhost:11434', help='Ollama API URL')
    
    args = parser.parse_args()
    
    if not args.sample and not args.full:
        print("❌ --sample N 또는 --full 옵션을 선택하세요.")
        print("   예: python 3_enrich_graph_data.py --sample 10")
        print("\n💡 Ollama 설정:")
        print("   ollama serve")
        print(f"   ollama pull {LLM_MODEL}")
        return
    
    try:
        enricher = GraphEnricher(graph_name=args.graph, ollama_url=args.ollama_url)
        
        limit = args.sample if args.sample else None
        enricher.run(limit=limit)
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        raise


if __name__ == "__main__":
    main()
