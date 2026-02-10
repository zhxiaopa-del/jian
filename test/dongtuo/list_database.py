import httpx

API_KEY = "ragflow-KCWP6wRAaUnjB1jdIGCWH4J5W1KOEYvwgSOjzgcpATE"
BASE_URL = "http://10.3.0.16:8080"

def list_datasets(page: int = 1, page_size: int = 10):
    """获取当前所有可用的知识库列表"""
    url = f"{BASE_URL.rstrip('/')}/api/v1/datasets"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
    }
    # 这里的参数通常通过 query string 传递
    params = {
        "page": page,
        "page_size": page_size
    }
    
    with httpx.Client(timeout=30) as client:
        resp = client.get(url, headers=headers, params=params)
        resp.raise_for_status()
        result = resp.json()

    if result.get("code") != 0:
        raise RuntimeError(result.get("message", result))

    # 返回数据集列表
    return result.get("data", [])

def show_all_datasets():
    """打印当前所有的知识库名称和 ID"""
    print("--- 当前可用知识库列表 ---")
    try:
        datasets = list_datasets()
        if not datasets:
            print("没有找到任何知识库。")
            return

        for ds in datasets:
            name = ds.get("name", "未命名")
            ds_id = ds.get("id", "无ID")
            doc_count = ds.get("doc_num", 0)
            print(f"名称: {name:<20} | ID: {ds_id} | 文档数: {doc_count}")
    except Exception as e:
        print(f"获取知识库列表失败: {e}")
    print("-" * 60)
if __name__ == "__main__":
    # 1. 先看看有哪些库
    show_all_datasets()
    
    # 2. 如果你想手动指定其中一个库进行测试
    # QUESTION = "安全口是几个"
    # run_retrieve_top3(question=QUESTION, top_k=3)