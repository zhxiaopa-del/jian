import json
import re
from datetime import datetime
from typing import Dict, Any, Optional
from openai import OpenAI
from config import OPENAI_CONFIG

# 使用共享的配置
MODEL = OPENAI_CONFIG["model"]

# ================= OpenAI 客户端实例 =================
openai_client = OpenAI(
    api_key=OPENAI_CONFIG["api_key"],
    base_url=OPENAI_CONFIG["base_url"],
    timeout=OPENAI_CONFIG["timeout"],
)


class IntentRecognizer:
    """意图识别器：判断用户输入是闲聊、报表还是增删改查"""
    
    def __init__(self):
        pass
    
    def recognize_intent(self, user_input: str) -> str:
        """
        识别用户意图
        
        Args:
            user_input: 用户输入的文本
            
        Returns:
            "chat" | "report" | "insert" | "update" | "delete" | "query"
        """
        system_prompt = """你是一个专业的意图识别助手。请分析用户的输入，判断用户的真实意图。

【意图类型分类】：

1. **chat（闲聊）**：
   - 用户在进行日常对话、问候、询问系统功能、闲聊等
   - 不涉及具体的数据操作或报表生成
   - 示例：
     * "你好"、"在吗"、"谢谢"、"辛苦了"
     * "这个系统怎么用？"、"有什么功能？"
     * "今天天气不错"、"吃饭了吗"
     * "帮我看看"（没有具体内容）

2. **report（生成报表）**：
   - 用户要生成、查看、导出汇总表、报表、统计信息
   - 包含时间信息：月份、年份、日期范围等
   - 关键词：汇总、报表、统计、生成、导出、查看、表格、Excel、月报、年报等
   - 示例：
     * "生成2月份的汇总表"
     * "查看2026年1月的报表"
     * "帮我统计一下这个月的回款情况"
     * "导出上个月的汇总表"
     * "生成汇总表"
     * "生成2026年2月的报表"

3. **insert（新增数据）**：
   - 用户要新增、添加、录入、记录数据到数据库
   - 包含具体的业务数据：回款、合同、项目、负责人、公司、金额等
   - 关键词：新增、添加、录入、记录、收到、签了、到账、收款等
   - 示例：
     * "丁辉收到1万元"
     * "A公司签了合同，金额5万"
     * "帮我记一下，张三收到A公司ERP项目5万元回款"
     * "新增一条回款记录"
     * "今天收到了C公司的回款2万"

4. **update（修改数据）**：
   - 用户要修改、更新、变更已有数据
   - 关键词：修改、更新、变更、改成、改为、调整等
   - 示例：
     * "把张三的回款金额改成10万"
     * "更新A公司的合同金额为8万"
     * "修改这条记录"
     * "把回款金额调整为5万元"

5. **delete（删除数据）**：
   - 用户要删除、移除、清除数据
   - 关键词：删除、移除、清除、去掉、删掉等
   - 示例：
     * "删除张三的这条回款记录"
     * "移除A公司的合同数据"
     * "删掉这条记录"
     * "清除这个项目的数据"

6. **query（查询数据）**：
   - 用户要查询、查找、搜索、查看具体数据（不是报表）
   - 关键词：查询、查找、搜索、显示、列出等
   - 示例：
     * "查询张三的回款记录"
     * "查找A公司的合同数据"
     * "显示这个月的回款明细"
     * "列出所有回款记录"

【输出格式】：
请返回 JSON 格式，只包含 intent 字段：
{
    "intent": "chat" | "report" | "insert" | "update" | "delete" | "query"
}

【重要规则】：
1. 如果输入同时包含多个意图，优先选择最明确的意图
2. 如果只是简单的问候或对话，判断为 chat
3. 如果用户明确提到"汇总"、"报表"、"统计"、"生成报表"等关键词，判断为 report
4. 如果用户提到"新增"、"添加"、"录入"、"记录"、"收到"、"签了"等，判断为 insert
5. 如果用户提到"修改"、"更新"、"变更"、"改成"等，判断为 update
6. 如果用户提到"删除"、"移除"、"清除"等，判断为 delete
7. 如果用户提到"查询"、"查找"、"搜索"、"查看"（且不是报表），判断为 query
8. 如果用户提到具体的业务数据（金额、公司、项目等）但没有明确操作，优先判断为 insert
"""

        try:
            response = openai_client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"用户输入：{user_input}"}
                ],
                temperature=0.3,
            )

            content = response.choices[0].message.content.strip()
            
            # 尝试提取 JSON
            json_match = re.search(r"\{.*\}", content, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                
                # 验证和规范化结果
                intent = result.get("intent", "chat")
                valid_intents = ["chat", "report", "insert", "update", "delete", "query"]
                if intent not in valid_intents:
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
        
        # 报表关键词（生成报表）
        report_keywords = ["汇总", "报表", "统计", "生成", "导出", "表格", "excel", "汇总表", "月报", "年报"]
        if any(keyword in user_input_lower for keyword in report_keywords):
            return "report"
        
        # 删除关键词
        delete_keywords = ["删除", "移除", "清除", "去掉", "删掉"]
        if any(keyword in user_input_lower for keyword in delete_keywords):
            return "delete"
        
        # 修改关键词
        update_keywords = ["修改", "更新", "变更", "改成", "改为", "调整"]
        if any(keyword in user_input_lower for keyword in update_keywords):
            return "update"
        
        # 查询关键词（查询数据，不是报表）
        query_keywords = ["查询", "查找", "搜索", "显示", "列出"]
        if any(keyword in user_input_lower for keyword in query_keywords):
            return "query"
        
        # 新增关键词
        insert_keywords = ["新增", "添加", "录入", "记录", "收到", "回款", "合同", "签约", "到账", "收款", "付款", "项目", "负责人", "公司", "万元", "元", "签了"]
        if any(keyword in user_input_lower for keyword in insert_keywords):
            return "insert"
        
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
        "删除张三的回款记录",
        "修改回款金额为10万",
        "查询所有回款记录",
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
