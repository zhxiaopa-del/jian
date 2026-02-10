import json
import re
from datetime import datetime
from openai import OpenAI
from typing import Dict, Any, Optional


# ================= 配置信息 =================
BASE_URL = "http://10.3.0.16:8100/v1" 
API_KEY = "222442bb160d5081b9e38506901d6889"  
MODEL = "qwen3-14b"     


client = OpenAI(
    api_key=API_KEY,
    base_url=BASE_URL,
    timeout=60.0,
)


class IntentRecognizer:
    """意图识别器：判断用户输入是闲聊、工作汇报还是查询汇总表"""
    
    def __init__(self):
        pass
    
    def recognize_intent(self, user_input: str) -> str:
        """
        识别用户意图
        
        Args:
            user_input: 用户输入的文本
            
        Returns:
            "chat" | "report" | "query"  # 只返回意图类型
        """
        system_prompt = """你是一个专业的意图识别助手。请分析用户的输入，判断用户的真实意图。

【三种意图类型】：

1. **chat（闲聊）**：
   - 用户在进行日常对话、问候、询问系统功能、闲聊等
   - 不涉及具体的工作数据录入或查询
   - 示例：
     * "你好"、"在吗"、"谢谢"、"辛苦了"
     * "这个系统怎么用？"、"有什么功能？"
     * "今天天气不错"、"吃饭了吗"
     * "帮我看看"（没有具体内容）

2. **report（工作汇报/数据录入）**：
   - 用户要汇报工作信息，需要提取并保存到数据库
   - 包含具体的业务数据：回款、合同、项目、负责人、公司、金额等
   - 关键词：收到、回款、合同、签约、到账、收款、付款、项目、负责人、公司等
   - 示例：
     * "丁辉收到1万元"
     * "A公司签了合同，金额5万"
     * "B公司项目回款3万元，负责人是张三"
     * "今天收到了C公司的回款2万"

3. **query（查询汇总表）**：
   - 用户要查询、生成、查看汇总表、报表、统计信息
   - 包含时间信息：月份、年份、日期范围等
   - 关键词：汇总、报表、统计、查询、生成、导出、查看、表格、Excel等
   - 示例：
     * "生成2月份的汇总表"
     * "查看2026年1月的报表"
     * "帮我统计一下这个月的回款情况"
     * "导出上个月的汇总表"
     * "生成汇总表"

【输出格式】：
请返回 JSON 格式，只包含 intent 字段：
{
    "intent": "chat" | "report" | "query"
}

【重要规则】：
1. 如果输入同时包含多个意图，优先选择最明确的意图
2. 如果只是简单的问候或对话，判断为 chat
3. 如果用户明确提到"汇总"、"报表"、"统计"等关键词，优先判断为 query
4. 如果用户提到具体的业务数据（金额、公司、项目等），优先判断为 report
"""

        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"用户输入：{user_input}"}
                ],
                temperature=0.3,  # 降低温度，提高一致性
            )

            content = response.choices[0].message.content.strip()
            
            # 尝试提取 JSON
            json_match = re.search(r"\{.*\}", content, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                
                # 验证和规范化结果
                intent = result.get("intent", "chat")
                if intent not in ["chat", "report", "query"]:
                    intent = "chat"  # 默认值
                
                return intent
            else:
                # 如果无法解析 JSON，使用规则匹配作为后备
                return self._fallback_intent_recognition(user_input)
                
        except Exception as e:
            print(f"意图识别出错: {str(e)}")
            # 出错时使用规则匹配作为后备
            return self._fallback_intent_recognition(user_input)
    
    def _fallback_intent_recognition(self, user_input: str) -> str:
        """
        规则匹配的后备方案（当 LLM 调用失败时使用）
        """
        user_input_lower = user_input.lower()
        
        # 查询关键词
        query_keywords = ["汇总", "报表", "统计", "查询", "生成", "导出", "查看", "表格", "excel", "汇总表"]
        if any(keyword in user_input_lower for keyword in query_keywords):
            return "query"
        
        # 工作汇报关键词
        report_keywords = ["收到", "回款", "合同", "签约", "到账", "收款", "付款", "项目", "负责人", "公司", "万元", "元"]
        if any(keyword in user_input_lower for keyword in report_keywords):
            return "report"
        
        # 默认判断为闲聊
        return "chat"
    


if __name__ == "__main__":
    # 测试代码
    recognizer = IntentRecognizer()
    
    test_cases = [
        "你好",
        "丁辉收到1万元",
        "生成2月份的汇总表",
        "A公司签了合同，金额5万",
        "查看2026年1月的报表",
        "谢谢",
        "帮我统计一下这个月的回款情况",
        "今天天气不错",
    ]
    
    print("=" * 60)
    print("意图识别测试")
    print("=" * 60)
    
    for test_input in test_cases:
        intent = recognizer.recognize_intent(test_input)
        print(f"\n输入: {test_input}")
        print(f"意图: {intent}")
        print("-" * 60)
