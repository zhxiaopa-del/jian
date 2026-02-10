"""
MCP Server for Sales Report Management System
使用 fastmcp 框架提供工具：意图识别、数据提取、数据库操作、报表生成
"""
from fastmcp import FastMCP
from intend_by_agent import IntentRecognizer
from extra_query_by_agent import DataExtractor
from generate_report import generate_complete_report, read_detail_table
from json_to_database import get_db_manager
from db_connection import db_manager as conn_mgr
from year_month_extractor import year_month_extractor
import sys
from datetime import datetime
# 初始化组件
intent_recognizer = IntentRecognizer()
data_extractor = DataExtractor()
db_manager = get_db_manager()

# 创建 FastMCP 服务器
mcp = FastMCP("sell-report-mcp")

@mcp.tool()
def recognize_intent(context: str) -> str:
    """识别用户输入的意图类型（chat/report/insert/update/delete/query）"""
    return intent_recognizer.recognize_intent(context)

@mcp.tool()
def extract_data(context: str) -> list:
    """从用户输入中提取结构化数据（负责人、公司名称、项目类型等）"""
    return data_extractor.extract_with_dialog(context)

@mcp.tool()
def insert_data(category: str, data: dict) -> dict:
    """插入新数据到数据库（回款或合同）"""
    result = db_manager.insert(category, data)
    return {"success": result}

@mcp.tool()
def update_data(category: str, data: dict) -> dict:
    """更新数据库中的数据"""
    result = db_manager.update(category, data)
    return {"success": result}

@mcp.tool()
def delete_data(category: str, data: dict) -> dict:
    """根据提供的字段匹配删除数据（支持中英文字段名）"""
    result = db_manager.delete(category, data)
    return {"success": result}

@mcp.tool()
def query_data(category: str, filters: dict = None) -> list:
    """查询数据库中的数据"""
    if filters:
        table = db_manager.table_map.get(category)
        if not table:
            return [{"error": "未知的数据类别"}]
        
        translated = {k: v for k, v in db_manager._translate_fields(filters).items() if v is not None and v != ''}
        if not translated:
            return [{"error": "至少需要一个过滤条件"}]
        
        where_clause = " AND ".join([f"`{k}`=%s" for k in translated.keys()])
        sql = f"SELECT * FROM {table} WHERE {where_clause}"
        with conn_mgr.get_connection(use_dict_cursor=True) as conn:
            with conn.cursor() as cur:
                cur.execute(sql, list(translated.values()))
                result = cur.fetchall()
    else:
        result = db_manager.select(category)
    
    return [dict(row) for row in result]

@mcp.tool()
def generate_report(year: int = None, month: int = None, user_input: str = None) -> dict:
    """生成指定年月的汇总报表（Excel格式）
    
    参数说明：
    - year: 年份（可选）
    - month: 月份（可选）
    - user_input: 用户输入的自然语言（可选），如果year和month都未提供，将使用LLM从此输入中提取年月信息
    """
    # 如果year和month都未提供，尝试从user_input中提取
    if not year or not month:
        if user_input:
            year_month_result = year_month_extractor.extract_year_month(user_input)
            if year_month_result.get("year") and year_month_result.get("month"):
                year = year_month_result.get("year")
                month = year_month_result.get("month")
        
        # 如果还是没有，使用当前日期
        if not year or not month:
            now = datetime.now()
            year, month = now.year, now.month

    pay_table, con_table = read_detail_table(year, month)
    print("正在生成汇总报表...")
    generate_complete_report(pay_table, con_table, year, month)

    return {"success": True, "message": f"报表已生成：{year}年{month}月"}

if __name__ == "__main__":
    mcp.run()
