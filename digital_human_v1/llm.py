# -*- coding: utf-8 -*-
import os
import json
import re
from datetime import datetime
from openai import OpenAI

class LLMService:
    def __init__(self):
        """初始化服务：加载配置、历史记录"""
        self._load_env()
        
        # 配置信息
        self.base_url = os.getenv("LLM_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1").rstrip("/")
        self.api_key = os.getenv("LLM_API_KEY", "") or os.getenv("DASHSCOPE_API_KEY", "")
        # 优先读取变量中的模型配置，默认使用 qwen-plus
        self.model = os.getenv("DOUBAO_MODEL") or os.getenv("MODEL_ID") or "qwen-plus"
        
        self.history_file = "data/db/memory.db"
        self.history = self._load_history()
        
        # 是否过滤思考过程 (针对 DeepSeek-R1 等模型)
        self.filter_think = True 

    def _load_env(self):
        """加载同目录下的 variables.env 环境变量"""
        env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "variables.env")
        if os.path.exists(env_path):
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip() and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        # 仅当环境变量不存在时才写入，避免覆盖系统设置
                        if k.strip() not in os.environ:
                            os.environ[k.strip()] = v.strip()

    def _get_current_time(self):
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def _load_history(self):
        """读取历史记录"""
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return []

    def _save_history(self):
        """保存历史记录"""
        try:
            os.makedirs(os.path.dirname(self.history_file), exist_ok=True)
            with open(self.history_file, "w", encoding="utf-8") as f:
                json.dump(self.history, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"历史记录保存失败: {e}")

    def clear_history(self):
        """清空对话记忆"""
        self.history = []
        self._save_history()

    def _raw_stream(self, text_stream):
        """
        只做 <think></think> 过滤，按 token 原样 yield。
        分块、首词、按句等均由 TTS 端（队列+缓冲）统一处理。
        """
        is_thinking = False
        for chunk in text_stream:
            delta = chunk.choices[0].delta.content or ""
            if not delta:
                continue
            if self.filter_think:
                if "<think>" in delta:
                    is_thinking = True
                    delta = delta.replace("<think>", "")
                if "</think>" in delta:
                    is_thinking = False
                    parts = delta.split("</think>")
                    delta = parts[-1]
                if is_thinking:
                    continue
            if delta:
                yield delta

    def chat_stream(self, user_msg):
        """
        【主入口】流式对话接口
        Args:
            user_msg (str): 用户输入的文本
        Yields:
            str: 原始 token 流（仅过滤 <think></think>），分块与缓冲由 TTS 端处理
        """
        if not self.api_key:
            yield "错误：未配置 API KEY，请检查 variables.env 文件。"
            return

        # 1. 注入时间感知
        prompt_msg = user_msg
        if any(w in user_msg for w in ["几点", "时间", "日期", "时候"]):
            prompt_msg = f"[系统时间: {self._get_current_time()}] {user_msg}"

        # 2. 构造请求上下文
        messages = [{"role": "system", "content": "你叫吉安电子客服，小名叫小吉，是个工作小助手。"}]
        messages.extend(self.history[-10:]) # 仅保留最近10轮
        messages.append({"role": "user", "content": prompt_msg})

        try:
            # 3. 发起 API 请求
            client = OpenAI(base_url=self.base_url, api_key=self.api_key)
            response_stream = client.chat.completions.create(
                model=self.model,
                messages=messages,
                stream=True,
                temperature=0.7
            )

            full_reply = ""
            # 4. 原始流输出，分块与缓冲由 TTS 端处理
            for delta in self._raw_stream(response_stream):
                full_reply += delta
                yield delta 

            # 5. 保存完整对话到历史
            self.history.append({"role": "user", "content": user_msg})
            self.history.append({"role": "assistant", "content": full_reply})
            self._save_history()

        except Exception as e:
            error_text = f"连接大脑时出错了: {str(e)}"
            print(error_text)
            yield "抱歉，我遇到了一点技术问题。"

# ----------------- 实例化供外部使用 -----------------
# 外部文件可以直接: from llm import llm_client
# 然后调用: llm_client.chat_stream("你好")
llm_client = LLMService()


# ----------------- 调试与测试代码 -----------------
if __name__ == "__main__":
    print(">>> 正在测试 LLM 服务 (模拟 TTS 接收)...")
    prompt = "10分钟介绍一下你自己，并告诉我几点了"
    print(f"User: {prompt}\nAI: ", end="")
    
    # 直接通过实例调用
    for text_block in llm_client.chat_stream(prompt):
        print(f"[{text_block}]", end="", flush=True)
    
    print("\n\n>>> 测试完成")