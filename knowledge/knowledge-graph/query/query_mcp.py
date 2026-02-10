from mcp.server.fastmcp import FastMCP
from query_api import query_graphrag,GraphRAGRequest,init

mcp = FastMCP(name="graph-rag-server",host="0.0.0.0",port=8001,stateless_http=True)

# GRAPH_RAG_API = "http://localhost:8000/neo4j/graphrag"

@mcp.tool()
def graph_rag_query(
    question: str,
    entities: list[str] = [],
    top_n_triple: int = 3
):
    """
    基于 Neo4j 的 GraphRAG 查询工具
    """
    payload=GraphRAGRequest(question=question,entities=entities,top_n_triple=top_n_triple)
    result=query_graphrag(payload)
    return result
    # payload = {
    #     "question": question,
    #     "entities": entities,
    #     "top_n_triple": top_n_triple
    # }
    #
    # resp = requests.post(GRAPH_RAG_API, json=payload, timeout=30)
    # resp.raise_for_status()
    # return resp.json()

if __name__ == "__main__":
    init()
    print("开始启动mcp")
    mcp.run(transport="streamable-http")