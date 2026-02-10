#!/usr/bin/env python3
"""
将CSV文件导入SQLite数据库
"""

import csv
import sys
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent / "jian_digitalhuman_mcp-dev"
sys.path.insert(0, str(project_root))

from database import (
    CollectionRecord,
    ContractRecord,
    init_database,
    get_session,
)


def import_collection_csv(csv_path: str, month: str = None):
    """
    导入回款CSV文件到数据库
    
    Args:
        csv_path: CSV文件路径
        month: 月份，格式：YYYY-MM。如果不提供，使用当前月份
    """
    if not month:
        month = datetime.now().strftime("%Y-%m")
    
    # 初始化数据库
    init_database()
    session = get_session()
    
    try:
        count = 0
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row_num, row in enumerate(reader, start=2):
                # 处理空值
                def get_float(value, default=0.0):
                    if not value or value.strip() == "":
                        return default
                    try:
                        return float(value)
                    except (ValueError, TypeError):
                        return default
                
                def get_str(value):
                    if not value or value.strip() == "":
                        return None
                    return value.strip()
                
                # 检查必填字段
                responsible_person = row.get("responsible_person", "").strip()
                project_type = row.get("project_type", "").strip()
                project_name = row.get("project_name", "").strip()
                
                if not responsible_person or not project_type or not project_name:
                    print(f"第 {row_num} 行: 跳过，缺少必填字段（responsible_person、project_type、project_name）")
                    continue
                
                # 检查是否已存在相同记录（根据负责人、项目类型、项目名称、月份）
                existing = session.query(CollectionRecord).filter(
                    CollectionRecord.responsible_person == responsible_person,
                    CollectionRecord.project_type == project_type,
                    CollectionRecord.project_name == project_name,
                    CollectionRecord.month == month
                ).first()
                
                if existing:
                    # 更新现有记录
                    existing.estimated_possible_at_start = get_float(row.get("estimated_possible_at_start", 0))
                    existing.estimated_confirmed_at_start = get_float(row.get("estimated_confirmed_at_start", 0))
                    existing.possible_collection = get_float(row.get("possible_collection", 0))
                    existing.confirmed_collection = get_float(row.get("confirmed_collection", 0))
                    existing.actual_collection = get_float(row.get("actual_collection", 0))
                    existing.uncollected_amount = get_float(row.get("uncollected_amount", 0))
                    existing.reason_for_non_completion = get_str(row.get("reason_for_non_completion"))
                    existing.solution = get_str(row.get("solution"))
                else:
                    # 创建新记录
                    collection = CollectionRecord(
                        responsible_person=responsible_person,
                        project_type=project_type,
                        project_name=project_name,
                        estimated_possible_at_start=get_float(row.get("estimated_possible_at_start", 0)),
                        estimated_confirmed_at_start=get_float(row.get("estimated_confirmed_at_start", 0)),
                        possible_collection=get_float(row.get("possible_collection", 0)),
                        confirmed_collection=get_float(row.get("confirmed_collection", 0)),
                        actual_collection=get_float(row.get("actual_collection", 0)),
                        uncollected_amount=get_float(row.get("uncollected_amount", 0)),
                        reason_for_non_completion=get_str(row.get("reason_for_non_completion")),
                        solution=get_str(row.get("solution")),
                        month=month,
                        is_subtotal=0,
                    )
                    session.add(collection)
                count += 1
        
        session.commit()
        print(f"成功导入 {count} 条回款记录到数据库（月份: {month}）")
        return count
    except Exception as e:
        session.rollback()
        print(f"导入回款数据失败: {e}")
        raise
    finally:
        session.close()


def import_contract_csv(csv_path: str, month: str = None):
    """
    导入合同CSV文件到数据库
    
    Args:
        csv_path: CSV文件路径
        month: 月份，格式：YYYY-MM。如果不提供，使用当前月份
    """
    if not month:
        month = datetime.now().strftime("%Y-%m")
    
    # 初始化数据库
    init_database()
    session = get_session()
    
    try:
        count = 0
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row_num, row in enumerate(reader, start=2):
                # 处理空值
                def get_float(value, default=0.0):
                    if not value or value.strip() == "":
                        return default
                    try:
                        return float(value)
                    except (ValueError, TypeError):
                        return default
                
                def get_str(value):
                    if not value or value.strip() == "":
                        return None
                    return value.strip()
                
                # 检查必填字段
                responsible_person = row.get("responsible_person", "").strip()
                project_name = row.get("project_name", "").strip()
                
                if not responsible_person or not project_name:
                    print(f"第 {row_num} 行: 跳过，缺少必填字段（responsible_person、project_name）")
                    continue
                
                # 检查是否已存在相同记录（根据负责人、项目名称、月份）
                existing = session.query(ContractRecord).filter(
                    ContractRecord.responsible_person == responsible_person,
                    ContractRecord.project_name == project_name,
                    ContractRecord.month == month
                ).first()
                
                if existing:
                    # 更新现有记录
                    existing.company_name = get_str(row.get("company_name"))
                    existing.estimated_possible_at_start = get_float(row.get("estimated_possible_at_start", 0))
                    existing.estimated_confirmed_at_start = get_float(row.get("estimated_confirmed_at_start", 0))
                    existing.possible_contract = get_float(row.get("possible_contract", 0))
                    existing.confirmed_contract = get_float(row.get("confirmed_contract", 0))
                    existing.actual_contract = get_float(row.get("actual_contract", 0))
                    existing.completion_status = get_str(row.get("completion_status"))
                else:
                    # 创建新记录
                    # 注意：ContractRecord表中没有project_type字段，CSV中有但会被忽略
                    contract = ContractRecord(
                        responsible_person=responsible_person,
                        company_name=get_str(row.get("company_name")),
                        project_name=project_name,
                        estimated_possible_at_start=get_float(row.get("estimated_possible_at_start", 0)),
                        estimated_confirmed_at_start=get_float(row.get("estimated_confirmed_at_start", 0)),
                        possible_contract=get_float(row.get("possible_contract", 0)),
                        confirmed_contract=get_float(row.get("confirmed_contract", 0)),
                        actual_contract=get_float(row.get("actual_contract", 0)),
                        completion_status=get_str(row.get("completion_status")),
                        month=month,
                        is_subtotal=0,
                    )
                    session.add(contract)
                count += 1
        
        session.commit()
        print(f"成功导入 {count} 条合同记录到数据库（月份: {month}）")
        return count
    except Exception as e:
        session.rollback()
        print(f"导入合同数据失败: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    # 获取当前月份
    current_month = datetime.now().strftime("%Y-%m")
    
    # CSV文件路径
    base_dir = Path(__file__).parent
    pay_csv = base_dir / "pay_table_en.csv"
    contract_csv = base_dir / "contract_table.csv"
    
    print("=" * 60)
    print("开始导入CSV数据到SQLite数据库")
    print("=" * 60)
    
    # 导入回款数据
    if pay_csv.exists():
        print(f"\n导入回款数据: {pay_csv}")
        try:
            collection_count = import_collection_csv(str(pay_csv), current_month)
        except Exception as e:
            print(f"错误: {e}")
            import traceback
            traceback.print_exc()
    else:
        print(f"\n警告: 回款CSV文件不存在: {pay_csv}")
    
    # 导入合同数据
    if contract_csv.exists():
        print(f"\n导入合同数据: {contract_csv}")
        try:
            contract_count = import_contract_csv(str(contract_csv), current_month)
        except Exception as e:
            print(f"错误: {e}")
            import traceback
            traceback.print_exc()
    else:
        print(f"\n警告: 合同CSV文件不存在: {contract_csv}")
    
    print("\n" + "=" * 60)
    print("导入完成!")
    print("=" * 60)
    
    # 验证数据
    print("\n验证数据库中的数据...")
    try:
        session = get_session()
        collection_count = session.query(CollectionRecord).filter(CollectionRecord.month == current_month).count()
        contract_count = session.query(ContractRecord).filter(ContractRecord.month == current_month).count()
        session.close()
        print(f"{current_month} 月份的回款记录总数: {collection_count}")
        print(f"{current_month} 月份的合同记录总数: {contract_count}")
    except Exception as e:
        print(f"验证失败: {e}")
