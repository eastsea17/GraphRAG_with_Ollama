# 🎉 100% Ollama 기반 GraphRAG 시스템

## ✅ 최종 구성

**모든 단계가 100% Ollama로 작동하는 완전 무료 시스템입니다!**

| 단계 | 스크립트 | 사용 모델 | 비용 |
|-----|---------|----------|------|
| 0️⃣ 데이터 생성 | `0_generate_data.py` | - | 무료 |
| 1️⃣ DB 로드 | `1_load_to_falkordb.py` | - | 무료 |
| 2️⃣ **설명 생성** | `2_enrich_graph_data.py` | **qwen3:8b** | **무료** ✨ |
| 3️⃣ **임베딩 생성** | `3_create_embeddings.py` | **nomic-embed-text** | **무료** ✨ |
| 4️⃣ **GraphRAG 쿼리** | `4_graph-rag.py` | **nomic-embed-text + qwen3:8b** | **무료** ✨ |
| 5️⃣ 네트워크 분석 | `5_analyze_network.py` | - | 무료 |

## 🚀 완전 무료 실행 가이드

### 1. Ollama 설치 및 모델 다운로드

```bash
# Ollama 설치 (macOS)
brew install ollama

# Ollama 서버 시작
ollama serve

# 필요한 모델 다운로드
ollama pull qwen3:8b             # LLM (4.9GB)
ollama pull nomic-embed-text     # 임베딩 (274MB)
```

### 2. FalkorDB 실행

```bash
docker run -p 6379:6379 -p 3001:3000 -it --rm \
  -v ./data:/var/lib/falkordb/data \
  falkordb/falkordb
```

### 3. 전체 파이프라인 실행

```bash
# Step 0: 데이터 생성 (배터리 산업 데이터)
python 0_generate_data.py

# Step 1: FalkorDB에 로드
python 1_load_to_falkordb.py

# Step 2: 노드 설명 생성 (Ollama LLM - 무료!)
python 2_enrich_graph_data.py

# Step 3: 벡터 임베딩 생성 (Ollama Embedding - 무료!)
python 3_create_embeddings.py

# Step 4: GraphRAG 쿼리 시스템 (Ollama - 무료!)
python 4_graph-rag.py

# Step 5: 네트워크 분석 (PageRank, Degree Centrality)
python 5_analyze_network.py
```

## 💰 최종 비용 비교

| 항목 | OpenAI 방식 | 100% Ollama |
|------|------------|-------------|
| LLM 설명 생성 | ~$1-2 | **무료** |
| 임베딩 생성 | ~$0.5-1 | **무료** |
| 쿼리당 비용 | ~$0.001-0.005 | **무료** |
| **총 초기 비용** | **$2-5** | **$0** 🎉 |
| **월간 사용 비용** | **$10-50** | **$0** 🎉 |

## 🎯 시스템 특징

### 장점
- ✅ **완전 무료** - API 비용 전혀 없음
- ✅ **데이터 프라이버시** - 모든 데이터가 로컬에 유지
- ✅ **오프라인 실행** - 인터넷 불필요 (모델 다운로드 후)
- ✅ **한국어 우수** - qwen3는 한국어 성능이 뛰어남
- ✅ **커스터마이징** - 원하는 모델로 쉽게 교체 가능
- ✅ **그래프 분석** - PageRank, Centrality 등 네트워크 분석 기능

### 시스템 요구사항
- **RAM**: 16GB 이상 (권장 24GB)
- **디스크**: 약 5-6GB (모델)
- **CPU/GPU**: M4 Pro의 Metal GPU 자동 활용
- **Docker**: FalkorDB 실행 필요

## 📊 성능

### 속도 (M4 Pro 기준)
- **데이터 생성**: ~1초 (20개 회사, 100개 기술, 300개 관계)
- **DB 로드**: ~5-10초
- **설명 생성**: ~2-3초/노드
- **임베딩 생성**: ~0.1-0.5초/노드
- **GraphRAG 쿼리**: ~3-5초/질문

### 품질
- **설명 정확도**: 산업 도메인에 적합한 설명 생성
- **검색 정확도**: 코사인 유사도 기반 정확한 검색
- **답변 품질**: 배터리 산업 컨텍스트 충실히 반영

## 🔧 모델 변경

원하는 Ollama 모델로 쉽게 변경 가능:

### LLM 변경 (설명 생성 & 답변 생성)

**`2_enrich_graph_data.py`:**
```python
# 라인 13
LLM_MODEL = 'qwen3:8b'  # 기본값

# 다른 옵션:
LLM_MODEL = 'llama3.1:8b'   # 영어에 강함
LLM_MODEL = 'gemma2:9b'     # Google 모델
LLM_MODEL = 'qwen2.5:14b'   # 더 나은 성능 (RAM 더 필요)
```

**`4_graph-rag.py`:**
```python
# 라인 17
CHAT_MODEL = 'qwen3:8b'  # 기본값
```

### 임베딩 모델 변경

**`3_create_embeddings.py`:**
```python
# 라인 22
EMBED_MODEL = 'nomic-embed-text:latest'  # 기본값

# 다른 옵션:
EMBED_MODEL = 'mxbai-embed-large'  # 1024차원
EMBED_MODEL = 'all-minilm'         # 384차원, 빠름
```

**`4_graph-rag.py`:**
```python
# 라인 16
EMBED_MODEL = 'nomic-embed-text:latest'  # 기본값
```

## 📝 파일 구조

```
251125_FalkorDB/
├── data/
│   └── csv/                       # CSV 데이터
│       ├── companies.csv          # 회사 정보 (name, country)
│       ├── technologies.csv       # 기술 정보 (name, category)
│       └── relations.csv          # 관계 정보 (START_ID, END_ID, TYPE)
│
├── 0_FalkorDB_intro.ipynb        # FalkorDB 소개 & 튜토리얼
│
├── 0_generate_data.py            # 배터리 산업 데이터 생성
├── 1_load_to_falkordb.py         # CSV → FalkorDB 로드
├── 2_enrich_graph_data.py        # LLM으로 노드 설명 생성 (Ollama)
├── 3_create_embeddings.py        # 벡터 임베딩 생성 (Ollama)
├── 4_graph-rag.py                # GraphRAG 쿼리 시스템 (Ollama)
├── 5_analyze_network.py          # 네트워크 분석 (PageRank, Centrality)
│
├── README.md                      # 프로젝트 전체 설명
├── README_OLLAMA.md              # Ollama 가이드 (이 문서)
└── FILE_STRUCTURE.md             # 파일 구조 설명
```

## 🎬 사용 예시

### GraphRAG 쿼리 (4_graph-rag.py)

```bash
$ python 4_graph-rag.py

🤖 Agent 가동 (Graph: EnergyGraph)
📥 데이터 로딩 중... ✅ 120개 노드 로드 완료

💬 질문: Sodium-Ion 배터리를 개발하는 곳은?
🔍 분석 중...
🧠 답변 생성 중...

============================================================
🤖 AI 답변:
Sodium-Ion 배터리는 [검색된 회사명]에서 개발하고 있습니다. 
이 기술은 리튬 이온 배터리의 대안으로 주목받고 있으며, 
[관련 기술 정보]...
============================================================
```

### 네트워크 분석 (5_analyze_network.py)

```bash
$ python 5_analyze_network.py

=== 1. 단순 인기도 (Degree Centrality) TOP 5 ===
가장 많은 회사가 매달려 있는 기술을 찾습니다.
1위: NCM Battery (개발사 8개)
2위: LFP Battery (개발사 6개)
...

=== 2. 구조적 영향력 (PageRank) TOP 5 ===
FalkorDB의 알고리즘 엔진(GraphBLAS)을 사용하여 PageRank를 계산합니다.
1위: NCM Battery (Score: 0.125432)
2위: LFP Battery (Score: 0.098765)
...
```

## 🚨 문제 해결

### Ollama 서버 연결 실패
```bash
# 서버 시작
ollama serve

# 백그라운드 실행
nohup ollama serve &

# 서버 상태 확인
curl http://localhost:11434/api/tags
```

### 모델 없음 오류
```bash
# 모델 다운로드
ollama pull qwen3:8b
ollama pull nomic-embed-text

# 설치된 모델 확인
ollama list
```

### FalkorDB 연결 실패
```bash
# FalkorDB 실행 확인
docker ps | grep falkordb

# FalkorDB 재시작
docker run -p 6379:6379 -p 3001:3000 -it --rm \
  -v ./data:/var/lib/falkordb/data \
  falkordb/falkordb
```

### 메모리 부족
- 더 작은 모델 사용: `qwen3:3b` 또는 `llama3.1:3b`
- 다른 프로그램 종료
- 노드 개수 줄이기 (0_generate_data.py의 설정 변경)

### 느린 속도
- GPU 확인: `ollama ps` (Metal 사용 중인지 확인)
- 모델 크기 축소
- 배치 크기 증가 (스크립트 수정)

## 📚 참고 자료

- [Ollama 공식 사이트](https://ollama.ai/)
- [Qwen3 모델 문서](https://qwen.readthedocs.io/)
- [Nomic Embed Text](https://www.nomic.ai/blog/posts/nomic-embed-text-v1)
- [FalkorDB 문서](https://docs.falkordb.com/)
- [GraphBLAS 알고리즘](https://docs.falkordb.com/graph_algorithms.html)

## 🔍 주요 기능 상세

### 1. 데이터 생성 (0_generate_data.py)
- 배터리 산업 관련 회사, 기술, 관계 데이터 생성
- 조정 가능한 노드 개수 (NUM_COMPANIES, NUM_TECHNOLOGIES, NUM_RELATIONS)
- 실제 존재하는 회사와 합성 데이터 조합

### 2. 그래프 데이터 강화 (2_enrich_graph_data.py)
- Ollama LLM을 사용하여 각 노드에 설명 자동 생성
- Technology: 기술적 특징, 용도, 장단점 설명
- Company: 회사 정보, 주요 사업, 특징 설명

### 3. 벡터 임베딩 (3_create_embeddings.py)
- Ollama embedding API로 텍스트 → 벡터 변환
- DB 인덱스 불필요 (데이터만 저장)
- 메모리 효율적인 처리

### 4. GraphRAG (4_graph-rag.py)
- **Guaranteed RAG**: DB 인덱스 의존성 제거
- Python 내부에서 코사인 유사도 직접 계산
- 그래프 관계 정보 자동 확장
- 컨텍스트 기반 정확한 답변 생성

### 5. 네트워크 분석 (5_analyze_network.py)
- Degree Centrality: 연결 개수 기반 중요도
- PageRank: 구조적 영향력 분석 (GraphBLAS)

---

**완전히 무료로 강력한 GraphRAG 시스템을 사용하세요!** 🚀
