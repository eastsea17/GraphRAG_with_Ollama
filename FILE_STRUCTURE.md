# 📁 파일 구조 및 설명

## 📊 프로젝트 개요

이 프로젝트는 **100% Ollama 기반 GraphRAG 시스템**으로, 배터리 산업 지식 그래프를 구축하고 자연어 질의응답을 제공합니다.

## 🗂️ 디렉토리 구조

```
251125_FalkorDB/
├── data/
│   └── csv/                          # CSV 데이터 파일
│       ├── companies.csv             # 회사 정보 (name, country)
│       ├── technologies.csv          # 기술 정보 (name, category)
│       └── relations.csv             # 관계 정보 (START_ID, END_ID, TYPE)
│
├── 0_FalkorDB_intro.ipynb           # FalkorDB 소개 및 튜토리얼
│
├── 0_generate_data.py               # Step 0: 데이터 생성
├── 1_load_to_falkordb.py            # Step 1: DB 로드
├── 2_enrich_graph_data.py           # Step 2: 설명 생성 (Ollama LLM)
├── 3_create_embeddings.py           # Step 3: 임베딩 생성 (Ollama)
├── 4_graph-rag.py                   # Step 4: GraphRAG 쿼리 시스템
├── 5_analyze_network.py             # Step 5: 네트워크 분석
│
├── README.md                         # 프로젝트 전체 설명
├── README_OLLAMA.md                 # Ollama 설정 가이드
├── FILE_STRUCTURE.md                # 파일 구조 설명 (이 문서)
│
└── __pycache__/                      # Python 캐시 파일
```

---

## 📝 파일별 상세 설명

### 📓 Jupyter Notebook

#### `0_FalkorDB_intro.ipynb`
- **목적**: FalkorDB 소개 및 기본 사용법 튜토리얼
- **내용**: 
  - FalkorDB 설치 및 설정
  - 기본 Cypher 쿼리 예제
  - 그래프 데이터 모델링 소개

---

### 🐍 Python 스크립트 (실행 순서별)

#### `0_generate_data.py` - 데이터 생성
**기능**: 배터리 산업 관련 합성 데이터 생성

**생성 데이터**:
- **Companies**: 회사 정보 (name, country)
  - 실제 회사: LG Energy Solution, Tesla, CATL 등
  - 합성 회사: 자동 생성된 회사명
- **Technologies**: 기술 정보 (name, category)
  - NCM Battery, LFP Battery, Solid-State Battery 등
- **Relations**: 회사-기술 관계 (DEVELOPS)

**설정 변경 가능**:
```python
NUM_COMPANIES = 20      # 생성할 회사 개수
NUM_TECHNOLOGIES = 100  # 생성할 기술 개수
NUM_RELATIONS = 300     # 생성할 관계 개수
```

**실행**:
```bash
python 0_generate_data.py
```

**출력**: `data/csv/` 디렉토리에 3개 CSV 파일 생성

---

#### `1_load_to_falkordb.py` - DB 로드
**기능**: CSV 데이터를 FalkorDB 그래프 데이터베이스에 로드

**주요 동작**:
1. FalkorDB 연결 (localhost:6379)
2. 기존 그래프 삭제 (사용자 확인 필요)
3. Company 노드 생성
4. Technology 노드 생성
5. DEVELOPS 관계 생성

**사용 그래프**: `EnergyGraph`

**실행**:
```bash
python 1_load_to_falkordb.py
```

**주의사항**: 
- FalkorDB가 실행 중이어야 함
- 기존 데이터를 삭제하므로 주의 필요

---

#### `2_enrich_graph_data.py` - 설명 생성 (Ollama LLM)
**기능**: 그래프 노드에 AI 생성 설명 추가

**사용 모델**: `qwen3:8b` (Ollama LLM)

**주요 동작**:
1. 설명이 없는 노드 조회
2. 각 노드에 대해 Ollama LLM으로 설명 생성
   - Technology: 기술적 특징, 용도, 장단점
   - Company: 회사 정보, 주요 사업, 특징
3. 생성된 설명을 노드 속성으로 저장

**실행**:
```bash
python 2_enrich_graph_data.py
```

**설정 변경**:
```python
LLM_MODEL = 'qwen3:8b'  # 라인 13에서 변경 가능
```

---

#### `3_create_embeddings.py` - 임베딩 생성 (Ollama)
**기능**: 노드 설명을 벡터 임베딩으로 변환

**사용 모델**: `nomic-embed-text:latest` (Ollama Embedding)

**주요 동작**:
1. 임베딩이 없는 노드 조회
2. Ollama API로 텍스트 → 벡터 변환
3. 벡터를 노드 속성 `embedding`으로 저장
4. DB 인덱스 생성 안 함 (데이터만 저장)

**특징**:
- 클라이언트 사이드 검색을 위한 데이터 준비
- 'Invalid arguments' 에러 방지

**실행**:
```bash
python 3_create_embeddings.py
```

---

#### `4_graph-rag.py` - GraphRAG 쿼리 시스템
**기능**: 자연어 질의응답 시스템 (Guaranteed RAG)

**사용 모델**:
- Embedding: `nomic-embed-text:latest`
- LLM: `qwen3:8b`

**주요 동작**:
1. 전체 노드 데이터를 메모리에 캐싱
2. 사용자 질문을 벡터로 변환
3. Python 내부에서 코사인 유사도 계산 (DB 인덱스 불사용)
4. Top-K 유사 노드 선택
5. 그래프 관계 정보 확장
6. 컨텍스트 기반 LLM 답변 생성

**특징**:
- **Guaranteed RAG**: DB 인덱스 의존성 제거
- 메모리 내 검색으로 정확성 보장

**실행**:
```bash
python 4_graph-rag.py
```

**예시 질문**:
- "Sodium-Ion 배터리를 개발하는 곳은?"
- "Ford와 협력하는 배터리 회사는?"

---

#### `5_analyze_network.py` - 네트워크 분석
**기능**: 그래프 네트워크 분석 및 중요 노드 발견

**분석 알고리즘**:
1. **Degree Centrality**: 연결 개수 기반 인기도
   - 가장 많은 회사가 개발하는 기술 발견
2. **PageRank**: 구조적 영향력 분석
   - FalkorDB GraphBLAS 엔진 사용

**실행**:
```bash
python 5_analyze_network.py
```

**출력 예시**:
```
=== 1. 단순 인기도 (Degree Centrality) TOP 5 ===
1위: NCM Battery (개발사 8개)
2위: LFP Battery (개발사 6개)
...

=== 2. 구조적 영향력 (PageRank) TOP 5 ===
1위: NCM Battery (Score: 0.125432)
2위: LFP Battery (Score: 0.098765)
...
```

---

## 🔄 전체 실행 순서

### 1단계: 환경 설정

```bash
# Ollama 모델 다운로드
ollama pull qwen3:8b
ollama pull nomic-embed-text

# FalkorDB 실행
docker run -p 6379:6379 -p 3001:3000 -it --rm \
  -v ./data:/var/lib/falkordb/data \
  falkordb/falkordb
```

### 2단계: 데이터 준비

```bash
# Step 0: 데이터 생성
python 0_generate_data.py

# Step 1: DB 로드
python 1_load_to_falkordb.py
```

### 3단계: AI 처리

```bash
# Step 2: 설명 생성 (Ollama LLM)
python 2_enrich_graph_data.py

# Step 3: 임베딩 생성 (Ollama Embedding)
python 3_create_embeddings.py
```

### 4단계: 활용

```bash
# Step 4: GraphRAG 쿼리
python 4_graph-rag.py

# Step 5: 네트워크 분석
python 5_analyze_network.py
```

---

## 📋 CSV 파일 형식

### `companies.csv`
```csv
name,country
LG Energy Solution,Korea
Tesla,USA
CATL,China
...
```

### `technologies.csv`
```csv
name,category
NCM Battery,Battery
LFP Battery,Battery
BMS,Software
...
```

### `relations.csv`
```csv
START_ID,END_ID,TYPE
LG Energy Solution,NCM Battery,DEVELOPS
Tesla,LFP Battery,DEVELOPS
CATL,LFP Battery,DEVELOPS
...
```

---

## ⚙️ 주요 설정 파일 위치

| 설정 항목 | 파일 | 라인 | 기본값 |
|---------|------|------|--------|
| 데이터 개수 | `0_generate_data.py` | 8-10 | 20/100/300 |
| LLM 모델 | `2_enrich_graph_data.py` | 13 | `qwen3:8b` |
| 임베딩 모델 | `3_create_embeddings.py` | 22 | `nomic-embed-text:latest` |
| 임베딩 모델 | `4_graph-rag.py` | 16 | `nomic-embed-text:latest` |
| LLM 모델 | `4_graph-rag.py` | 17 | `qwen3:8b` |
| 그래프 이름 | 모든 파일 | - | `EnergyGraph` |

---

## 🎯 다음 단계

이제 파일 구조를 이해했다면:

1. ✅ **README_OLLAMA.md** 확인 - Ollama 설정 상세 가이드
2. ✅ **README.md** 확인 - 프로젝트 전체 개요
3. 🚀 **단계별 스크립트 실행** - 위의 실행 순서 참고
4. 🎬 **GraphRAG 활용** - 질의응답 시스템 테스트

---

**모든 준비가 완료되었습니다! 이제 100% 무료 GraphRAG 시스템을 사용하세요!** 🎉
