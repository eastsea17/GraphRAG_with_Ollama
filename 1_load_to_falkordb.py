"""
Load CSV Data to FalkorDB
==========================

CSV 파일을 읽어서 FalkorDB 그래프에 로드하는 스크립트입니다.

Usage:
    python 2_load_to_falkordb.py
"""

import csv
import os
from falkordb import FalkorDB

# 설정
GRAPH_NAME = 'EnergyGraph'
CSV_DIR = 'data/csv'

def load_data_to_falkordb():
    """CSV 데이터를 FalkorDB에 로드합니다."""
    
    print("=" * 60)
    print("FalkorDB 데이터 로드")
    print("=" * 60)
    
    # FalkorDB 연결
    print("\n🔌 FalkorDB에 연결 중...")
    try:
        db = FalkorDB(host='localhost', port=6379)
        g = db.select_graph(GRAPH_NAME)
        print(f"✅ '{GRAPH_NAME}' 그래프에 연결 완료")
    except Exception as e:
        print(f"❌ FalkorDB 연결 실패: {e}")
        print("\n💡 FalkorDB가 실행 중인지 확인하세요:")
        print("   docker ps | grep falkordb")
        return
    
    # 기존 그래프 삭제 확인
    print(f"\n⚠️  기존 '{GRAPH_NAME}' 데이터를 삭제하고 새로 로드합니다.")
    confirm = input("계속하시겠습니까? (y/N): ").strip().lower()
    if confirm != 'y':
        print("취소되었습니다.")
        return
    
    # 그래프 삭제
    try:
        g = db.select_graph(GRAPH_NAME)
        g.delete()
        print("✅ 기존 데이터 삭제 완료")
    except Exception as e:
        # 그래프가 없으면 에러가 날 수 있음 (무시)
        # print(f"⚠️  기존 데이터 삭제 중 오류 발생 (무시됨): {e}")
        pass
    
    # 그래프 다시 선택 (생성)
    g = db.select_graph(GRAPH_NAME)
    
    # 1. Companies 로드
    print("\n🏢 Companies 로드 중...")
    companies_path = os.path.join(CSV_DIR, 'companies.csv')
    
    try:
        with open(companies_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            companies = list(reader)
            
        for i, row in enumerate(companies, 1):
            # 작은따옴표 이스케이프
            name = row['name'].replace("'", "\\'")
            country = row['country'].replace("'", "\\'")
            comp_type = row.get('type', 'Unknown').replace("'", "\\'")
            
            query = f"CREATE (:Company {{name: '{name}', country: '{country}', type: '{comp_type}'}})"
            g.query(query)
            
            if i % 20 == 0:
                print(f"   {i}/{len(companies)} 처리 중...", end="\r")
        
        print(f"   ✅ {len(companies)}개 회사 로드 완료")
        
    except FileNotFoundError:
        print(f"   ❌ 파일을 찾을 수 없습니다: {companies_path}")
        return
    except Exception as e:
        print(f"   ❌ Companies 로드 실패: {e}")
        return
    
    # 2. Technologies 로드
    print("\n🔋 Technologies 로드 중...")
    technologies_path = os.path.join(CSV_DIR, 'technologies.csv')
    
    try:
        with open(technologies_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            technologies = list(reader)
            
        for i, row in enumerate(technologies, 1):
            name = row['name'].replace("'", "\\'")
            category = row['category'].replace("'", "\\'")
            
            query = f"CREATE (:Technology {{name: '{name}', category: '{category}'}})"
            g.query(query)
            
            if i % 100 == 0:
                print(f"   {i}/{len(technologies)} 처리 중...", end="\r")
        
        print(f"   ✅ {len(technologies)}개 기술 로드 완료")
        
    except FileNotFoundError:
        print(f"   ❌ 파일을 찾을 수 없습니다: {technologies_path}")
        return
    except Exception as e:
        print(f"   ❌ Technologies 로드 실패: {e}")
        return
    
    # 3. Relations 로드
    print("\n🔗 Relations 로드 중...")
    relations_path = os.path.join(CSV_DIR, 'relations.csv')
    
    try:
        with open(relations_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            relations = list(reader)
        
        for i, row in enumerate(relations, 1):
            start_id = row['START_ID'].replace("'", "\\'")
            end_id = row['END_ID'].replace("'", "\\'")
            rel_type = row['TYPE'].upper() # 관계 타입은 대문자로 통일
            
            # 노드 라벨에 상관없이 name으로 매칭하여 관계 생성
            query = f"""
            MATCH (a {{name: '{start_id}'}}), (b {{name: '{end_id}'}})
            CREATE (a)-[:{rel_type}]->(b)
            """
            g.query(query)
            
            if i % 100 == 0:
                print(f"   {i}/{len(relations)} 처리 중...", end="\r")
        
        print(f"   ✅ {len(relations)}개 관계 로드 완료")
        
    except FileNotFoundError:
        print(f"   ❌ 파일을 찾을 수 없습니다: {relations_path}")
        return
    except Exception as e:
        print(f"   ❌ Relations 로드 실패: {e}")
        return
    
    # 완료
    print("\n" + "=" * 60)
    print("✅ 데이터 로드 완료!")
    print(f"📊 그래프 '{GRAPH_NAME}':")
    print(f"   - Companies: {len(companies)}개")
    print(f"   - Technologies: {len(technologies)}개")
    print(f"   - Relations: {len(relations)}개")
    print("=" * 60)
    print("\n💡 다음 단계:")
    print("   python 3_enrich_graph_data.py --full")
    print("=" * 60)


if __name__ == "__main__":
    load_data_to_falkordb()
