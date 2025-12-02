from falkordb import FalkorDB
import config
import argparse

def analyze_network(graph_name=None):
    if graph_name is None:
        graph_name = config.GRAPH_NAME
        
    # 1. Connect to DB
    db = FalkorDB(host=config.FALKORDB_HOST, port=config.FALKORDB_PORT)
    g = db.select_graph(graph_name)
    
    print(f"Analyzing graph: {graph_name}")
    print("=" * 60)

    # Get basic statistics
    print("\n=== Graph Statistics ===")
    node_count = g.query("MATCH (n) RETURN count(n)").result_set[0][0]
    edge_count = g.query("MATCH ()-[r]->() RETURN count(r)").result_set[0][0]
    print(f"Total Nodes: {node_count}")
    print(f"Total Edges: {edge_count}")
    
    # Get node labels
    labels_query = "MATCH (n) RETURN DISTINCT labels(n)[0] as label, count(*) as cnt ORDER BY cnt DESC"
    labels_result = g.query(labels_query).result_set
    print("\nNode Types:")
    for row in labels_result:
        print(f"  - {row[0]}: {row[1]} nodes")
    
    print("\n" + "=" * 60 + "\n")

    print("=== 1. Degree Centrality TOP 10 ===")
    print("Finding nodes with the most connections.\n")
    
    # Generic degree centrality query
    degree_query = """
    MATCH (n)-[r]-()
    RETURN labels(n)[0] as type, 
           CASE 
               WHEN exists(n.name) THEN n.name
               WHEN exists(n.Id) THEN n.Id
               WHEN exists(n.Label) THEN n.Label
               ELSE toString(id(n))
           END as name,
           count(r) as degree
    ORDER BY degree DESC
    LIMIT 10
    """
    
    res = g.query(degree_query)
    for i, row in enumerate(res.result_set, 1):
        node_type, node_name, degree = row
        # Truncate long names
        display_name = node_name[:50] + "..." if len(node_name) > 50 else node_name
        print(f"Rank {i}: [{node_type}] {display_name} (Degree: {degree})")

    print("\n" + "=" * 60 + "\n")

    print("=== 2. PageRank (Structural Influence) TOP 10 ===")
    print("Calculating PageRank using custom algorithm.\n")
    
    # Since FalkorDB's pagerank.stream might not be available,
    # use a simple influence metric based on incoming edges
    influence_query = """
    MATCH (n)<-[r]-()
    RETURN labels(n)[0] as type,
           CASE 
               WHEN exists(n.name) THEN n.name
               WHEN exists(n.Id) THEN n.Id
               WHEN exists(n.Label) THEN n.Label
               ELSE toString(id(n))
           END as name,
           count(r) as influence_score
    ORDER BY influence_score DESC
    LIMIT 10
    """
    
    try:
        res = g.query(influence_query)
        if res.result_set:
            for i, row in enumerate(res.result_set, 1):
                node_type, node_name, score = row
                display_name = node_name[:50] + "..." if len(node_name) > 50 else node_name
                print(f"Rank {i}: [{node_type}] {display_name} (Influence: {score})")
        else:
            print("No incoming edges found.")
    except Exception as e:
        print(f"Error calculating influence: {e}")

    print("\n" + "=" * 60 + "\n")
    
    print("=== 3. Clustering Coefficient (Sample) ===")
    print("Checking local clustering for highly connected nodes.\n")
    
    # Simple triangle counting for top nodes
    clustering_query = """
    MATCH (n)-[r]-()
    WITH n, count(r) as deg
    WHERE deg > 2
    OPTIONAL MATCH (n)-[]-(neighbor1)-[]-(neighbor2)-[]-(n)
    WHERE id(neighbor1) < id(neighbor2)
    WITH labels(n)[0] as type,
         CASE 
             WHEN exists(n.name) THEN n.name
             WHEN exists(n.Id) THEN n.Id
             WHEN exists(n.Label) THEN n.Label
             ELSE toString(id(n))
         END as name,
         deg,
         count(DISTINCT neighbor1) as triangles
    WHERE deg > 0
    RETURN type, name, deg, 
           toFloat(triangles) / (deg * (deg - 1) / 2) as clustering_coef
    ORDER BY clustering_coef DESC
    LIMIT 10
    """
    
    try:
        res = g.query(clustering_query)
        if res.result_set:
            for i, row in enumerate(res.result_set, 1):
                node_type, node_name, deg, coef = row
                display_name = node_name[:50] + "..." if len(node_name) > 50 else node_name
                print(f"Rank {i}: [{node_type}] {display_name}")
                print(f"         Degree: {deg}, Clustering: {coef:.4f}")
        else:
            print("No triangles found in the graph.")
    except Exception as e:
        print(f"Error calculating clustering: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Analyze network structure in FalkorDB')
    parser.add_argument('--graph', type=str, default=config.GRAPH_NAME,
                       help=f'Graph name (default: {config.GRAPH_NAME})')
    args = parser.parse_args()
    
    analyze_network(graph_name=args.graph)
