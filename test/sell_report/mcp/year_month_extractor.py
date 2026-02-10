"""
年月提取器
使用大语言模型从用户输入中提取年份和月份信息
"""
import json
import re
from datetime import datetime
from openai import OpenAI
from config import OPENAI_CONFIG


class YearMonthExtractor:
    """使用大语言模型从用户输入中提取年月信息"""
    
    def __init__(self):
        self.client = OpenAI(
            api_key=OPENAI_CONFIG["api_key"],
            base_url=OPENAI_CONFIG["base_url"],
            timeout=OPENAI_CONFIG["timeout"],
        )
        self.model = OPENAI_CONFIG["model"]
    
    def extract_year_month(self, user_input: str) -> dict:
        """
        从用户输入中提取年月信息
        :param user_input: 用户输入的自然语言
        :return: 包含year和month的字典，如果无法识别则返回None
        """
        if not user_input or not user_input.strip():
            return {"year": None, "month": None, "error": "输入为空"}
        
        current_date = datetime.now()
        current_year = current_date.year
        current_month = current_date.month
        
        system_prompt = f"""你是一个专业的日期提取助手。请从用户输入中提取年份和月份信息。

【当前日期参考】：
- 当前日期：{current_date.strftime('%Y年%m月%d日')}
- 当前年份：{current_year}年
- 当前月份：{current_month}月

【提取规则】：
1. 年份识别：
   - 如果用户明确提到年份（如"2026年"、"2025年"），提取该年份
   - 如果用户只提到月份（如"2月"、"二月"），默认使用当前年份
   - 如果用户提到"今年"、"本年"，使用当前年份
   - 如果用户提到"去年"、"上年"，使用当前年份-1
   - 如果用户提到"明年"、"来年"，使用当前年份+1

2. 月份识别：
   - 支持中文数字：一月、二月...十二月
   - 支持阿拉伯数字：1月、2月...12月
   - 支持相对表达：本月、这个月 → 当前月份；上月、上个月 → 当前月份-1；下月、下个月 → 当前月份+1
   - 如果用户没有提到月份，默认使用当前月份

3. 特殊情况：
   - "生成报表"、"生成汇总表" 等没有明确年月时，使用当前年月
   - "2月份的报表" → year=当前年份, month=2
   - "2026年2月的报表" → year=2026, month=2
   - "上个月的报表" → year=当前年份（如果上个月是去年，则year=当前年份-1）, month=当前月份-1

【输出格式】：
必须输出JSON格式，包含year和month两个字段：
{{"year": 2026, "month": 2}}

如果无法识别，返回：
{{"year": null, "month": null, "error": "无法识别年月信息"}}
"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"用户输入：{user_input}"}
                ],
                temperature=0,
            )
            
            content = response.choices[0].message.content.strip()
            
            # 尝试解析JSON
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                year = result.get("year")
                month = result.get("month")
                
                # 验证年月有效性
                if year and month:
                    if isinstance(year, int) and isinstance(month, int):
                        if 1 <= month <= 12:
                            return {"year": year, "month": month}
                        else:
                            return {"year": year, "month": None, "error": f"月份无效: {month}"}
                    else:
                        return {"year": None, "month": None, "error": "年月必须是整数"}
                else:
                    return result
            
            return {"year": None, "month": None, "error": "无法解析LLM返回结果"}
            
        except Exception as e:
            return {"year": None, "month": None, "error": f"调用LLM失败: {str(e)}"}


# 创建全局实例
year_month_extractor = YearMonthExtractor()
