import httpx

# 配置信息
API_KEY = "ragflow-KCWP6wRAaUnjB1jdIGCWH4J5W1KOEYvwgSOjzgcpATE"
BASE_URL = "http://10.3.0.16:8080"
DEFAULT_DATASET_ID = "290db77ceac211f0be558281f8988170"

def retrieve_similar_topk(
    question: str,
    dataset_id: str = DEFAULT_DATASET_ID,
    top_k: int = 3,
    similarity_threshold: float = 0.2,
) -> list:
    """根据问题在指定知识库中做相似性检索，返回包含‘问题’和‘答案’的原始切片。"""
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
    
    # 按照相似度排序
    by_sim = sorted(
        chunks,
        key=lambda x: float(x.get("similarity") or x.get("vector_similarity") or 0),
        reverse=True,
    )
    return by_sim[:top_k]


def get_chunk_question(item: dict) -> str:
    """从 RAGFlow 返回的 chunk 中提取 Question 字段。兼容 question_kwd / question / questions 等。"""
    q = item.get("question_kwd") or item.get("question") or item.get("chunk_question")
    if q and isinstance(q, str):
        return q.strip()
    questions = item.get("questions")
    if isinstance(questions, list) and questions:
        first = questions[0]
        return (first.strip() if isinstance(first, str) else str(first)) if first else ""
    return "（该切片未单独存储问题字段）"


def get_top_similar_questions(question: str, top_k: int = 3, dataset_id: str = DEFAULT_DATASET_ID) -> list[str]:
    """根据用户问题检索相似度最高的 top_k 个切片，仅返回每个切片的 Question 列表。"""
    rows = retrieve_similar_topk(question, dataset_id=dataset_id, top_k=top_k)
    return [get_chunk_question(item) for item in rows]


def run_retrieve_top3(question: str, top_k: int = 3):
    """提取并输出 TopK 检索结果中存储的‘相似问题’。"""
    print(f"🔍 正在检索与“{question}”相似的问题...\n")

    try:
        rows = retrieve_similar_topk(question, top_k=top_k)
    except Exception as e:
        print(f"❌ 检索失败: {e}")
        return

    if not rows:
        print("未检索到相关内容。")
        return

    print("=" * 80)
    for i, item in enumerate(rows, 1):
        # --- 关键提取逻辑 ---
        # RAGFlow 的 QA 模式通常将问题存在 'question_kwd' 或 'question' 字段中
        print(item)
        print("-" * 80)
        matched_question = item.get("question_kwd") or item.get("question") or "（该切片未单独存储问题字段）"
        
        # 获取切片正文内容（答案部分）
        content = item.get("content_with_weight") or item.get("content") or "无内容"
        
        # 获取相关元数据
        doc_name = item.get("document_keyword") or item.get("docnm_kwd") or "未知文档"
        sim = item.get("similarity") or item.get("vector_similarity")
        sim_str = f"{sim:.4f}" if sim is not None else "-"

        print(f"【Top {i}】 匹配得分: {sim_str} | 来源文档: {doc_name}")
        print(f"📌 检索到的原问题: {matched_question}")
        print(f"💡 对应切片内容: {content.strip()}")
        print("-" * 80)


if __name__ == "__main__":
    # 执行检索
    TOP_K = 3
    QUESTION = "煤矿企业如何保障从业人员在安全生产与职业病危害防治中的监督权利？"
    run_retrieve_top3(question=QUESTION, top_k=TOP_K)