#!/usr/bin/env python3
"""
将中文CSV转换为英文列名的CSV
"""

import csv
from pathlib import Path

# 字段映射：中文 -> 英文
FIELD_MAPPING = {
    "负责人": "responsible_person",
    "公司名称": "company_name",
    "项目类型": "project_type",
    "项目名称": "project_name",
    "月初预计可能合同": "estimated_possible_at_start",
    "月初预计确定合同": "estimated_confirmed_at_start",
    "可能合同": "possible_contract",
    "确定合同": "confirmed_contract",
    "实际合同": "actual_contract",
    "完成情况": "completion_status",
}

# 回款字段映射（如果需要）
COLLECTION_FIELD_MAPPING = {
    "负责人": "responsible_person",
    "公司名称": "company_name",
    "项目类型": "project_type",
    "项目名称": "project_name",
    "月初预计可能回款": "estimated_possible_at_start",
    "月初预计确定回款": "estimated_confirmed_at_start",
    "可能回款": "possible_collection",
    "确定回款": "confirmed_collection",
    "实际回款": "actual_collection",
    "未回款金额": "uncollected_amount",
    "未完成原因": "reason_for_non_completion",
    "解决办法": "solution",
}


def convert_csv_to_english(input_file: str, output_file: str = None, field_mapping: dict = None):
    """
    将中文CSV转换为英文列名的CSV
    
    Args:
        input_file: 输入CSV文件路径
        output_file: 输出CSV文件路径，如果不提供，自动生成
        field_mapping: 字段映射字典，如果不提供，使用默认的合同字段映射
    """
    if field_mapping is None:
        field_mapping = FIELD_MAPPING
    
    input_path = Path(input_file)
    if not input_path.exists():
        print(f"错误: 文件不存在: {input_file}")
        return
    
    # 生成输出文件名
    if output_file is None:
        output_path = input_path.parent / f"{input_path.stem}_en{input_path.suffix}"
    else:
        output_path = Path(output_file)
    
    # 读取并转换
    with open(input_path, 'r', encoding='utf-8') as f_in:
        reader = csv.DictReader(f_in)
        
        # 获取原始列名
        original_headers = reader.fieldnames
        
        # 创建英文列名映射
        english_headers = []
        for header in original_headers:
            english_header = field_mapping.get(header.strip(), header.strip())
            english_headers.append(english_header)
        
        # 写入新文件
        with open(output_path, 'w', encoding='utf-8', newline='') as f_out:
            writer = csv.DictWriter(f_out, fieldnames=english_headers)
            writer.writeheader()
            
            for row in reader:
                # 转换每一行的字段名
                english_row = {}
                for original_header, english_header in zip(original_headers, english_headers):
                    english_row[english_header] = row.get(original_header, "")
                writer.writerow(english_row)
    
    print("转换完成!")
    print(f"   输入文件: {input_path}")
    print(f"   输出文件: {output_path}")
    print(f"   记录数: {sum(1 for _ in open(output_path, encoding='utf-8')) - 1}")


if __name__ == "__main__":
    # 转换合同CSV
    convert_csv_to_english(
        "d:\\1work\\test\\sell_report\\con_table.csv",
        "d:\\1work\\test\\sell_report\\con_table_en.csv",
        FIELD_MAPPING
    )
