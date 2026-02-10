"""
主逻辑流程：
1. 输入一句话
2. 使用 agent 提取数据（多轮对话补全缺失字段）
3. 生成 JSON 文件
4. 存入数据库
5. 汇总成表格
"""

import json
from pathlib import Path
from datetime import datetime
from extra_query_by_agent import DataExtractor, interactive_mode
from json_to_database import SimpleDBManager
from sum_table import main as generate_report

# ================= 配置信息 =================
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "qwer1234",
    "database": "sell_report"
}

PROJECT_ROOT = Path.cwd()
JSON_OUTPUT_DIR = PROJECT_ROOT / "data" / "json_output"
JSON_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def save_json_to_file(json_data, output_dir=JSON_OUTPUT_DIR):
    """
    将 JSON 数据保存到文件
    :param json_data: JSON 数据（列表或字典）
    :param output_dir: 输出目录
    :return: 保存的文件路径
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_file = output_dir / f"extracted_data_{timestamp}.json"
    
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ JSON 文件已保存: {json_file}")
    return json_file


def save_to_database(json_list, db_manager):
    """
    将 JSON 数据存入数据库（直接调用 db_manager.insert）
    :param json_list: JSON 数据列表
    :param db_manager: 数据库管理器实例
    :return: (成功数, 失败数)
    """
    success_count = 0
    failed_count = 0
    
    for item in json_list:
        try:
            # 获取数据类别
            category = item.get('数据类别', '')
            if category not in ['回款', '合同']:
                print(f"⚠️ 跳过无效的数据类别: {category}")
                failed_count += 1
                continue
            
            # 准备数据（排除数据类别字段）
            data = {k: v for k, v in item.items() if k != '数据类别'}
            
            # 直接调用 insert 方法（已支持 upsert）
            if db_manager.insert(category, data):
                success_count += 1
                print(f"✅ 保存成功: {category} - {data.get('负责人', '')} - {data.get('公司名称', '')} - {data.get('项目名称', '')}")
            else:
                failed_count += 1
                print(f"❌ 保存失败: {category} - {data.get('负责人', '')} - {data.get('公司名称', '')} - {data.get('项目名称', '')}")
                    
        except Exception as e:
            failed_count += 1
            print(f"❌ 处理数据时出错: {str(e)}")
            print(f"   数据: {json.dumps(item, ensure_ascii=False)}")
            import traceback
            traceback.print_exc()
    
    return success_count, failed_count


def main_workflow(user_input=None, year=None, month=None, generate_excel=True):
    """
    主工作流程
    :param user_input: 用户输入的一句话（如果为None，则从命令行获取）
    :param year: 年份（用于生成报表，如果为None则使用当前年份）
    :param month: 月份（用于生成报表，如果为None则使用当前月份）
    :param generate_excel: 是否生成Excel报表
    """
    print("=" * 60)
    print("开始主工作流程")
    print("=" * 60)
    
    # 1. 获取用户输入
    if user_input is None:
        print("\n请输入要提取的信息（输入 'quit' 或 'exit' 退出）:")
        user_input = input("> ").strip()
        if not user_input or user_input.lower() in ['quit', 'exit', 'q']:
            print("已退出")
            return
    
    print(f"\n📝 输入内容: {user_input}")
    
    # 2. 使用 agent 提取数据（多轮对话）
    print("\n" + "=" * 60)
    print("步骤 1: 使用 Agent 提取数据")
    print("=" * 60)
    
    extractor = DataExtractor()
    json_list = extractor.extract_with_dialog(user_input, interactive=True)
    
    if not json_list:
        print("❌ 数据提取失败，流程终止")
        return
    
    print(f"\n✅ 成功提取 {len(json_list)} 条记录")
    print(f"提取结果:\n{json.dumps(json_list, indent=2, ensure_ascii=False)}")
    
    # 3. 保存 JSON 文件
    print("\n" + "=" * 60)
    print("步骤 2: 保存 JSON 文件")
    print("=" * 60)
    
    json_file = save_json_to_file(json_list)
    
    # 4. 存入数据库
    print("\n" + "=" * 60)
    print("步骤 3: 存入数据库")
    print("=" * 60)
    
    db_manager = SimpleDBManager(DB_CONFIG)
    success_count, failed_count = save_to_database(json_list, db_manager)
    
    print(f"\n📊 数据库保存结果:")
    print(f"   成功: {success_count} 条")
    print(f"   失败: {failed_count} 条")
    
    # 5. 生成汇总报表（如果需要）
    if generate_excel:
        print("\n" + "=" * 60)
        print("步骤 4: 生成汇总报表")
        print("=" * 60)
        
        # 确定年份和月份
        if year is None or month is None:
            now = datetime.now()
            year = year or now.year
            month = month or now.month
            print(f"使用当前日期: {year}年{month}月")
        
        try:
            generate_report(year=year, month=month)
            print(f"\n✅ 报表生成完成！")
        except Exception as e:
            print(f"\n❌ 报表生成失败: {str(e)}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("✅ 主工作流程完成！")
    print("=" * 60)


def interactive_main():
    """
    交互式主程序
    """
    print("=" * 60)
    print("数据提取与汇总系统")
    print("=" * 60)
    print("功能：")
    print("1. 输入一句话，使用 Agent 提取结构化数据")
    print("2. 自动保存 JSON 文件")
    print("3. 自动存入数据库")
    print("4. 自动生成汇总报表")
    print("\n输入 'quit' 或 'exit' 退出程序")
    print("=" * 60)
    
    # 默认自动生成报表，使用当前日期
    generate_excel = True
    year = None
    month = None
    
    # 循环处理输入
    while True:
        try:
            print("\n" + "-" * 60)
            user_input = input("\n请输入要提取的信息（输入 'quit' 或 'exit' 退出）:\n> ").strip()
            
            if not user_input or user_input.lower() in ['quit', 'exit', 'q']:
                print("\n再见！")
                break
            
            # 执行主工作流程
            main_workflow(user_input=user_input, year=year, month=month, generate_excel=generate_excel)
            
        except KeyboardInterrupt:
            print("\n\n检测到中断信号，退出程序")
            break
        except Exception as e:
            print(f"\n❌ 程序出错: {str(e)}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    import sys
    
    # 如果提供了命令行参数，直接处理
    if len(sys.argv) > 1:
        user_input = " ".join(sys.argv[1:])
        main_workflow(user_input=user_input)
    else:
        # 否则启动交互式模式
        interactive_main()
