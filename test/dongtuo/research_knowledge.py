import httpx

# 配置信息
API_KEY = "ragflow-KCWP6wRAaUnjB1jdIGCWH4J5W1KOEYvwgSOjzgcpATE"
BASE_URL = "http://10.3.0.16:8080"
DEFAULT_DATASET_ID = "290db77ceac211f0be558281f8988170"
# DEFAULT_DATASET_ID = "f0b9b438fbed11f099a702679dd8882f"


def retrieve_similar_topk(
    question: str,
    dataset_id: str = DEFAULT_DATASET_ID,
    top_k: int = 3,
    similarity_threshold: float = 0.2,
) -> list:
    """根据问题在指定知识库中做相似性检索，返回相似度最高的 top_k 条结果。"""
    url = f"{BASE_URL.rstrip('/')}/api/v1/retrieval"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}",
    }
    payload = {
        "question": question,
        "dataset_ids": [str(dataset_id)],
        "top_k": max(top_k, 20),
        "similarity_threshold": similarity_threshold,
        "page_size": top_k,
    }
    with httpx.Client(timeout=30) as client:
        resp = client.post(url, json=payload, headers=headers)
        resp.raise_for_status()
        result = resp.json()

    if result.get("code") != 0:
        raise RuntimeError(result.get("message", result))

    data = result.get("data") or {}
    chunks = data.get("chunks", []) if isinstance(data, dict) else []
    by_sim = sorted(
        chunks,
        key=lambda x: float(x.get("similarity") or x.get("vector_similarity") or 0),
        reverse=True,
    )
    return by_sim[:top_k]


def run_retrieve_top3(question: str, top_k: int = 3):
    """在文档中做相似性检索并输出 Top N 答案。"""
    print("正在使用 RAGFlow 检索接口（相似性检索）...\n")
    print(f"🔍 问题：{question}")
    print(f"📌 在文档中检索相似度最高的 Top {top_k} 条答案…\n")

    try:
        rows = retrieve_similar_topk(question, top_k=top_k)
    except Exception as e:
        print(f"❌ 检索失败: {e}")
        return

    if not rows:
        print("未检索到与问题相似的内容。")
        return

    print("=" * 60)
    for i, item in enumerate(rows, 1):
        content = item.get("content") or item.get("content_with_weight") or "无内容"
        doc_name = item.get("document_keyword") or item.get("docnm_kwd") or "未知文档"
        sim = item.get("similarity") or item.get("vector_similarity")
        sim_str = f"相似度: {sim:.4f}" if sim is not None else "相似度: -"
        print(f"【Top {i}】 {sim_str} | 来源: {doc_name}")
        print(f"内容: {content}")
        print("-" * 60)


if __name__ == "__main__":
        # 固定参数：传入代码使用
    TOP_K = 3
    QUESTION = "安全口是几个"
    run_retrieve_top3(question=QUESTION, top_k=TOP_K)
