# FalkorDB GraphRAG System

이 디렉토리는 FalkorDB를 사용한 배터리 산업 GraphRAG 시스템을 포함합니다.

## 📁 파일 구조

### 데이터 파일
- `companies.csv` - 배터리 회사 데이터 (1,200개)
- `technologies.csv` - 배터리 기술 데이터 (12,000개)
- `relations.csv` - 회사-기술 관계 데이터 (20,000개)

### GraphRAG 시스템
1. **`enrich_graph_data.py`** - 노드에 설명 추가
   - LLM을 사용하여 각 노드에 자동으로 description 생성
   
2. **`create_embeddings.py`** - 벡터 임베딩 생성
   - 설명을 벡터로 변환하고 인덱스 생성
   
3. **`graphrag_query.py`** - GraphRAG 쿼리 시스템
   - 벡터 검색 + 그래프 탐색 + LLM 답변 생성
   
4. **`demo_graphrag.py`** - 데모 스크립트
   - 샘플 질문으로 시스템 테스트

### 기타
- `analyze_network.py` - 네트워크 분석 (PageRank 등)
- `FalkorDB.ipynb` - Jupyter 노트북
- `generate_data.py` - 데이터 생성 스크립트

## 🚀 빠른 시작 가이드

### 1. 환경 설정

```bash
# 필요한 패키지 설치
pip install falkordb openai

# OpenAI API 키 설정
export OPENAI_API_KEY='your-api-key-here'
```

### 2. FalkorDB 실행

```bash
# Docker로 FalkorDB 실행
docker run -p 6379:6379 -p 3001:3000 -it --rm -v ./data:/var/lib/falkordb/data falkordb/falkordb
```

### 3. 데이터 로드 (이미 완료되어 있다면 건너뛰기)

```bash
# 터미널에서 bulk insert 실행
falkordb-bulk-insert EnergyGraph \
  --nodes-with-label Company companies.csv \
  --nodes-with-label Technology technologies.csv \
  --relations-with-type DEVELOPS relations.csv
```

### 4. GraphRAG 시스템 구축

**Step 1: 노드에 설명 추가** (테스트)
```bash
# 샘플로 10개만 처리
python enrich_graph_data.py --sample 10
```

모든 것이 정상이면 전체 처리:
```bash
# 전체 노드 처리 (시간 소요, API 비용 발생)
python enrich_graph_data.py --full
```

**Step 2: 벡터 임베딩 생성** (테스트)
```bash
# 샘플로 10개만 처리
python create_embeddings.py --sample 10
```

전체 처리:
```bash
# 전체 노드 임베딩 생성
python create_embeddings.py --full
```

**Step 3: GraphRAG 테스트**
```bash
# 데모 실행
python demo_graphrag.py

# 또는 대화형 모드
python graphrag_query.py
```

## 💡 사용 예시

### Python 코드에서 사용

```python
from graphrag_query import GraphRAG

# GraphRAG 초기화
rag = GraphRAG(graph_name='EnergyGraph')

# 질문하기
answer = rag.query("고에너지 밀도 배터리를 개발하는 한국 회사는?")
print(answer)

# 상세 정보와 함께 질문
answer = rag.query(
    "Solid-State Battery를 개발하는 회사들은?",
    top_k=5,           # 상위 5개 노드 검색
    verbose=True       # 검색 과정 출력
)
```

### 대화형 모드

```bash
python graphrag_query.py
```

```
💬 질문: Tesla가 개발하는 배터리 기술은?
🔍 질문: Tesla가 개발하는 배터리 기술은?
...
✅ 답변:
Tesla는 LFP Battery와 BMS 기술을 개발하고 있습니다...
```

## 🔍 시스템 아키텍처

```
사용자 질문
    ↓
1. Query Embedding (OpenAI)
    ↓
2. Vector Search (FalkorDB)
   - Technology 노드 검색
   - Company 노드 검색
    ↓
3. Graph Traversal (Cypher)
   - Technology → DEVELOPS ← Company
   - 관계망 탐색
    ↓
4. Context Assembly
   - 검색된 노드 정보 수집
   - 그래프 관계 정보 추가
    ↓
5. LLM Answer Generation (GPT-4)
    ↓
최종 답변
```

## ⚙️ 설정 옵션

### enrich_graph_data.py
- `--graph`: 그래프 이름 (기본값: EnergyGraph)
- `--sample N`: 샘플 모드 (각 타입별 N개만 처리)
- `--full`: 전체 노드 처리
- `--api-key`: OpenAI API 키 (환경변수 대신)

### create_embeddings.py
동일한 옵션 지원

### graphrag_query.py
```python
rag = GraphRAG(
    graph_name='EnergyGraph',  # 그래프 이름
    api_key='...'              # API 키 (선택사항)
)

answer = rag.query(
    question,
    top_k=3,        # 검색할 상위 노드 개수
    verbose=False   # 상세 로그 출력 여부
)
```

## 📊 데이터 확인

### FalkorDB UI 사용
브라우저에서 `http://localhost:3001` 접속

```cypher
// 설명이 있는 Technology 노드 확인
MATCH (t:Technology) 
WHERE t.description IS NOT NULL 
RETURN t LIMIT 5

// 임베딩이 있는 노드 확인
MATCH (t:Technology) 
WHERE t.embedding IS NOT NULL 
RETURN t.name, t.description LIMIT 5

// 벡터 검색 테스트
CALL db.idx.vector.queryNodes('Technology', 'embedding', 3, [벡터...]) 
YIELD node RETURN node
```

## 🐛 문제 해결

### "OpenAI API key가 필요합니다"
```bash
export OPENAI_API_KEY='sk-...'
```

### "FalkorDB 연결 실패"
FalkorDB Docker 컨테이너가 실행 중인지 확인:
```bash
docker ps | grep falkordb
```

### "벡터 인덱스가 없습니다"
`create_embeddings.py`를 먼저 실행하세요.

## 💰 비용 예상

- **설명 생성**: ~13,000 노드 × GPT-4-mini → 약 $1-2
- **임베딩 생성**: ~13,000 노드 × text-embedding-3-small → 약 $0.5-1
- **쿼리당 비용**: 약 $0.001-0.005

총 초기 구축 비용: **약 $2-5**

## 📚 추가 정보

- [FalkorDB 문서](https://docs.falkordb.com/)
- [OpenAI API 문서](https://platform.openai.com/docs/)
- [GraphRAG 개념](https://www.microsoft.com/en-us/research/project/graphrag/)

## 🤝 기여

버그 리포트나 개선 제안은 이슈로 등록해주세요!
