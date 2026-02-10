"""
列出 MCP 服务器的所有工具
"""
import re
import sys

# 设置输出编码
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def list_all_tools():
    """列出所有可用的工具"""
    print("=" * 60)
    print("MCP 服务器工具列表")
    print("=" * 60)
    print()
    
    # 直接列出已知的工具（从 mcp_server.py 中统计）
    tools = [
        {
            "name": "recognize_intent",
            "description": "识别用户输入的意图类型（chat/report/insert/update/delete/query）",
            "category": "意图识别"
        },
        {
            "name": "extract_data",
            "description": "从用户输入中提取结构化数据（负责人、公司名称、项目类型等）",
            "category": "数据提取"
        },
        {
            "name": "insert_data",
            "description": "插入新数据到数据库（回款或合同）",
            "category": "数据操作"
        },
        {
            "name": "update_data",
            "description": "更新数据库中的数据",
            "category": "数据操作"
        },
        {
            "name": "delete_data",
            "description": "根据提供的字段匹配删除数据（支持中英文字段名）",
            "category": "数据操作"
        },
        {
            "name": "query_data",
            "description": "查询数据库中的数据",
            "category": "数据操作"
        },
        {
            "name": "generate_report",
            "description": "生成指定年月的汇总报表（Excel格式）",
            "category": "报表生成"
        }
    ]
    
    print(f"总共 {len(tools)} 个工具：\n")
    
    # 按分类显示
    categories = {}
    for tool in tools:
        cat = tool["category"]
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(tool)
    
    for i, (category, tool_list) in enumerate(categories.items(), 1):
        print(f"{i}. {category} ({len(tool_list)} 个工具):")
        for j, tool in enumerate(tool_list, 1):
            print(f"   {i}.{j} {tool['name']}")
            print(f"      描述: {tool['description']}")
        print()
    
    print("=" * 60)
    print("工具详情：")
    print("=" * 60)
    for i, tool in enumerate(tools, 1):
        print(f"\n{i}. {tool['name']}")
        print(f"   分类: {tool['category']}")
        print(f"   描述: {tool['description']}")
    
    print("\n" + "=" * 60)
    print(f"总计: {len(tools)} 个工具")
    print("=" * 60)
    
    return len(tools)

if __name__ == "__main__":
    count = list_all_tools()
    print(f"\n工具列表生成完成，共 {count} 个工具")
