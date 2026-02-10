import json
import re
from datetime import datetime
from openai import OpenAI
from typing import Union


# ================= 配置信息 =================
BASE_URL = "http://10.3.0.16:8100/v1" 
API_KEY = "222442bb160d5081b9e38506901d6889"  
MODEL = "qwen3-14b"     


client = OpenAI(
    api_key=API_KEY,
    base_url=BASE_URL,
    timeout=60.0,
)

class DataExtractor:
    def __init__(self):
        self.conversation_history = []  # 对话历史记录

    def extract_fields(self, user_input):
        """
        提取字段，返回JSON
        :param user_input: 用户输入
        :return: JSON对象或数组
        """
        # 获取当前日期用于提示
        current_date = datetime.now()
        current_date_str = current_date.strftime('%Y-%m-%d')
        current_date_cn = current_date.strftime('%Y年%m月%d日')
        
        system_prompt = f"""你是一个专业的数据提取助手。请从用户输入提取信息，**必须同时检查回款类和合同类信息**。

【重要规则】：
1. **一条输入可能同时包含回款和合同两类信息**，需要分别提取
2. **所有字段都必须输出**，即使没有值也要设置为空字符串 "" 或 0（金额字段）
3. 如果输入中只提到回款信息，只返回回款类数据；如果只提到合同信息，只返回合同类数据；如果两类都有，返回两个JSON对象

【必填字段（这四个字段必须提取，不能为空）】：
- **负责人**：必须从用户输入中提取负责人姓名，不能为空
- **公司名称**：必须从用户输入中提取公司名称，不能为空
- **项目类型**：必须从用户输入中提取项目类型（如：软件开发、设备采购、技术服务等），不能为空
- **项目名称**：必须从用户输入中提取项目名称，如果用户没有明确提到，可以根据公司名称+项目类型组合生成，不能为空

【分类规则】：
1. **回款类**：涉及钱款到账、预计回款、回款节点、未回款金额、回款原因等
   - 关键词：回款、到账、收款、付款、未回款、催款等
2. **合同类**：涉及签署合同、合同金额、合同完成情况、合同状态等
   - 关键词：合同、签约、签署、完成情况、实施等

【日期字段（必填）】：
- 格式：必须是 "YYYY-MM-DD" 格式
- 当前日期参考：今天是 {current_date_str}（{current_date_cn}）
- 相对日期处理：
  * "今天"、"今日" → 今天的日期
  * "昨天"、"昨日" → 昨天的日期
  * "2月1号"、"2月1日" → 需要判断年份（通常是今年，如果已过且接近年底可能是明年）
- 如果用户没有提到日期，默认使用今天的日期：{current_date_str}

【回款类字段（所有字段都必须输出）】：
负责人、公司名称、项目类型、项目名称、月初预计可能回款、月初预计确定回款、可能回款、确定回款、实际回款、回款节点确定、回款节点、未回款金额、未完成原因、解决办法
- 金额字段（月初预计可能回款、月初预计确定回款、可能回款、确定回款、实际回款、未回款金额）：如果没有值，设置为 0
- 文本字段（负责人、公司名称、项目类型、项目名称、回款节点确定、未完成原因、解决办法）：如果没有值，设置为空字符串 ""
- **回款节点字段（重要）**：必须从以下四种标准值中选择一个，不能使用其他值：
  * "验收结算流程"
  * "挂账流程"
  * "付款计划发起"
  * "付款流程发起"
  * 如果用户提到的回款节点与以上四种不完全一致，请选择最接近的一个
  * 如果用户没有提到回款节点，设置为空字符串 ""

【合同类字段（所有字段都必须输出）】：
负责人、公司名称、项目类型、项目名称、月初预计可能合同、月初预计确定合同、可能合同、确定合同、实际合同、完成情况
- 金额字段（月初预计可能合同、月初预计确定合同、可能合同、确定合同、实际合同）：如果没有值，设置为 0
- 文本字段（负责人、公司名称、项目类型、项目名称、完成情况）：如果没有值，设置为空字符串 ""

【输出格式】：
如果只有一类信息，返回单个JSON对象；如果两类都有，返回JSON数组，包含两个对象,最后都是一个列表。

【输出示例1 - 只有回款信息】：
[{{
    "数据类别": "回款",
    "负责人": "王五",
    "公司名称": "C公司",
    "项目类型": "设备采购",
    "项目名称": "设备采购项目",
    "月初预计可能回款": 0,
    "月初预计确定回款": 0,
    "可能回款": 0,
    "确定回款": 0,
    "实际回款": 30000,
    "回款节点确定": "",
    "回款节点": "",
    "未回款金额": 25000,
    "未完成原因": "客户流程慢",
    "解决办法": "催一下"
}}]

【输出示例2 - 只有合同信息】：
[{{
    "数据类别": "合同",
    "负责人": "李四",
    "公司名称": "B公司",
    "项目类型": "软件开发",
    "项目名称": "软件开发项目",
    "月初预计可能合同": 0,
    "月初预计确定合同": 0,
    "可能合同": 0,
    "确定合同": 500000,
    "实际合同": 0,
    "完成情况": "目前还没开始实施"
}}]

【输出示例3 - 同时包含回款和合同信息】：
[
    {{
        "数据类别": "回款",
        "负责人": "张三",
        "公司名称": "A公司",
        "项目类型": "软件开发",
        "项目名称": "ERP系统",
        "月初预计可能回款": 0,
        "月初预计确定回款": 0,
        "可能回款": 0,
        "确定回款": 0,
        "实际回款": 50000,
        "回款节点确定": "",
        "回款节点": "",
        "未回款金额": 0,
        "未完成原因": "",
        "解决办法": ""
    }},
    {{
        "数据类别": "合同",
        "负责人": "张三",
        "公司名称": "A公司",
        "项目类型": "软件开发",
        "项目名称": "ERP系统",
        "月初预计可能合同": 0,
        "月初预计确定合同": 0,
        "可能合同": 0,
        "确定合同": 100000,
        "实际合同": 0,
        "完成情况": ""
    }}
]
"""
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"当前日期：{current_date_str}。用户输入：{user_input}"}
                ],
                temperature=0,
            )

            content = response.choices[0].message.content.strip()
            
            # 尝试解析JSON数组或单个JSON对象
            json_match = re.search(r'(\[.*\]|\{.*\})', content, re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group())
                # 如果是数组，返回数组；如果是单个对象，返回数组包含该对象
                if isinstance(parsed, list):
                    return parsed
                else:
                    return [parsed]
            return [{"error": "JSON解析失败", "raw": content}]
        except Exception as e:
            return [{"error": f"调用失败: {str(e)}"}]

    def extract_with_dialog(self, user_input):
        """
        提取字段，支持多轮对话补全缺失的必填字段
        :param user_input: 用户输入
        :return: 提取并补全后的数据列表（始终返回列表）
        """
        # 第一次提取
        result = self.extract_fields(user_input)
        
        # 确保result是列表格式
        if not isinstance(result, list):
            result = [result] if result else []
        
        # 处理每个元素
        completed_results = []
        for item in result:
            # 跳过错误项
            if not isinstance(item, dict) or "error" in item:
                continue
  
            # 补全缺失字段
            completed = self._complete_missing_fields(item)
            if completed:
                completed_results.append(completed)
        
        
        # 始终返回列表
        return completed_results
    
    def _complete_missing_fields(self, data):
        """
        补全缺失的必填字段
        :param data: 提取的数据
        :return: 补全后的数据，如果有缺失字段则返回 None（由前端通过 API 补全）
        """
        required_fields = ["负责人", "公司名称", "项目类型", "项目名称"]
        missing_fields = [field for field in required_fields if not data.get(field) or str(data.get(field)).strip() == ""]
        
        if not missing_fields:
            return data
        
        # 前后端交互模式：不在这里补全，返回 None，让前端通过 API 补全
        return data
    
    def get_missing_fields(self, data):
        """
        获取缺失的必填字段列表
        :param data: 提取的数据
        :return: 缺失字段列表
        """
        required_fields = ["负责人", "公司名称", "项目类型", "项目名称"]
        return [field for field in required_fields if not data.get(field) or str(data.get(field)).strip() == ""]


# ================= 主程序 =================
if __name__ == "__main__":
    extractor = DataExtractor()
    input_text = "丁辉说2月1号上海环保公司那个污水处理项目收到了5.5万元实际回款"
    result = extractor.extract_with_dialog(input_text)
    print(result)
    input_text = "丁辉说污水处理项目收到了5.5万元实际回款"
    print(result)
