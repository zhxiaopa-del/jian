#!/usr/bin/env python3
"""
类型映射配置
将agent传来的"类型"字段映射到数据库字段
"""

# 回款类型映射
COLLECTION_TYPE_MAPPING = {
    "实际回款": "actual_collection",
    "确定回款": "confirmed_collection",
    "可能回款": "possible_collection",
    "月初预计可能回款": "estimated_possible_at_start",
    "月初预计确定回款": "estimated_confirmed_at_start",
    "未回款金额": "uncollected_amount",
    "未完成原因": "reason_for_non_completion",
    "解决办法": "solution",
}

# 合同类型映射
CONTRACT_TYPE_MAPPING = {
    "实际合同": "actual_contract",
    "确定合同": "confirmed_contract",
    "可能合同": "possible_contract",
    "月初预计可能合同": "estimated_possible_at_start",
    "月初预计确定合同": "estimated_confirmed_at_start",
    "完成情况": "completion_status",
}

# 所有类型映射（用于判断是回款还是合同）
ALL_TYPE_MAPPING = {
    **{k: ("collection", v) for k, v in COLLECTION_TYPE_MAPPING.items()},
    **{k: ("contract", v) for k, v in CONTRACT_TYPE_MAPPING.items()},
}


def get_data_category_and_field(type_name: str):
    """
    根据类型名称获取数据类别和字段名
    
    Args:
        type_name: 类型名称，如"实际回款"、"未完成原因"等
    
    Returns:
        tuple: (category, field_name) 或 (None, None) 如果类型不存在
        category: "collection" 或 "contract"
        field_name: 数据库字段名
    """
    return ALL_TYPE_MAPPING.get(type_name, (None, None))


def is_numeric_field(field_name: str) -> bool:
    """
    判断字段是否为数值类型
    
    Args:
        field_name: 数据库字段名
    
    Returns:
        bool: True表示数值字段，False表示文本字段
    """
    text_fields = {
        "reason_for_non_completion",
        "solution",
        "completion_status",
    }
    return field_name not in text_fields
