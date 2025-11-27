from falkordb import FalkorDB

def analyze_network():
    # 1. DB 연결
    db = FalkorDB(host='localhost', port=6379)
    
    # 그래프 선택 (사용자님이 만드신 그래프 이름으로 변경하세요)
    # 예: 'EnergyGraph' 또는 'EnergyGraph_10000'
    g = db.select_graph('EnergyGraph') 

    print("=== 1. 단순 인기도 (Degree Centrality) TOP 5 ===")
    print("가장 많은 회사가 매달려 있는 기술을 찾습니다.")
    
    # Cypher 쿼리로 단순 집계
    degree_query = """
    MATCH (t:Technology)<-[:DEVELOPS]-(c:Company)
    RETURN t.name, count(c) as developers_count
    ORDER BY developers_count DESC
    LIMIT 5
    """
    
    res = g.query(degree_query)
    for i, row in enumerate(res.result_set, 1):
        print(f"{i}위: {row[0]} (개발사 {row[1]}개)")

    print("\n" + "="*50 + "\n")

    print("=== 2. 구조적 영향력 (PageRank) TOP 5 ===")
    print("FalkorDB의 알고리즘 엔진(GraphBLAS)을 사용하여 PageRank를 계산합니다.")
    
    # FalkorDB 내장 알고리즘 호출 (CALL pagerank.stream)
    # 문법: CALL pagerank.stream(NodeLabel, RelationType)
    pagerank_query = """
    CALL pagerank.stream('Technology', 'DEVELOPS')
    YIELD node, score
    RETURN node.name, score
    ORDER BY score DESC
    LIMIT 5
    """
    
    try:
        res = g.query(pagerank_query)
        for i, row in enumerate(res.result_set, 1):
            # score는 소수점으로 나오므로 보기 좋게 포맷팅
            print(f"{i}위: {row[0]} (Score: {row[1]:.6f})")
    except Exception as e:
        print(f"PageRank 계산 중 오류 발생: {e}")
        print("Tip: 데이터가 너무 적거나(노드 1~2개), 관계가 형성되지 않았을 수 있습니다.")
# FalkorDB 설치
if __name__ == "__main__":
    analyze_network()
