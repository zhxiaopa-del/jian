from langchain_community.chat_models import ChatTongyi
from research_knowledge import retrieve_similar_topk

# -------------------------------
# 完整封装函数
# -------------------------------
def risk_analysis(question: str, top_k: int = 3, model_name: str = "qwen-turbo", api_key: str = None) -> str:
    """
    根据用户问题进行风险分析：
    1. 从知识库检索 top_k 条相关内容作为参考标准
    2. 调用 LLM 对比标准与实际情况，返回风险分析结果

    Args:
        question: 用户描述的问题或场景
        top_k: 从知识库中检索的相关内容条数
        model_name: 使用的 LLM 模型名称
        api_key: LLM 接口的 API Key

    Returns:
        风险分析结果文本
    """

    # -------------------------------
    # 初始化 LLM（完全在函数内封装）
    # -------------------------------
    llm = ChatTongyi(
        model_name=model_name,
        api_key=api_key or "",
    )

    # -------------------------------
    # 风险分析提示模板
    # -------------------------------
    RISK_PROMPT_TEMPLATE = """你是一个专业的合规与风险评估专家。
        请根据提供的【参考标准】来分析【用户问题】中描述的情况，判断是否存在风险。

        【参考标准】：
        {rag_context}

        【用户问题】：
        {user_msg}

        请严格按照以下格式回答，不要有任何开场白：
        1. 标准要求：(请简述知识库中的相关标准规定)
        2. 实际情况：(请简述用户问题中描述的现状)
        3. 风险评估：(判断是否存在风险，并说明理由)
        4. 风险结论：(仅输出：存在风险 / 暂无风险 / 数据不足无法判断)
        """

    # -------------------------------
    # 1. 检索知识库，获取 top_k 条参考内容
    # -------------------------------
    chunks = retrieve_similar_topk(question, top_k=top_k)
    rag_context = "\n\n---\n\n".join(
        (c.get("content") or c.get("content_with_weight") or "无内容") for c in chunks
    )
    if not rag_context.strip():
        rag_context = "（未检索到相关标准，请根据常识与用户描述进行判断）"

    # -------------------------------
    # 2. 填充提示模板
    # -------------------------------
    risk_prompt = RISK_PROMPT_TEMPLATE.format(
        rag_context=rag_context,
        user_msg=question,
    )

    prompts = [
        {"role": "system", "content": "你只负责对比标准和实际情况进行风险判定。"},
        {"role": "user", "content": risk_prompt},
    ]

    # -------------------------------
    # 3. 调用 LLM
    # -------------------------------
    response = llm.invoke(prompts)
    return (response.content or "").strip()


# -------------------------------
# 示例调用
# -------------------------------
if __name__ == "__main__":
    question = "钻进冻结孔度，测斜的间隔为40m"
    api_key = "sk-ac445b11dbe74063b5a9d379d773fec4"
    result = risk_analysis(question, top_k=3, api_key=api_key)
    print(result)
