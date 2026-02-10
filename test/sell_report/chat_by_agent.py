from openai import OpenAI
from config import OPENAI_CONFIG
# 使用统一的配置（如果存在）

BASE_URL = OPENAI_CONFIG["base_url"]
API_KEY = OPENAI_CONFIG["api_key"]
MODEL = OPENAI_CONFIG["model"]

client = OpenAI(
    api_key=API_KEY,
    base_url=BASE_URL,
    timeout=60.0,
)

def chat_with_model(user_input: str):
    """普通对话 / 闲聊"""
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": "你是一个友好的聊天助手。"},
                {"role": "user", "content": user_input}
            ],
            max_tokens=200,
            temperature=0.7,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"出错：{str(e)}"


# 测试一下：
if __name__ == "__main__":
    reply = chat_with_model("你好呀，你今天过得怎么样？")
    print("AI 回复：", reply)
