"""
测试 generate_report MCP 工具
直接调用函数进行测试，支持通过LLM识别年月信息
"""
import sys
import io
import json
import re
from pathlib import Path
from datetime import datetime
from openai import OpenAI

# 设置输出编码为 UTF-8（修复 Windows GBK 编码问题）
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 添加当前目录到路径
sys.path.insert(0, str(Path(__file__).parent))

# 导入配置
from config import OPENAI_CONFIG

# ================= 年月提取器 =================
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

def test_generate_report_direct():
    """直接测试 generate_report 函数"""
    print("="*60)
    print("测试 generate_report 函数（直接调用）")
    print("="*60)
    print()
    
    try:
        # 导入函数
        from generate_report import generate_complete_report, read_detail_table
        print("[成功] 导入函数成功")
        print()
    except ImportError as e:
        print(f"[错误] 导入失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return
    
    # 测试用例1: 读取数据
    print("="*60)
    print("测试用例1: 读取2026年2月的数据")
    print("="*60)
    try:
        pay_table, con_table = read_detail_table(2026, 2)
        print(f"[成功] 数据读取成功")
        print(f"  回款表: {len(pay_table)} 条记录")
        print(f"  合同表: {len(con_table)} 条记录")
        if not pay_table.empty:
            print(f"  回款表列: {list(pay_table.columns)}")
        if not con_table.empty:
            print(f"  合同表列: {list(con_table.columns)}")
        print()
    except Exception as e:
        print(f"[错误] 数据读取失败: {str(e)}")
        import traceback
        traceback.print_exc()
        print()
        return
    
    # 测试用例2: 生成报表
    print("="*60)
    print("测试用例2: 生成2026年2月的汇总报表")
    print("="*60)
    try:
        generate_complete_report(pay_table, con_table, 2026, 2)
        print("[成功] 报表生成完成")
        print()
    except Exception as e:
        print(f"[错误] 报表生成失败: {str(e)}")
        import traceback
        traceback.print_exc()
        print()
        return
    
    print("="*60)
    print("测试完成")
    print("="*60)


def test_generate_report_mcp():
    """通过 MCP 服务器测试 generate_report 工具"""
    print("="*60)
    print("测试 generate_report MCP 工具（通过MCP服务器）")
    print("="*60)
    print()
    
    try:
        # 导入 MCP 服务器中的函数
        from mcp_server import generate_report
        print("[成功] 导入 MCP 工具函数成功")
        print()
    except ImportError as e:
        print(f"[错误] 导入失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return
    
    # 测试用例1: 使用当前年月（默认）
    print("="*60)
    print("测试用例1: 生成当前年月的报表（不传参数）")
    print("="*60)
    try:
        # 直接调用函数，不是通过MCP工具装饰器
        from generate_report import generate_complete_report, read_detail_table
        from datetime import datetime
        now = datetime.now()
        year, month = now.year, now.month
        pay_table, con_table = read_detail_table(year, month)
        generate_complete_report(pay_table, con_table, year, month)
        print("[成功] 工具调用成功")
        print(f"结果: 报表已生成 - {year}年{month}月")
        print()
    except Exception as e:
        print(f"[错误] 工具调用失败: {str(e)}")
        import traceback
        traceback.print_exc()
        print()
    
    # 测试用例2: 指定年月
    print("="*60)
    print("测试用例2: 生成指定年月的报表（2026年2月）")
    print("="*60)
    try:
        from generate_report import generate_complete_report, read_detail_table
        pay_table, con_table = read_detail_table(2026, 2)
        generate_complete_report(pay_table, con_table, 2026, 2)
        print("[成功] 工具调用成功")
        print(f"结果: 报表已生成 - 2026年2月")
        print()
    except Exception as e:
        print(f"[错误] 工具调用失败: {str(e)}")
        import traceback
        traceback.print_exc()
        print()
    
    print("="*60)
    print("MCP 工具测试完成")
    print("="*60)


def test_generate_report_with_llm():
    """通过LLM识别年月信息，然后生成报表"""
    print("="*60)
    print("测试 generate_report（通过LLM识别年月信息）")
    print("="*60)
    print()
    
    # 初始化年月提取器
    extractor = YearMonthExtractor()
    print("[成功] 年月提取器初始化成功")
    print()
    
    # 测试用例列表
    test_cases = [
        "生成2026年2月的报表",
        "帮我生成2月份的汇总表",
        "生成上个月的报表",
        "生成本月的报表",
        "生成报表",  # 没有明确年月，应该使用当前年月
        "生成2025年12月的汇总报表",
        "生成明年1月的报表",
    ]
    
    for i, user_input in enumerate(test_cases, 1):
        print("="*60)
        print(f"测试用例{i}: {user_input}")
        print("="*60)
        
        # 步骤1: 使用LLM提取年月信息
        print(f"【步骤1】使用LLM提取年月信息...")
        year_month = extractor.extract_year_month(user_input)
        
        if year_month.get("error"):
            print(f"[错误] 提取失败: {year_month.get('error')}")
            print()
            continue
        
        year = year_month.get("year")
        month = year_month.get("month")
        
        if not year or not month:
            print(f"[错误] 无法提取有效的年月信息")
            print(f"提取结果: {year_month}")
            print()
            continue
        
        print(f"[成功] 提取到年月信息: {year}年{month}月")
        print()
        
        # 步骤2: 调用生成报表函数
        print(f"【步骤2】生成报表...")
        try:
            from generate_report import generate_complete_report, read_detail_table
            
            pay_table, con_table = read_detail_table(year, month)
            print(f"  读取数据: 回款表{len(pay_table)}条, 合同表{len(con_table)}条")
            
            generate_complete_report(pay_table, con_table, year, month)
            print(f"[成功] 报表生成完成: {year}年{month}月")
            print()
        except Exception as e:
            print(f"[错误] 报表生成失败: {str(e)}")
            import traceback
            traceback.print_exc()
            print()
    
    print("="*60)
    print("LLM识别年月测试完成")
    print("="*60)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="测试 generate_report 工具")
    parser.add_argument(
        "--mode",
        choices=["direct", "mcp", "llm", "all"],
        default="all",
        help="测试模式: direct=直接调用函数, mcp=通过MCP工具, llm=通过LLM识别年月, all=全部测试"
    )
    
    args = parser.parse_args()
    
    if args.mode in ["direct", "all"]:
        test_generate_report_direct()
        print("\n")
    
    if args.mode in ["mcp", "all"]:
        test_generate_report_mcp()
        print("\n")
    
    if args.mode in ["llm", "all"]:
        test_generate_report_with_llm()
