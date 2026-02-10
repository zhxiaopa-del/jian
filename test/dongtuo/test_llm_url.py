"""测试 vLLM 模型（与 Dify 上配置的 qwen3-14b 凭据一致）。"""
from openai import OpenAI

# Dify 里填的是 http://host.docker.internal:8100/v1（容器内访问宿主机）
BASE_URL = "http://10.3.0.16:8100/v1" 
API_KEY = "222442bb160d5081b9e38506901d6889"  
MODEL = "qwen3-14b"     

client = OpenAI(
    api_key=API_KEY,
    base_url=BASE_URL,
    timeout=60.0,
)

max_retries = 2
for attempt in range(max_retries + 1):
    try:
        resp = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "user", "content": "解释一下什么是私有化部署"},
            ],
        )
        print(resp.choices[0].message.content or "")
        break
    except Exception as e:
        err_msg = str(e)
        is_502 = "502" in err_msg or (getattr(e, "response", None) and getattr(e.response, "status_code", None) == 502)
        if is_502 and attempt < max_retries:
            print(f"请求返回 502，正在重试 ({attempt + 1}/{max_retries})...")
            continue
        if is_502:
            print("❌ 502 Bad Gateway：网关后面的模型服务未正常响应，请检查：")
            print("   1. 模型服务是否已启动、是否卡死")
            print("   2. 网关/反向代理到模型服务的配置与端口")
            print("   3. 模型是否仍在加载或超时")
        else:
            print("❌ 调用失败:", e)
        exit(1)
