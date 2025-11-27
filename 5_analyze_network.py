from falkordb import FalkorDB

def analyze_network():
    # 1. Connect to DB
    db = FalkorDB(host='localhost', port=6379)
    
    # Select Graph (Change to your graph name)
    # e.g., 'EnergyGraph' or 'EnergyGraph_10000'
    g = db.select_graph('EnergyGraph') 

    print("=== 1. Degree Centrality TOP 5 ===")
    print("Finding technologies with the most developing companies.")
    
    # Simple aggregation with Cypher query
    degree_query = """
    MATCH (t:Technology)<-[:DEVELOPS]-(c:Company)
    RETURN t.name, count(c) as developers_count
    ORDER BY developers_count DESC
    LIMIT 5
    """
    
    res = g.query(degree_query)
    for i, row in enumerate(res.result_set, 1):
        print(f"Rank {i}: {row[0]} ({row[1]} developers)")

    print("\n" + "="*50 + "\n")

    print("=== 2. PageRank (Structural Influence) TOP 5 ===")
    print("Calculating PageRank using FalkorDB's algorithm engine (GraphBLAS).")
    
    # Call FalkorDB built-in algorithm (CALL pagerank.stream)
    # Syntax: CALL pagerank.stream(NodeLabel, RelationType)
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
            # Format score for readability
            print(f"Rank {i}: {row[0]} (Score: {row[1]:.6f})")
    except Exception as e:
        print(f"Error calculating PageRank: {e}")
        print("Tip: Data might be too small (1-2 nodes) or no relationships formed.")
# FalkorDB Installation
if __name__ == "__main__":
    analyze_network()
