#!/usr/bin/env python3
"""
保存财务数据工具
用于接收agent传来的数据并存储到数据库
"""

import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import sys
from pathlib import Path
from collections import defaultdict

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from database import (
    CollectionRecord,
    ContractRecord,
    get_session,
    init_database,
)
from database.type_mapping import (
    get_data_category_and_field,
    is_numeric_field,
)
from mcp_instance import mcp

logger = logging.getLogger(__name__)


@mcp.tool()
async def save_collection_data(
    data: str, month: str = None
) -> str:
    """
    保存回款数据到数据库
    
    Args:
        data: JSON字符串，包含回款数据列表。每个记录应包含：
            - responsible_person: 负责人
            - project_type: 项目类型
            - project_name: 项目名称
            - estimated_possible_at_start: 月初预计可能回款（可选，默认0）
            - estimated_confirmed_at_start: 月初预计确定回款（可选，默认0）
            - possible_collection: 可能回款（可选，默认0）
            - confirmed_collection: 确定回款（可选，默认0）
            - actual_collection: 实际回款（可选，默认0）
            - uncollected_amount: 未回款金额（可选，默认0）
            - reason_for_non_completion: 未完成原因（可选）
            - solution: 解决办法（可选）
            - is_subtotal: 是否为小计行（可选，默认0）
        month: 月份，格式：YYYY-MM（如：2026-02）。如果不提供，使用当前月份
    
    Returns:
        保存结果信息
    """
    try:
        # 初始化数据库
        init_database()
        
        # 解析JSON数据
        if isinstance(data, str):
            records = json.loads(data)
        else:
            records = data
        
        if not isinstance(records, list):
            records = [records]
        
        # 确定月份
        if not month:
            month = datetime.now().strftime("%Y-%m")
        
        # 获取数据库会话
        session = get_session()
        
        saved_count = 0
        try:
            for record in records:
                collection = CollectionRecord(
                    responsible_person=record.get("responsible_person", ""),
                    project_type=record.get("project_type", ""),
                    project_name=record.get("project_name", ""),
                    estimated_possible_at_start=float(
                        record.get("estimated_possible_at_start", 0) or 0
                    ),
                    estimated_confirmed_at_start=float(
                        record.get("estimated_confirmed_at_start", 0) or 0
                    ),
                    possible_collection=float(
                        record.get("possible_collection", 0) or 0
                    ),
                    confirmed_collection=float(
                        record.get("confirmed_collection", 0) or 0
                    ),
                    actual_collection=float(
                        record.get("actual_collection", 0) or 0
                    ),
                    uncollected_amount=float(
                        record.get("uncollected_amount", 0) or 0
                    ),
                    reason_for_non_completion=record.get(
                        "reason_for_non_completion"
                    ),
                    solution=record.get("solution"),
                    is_subtotal=int(record.get("is_subtotal", 0)),
                    month=month,
                )
                session.add(collection)
                saved_count += 1
            
            session.commit()
            return json.dumps(
                {
                    "success": True,
                    "message": f"成功保存 {saved_count} 条回款记录",
                    "month": month,
                    "count": saved_count,
                },
                ensure_ascii=False,
            )
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    except Exception as e:
        logger.error(f"保存回款数据失败: {e}", exc_info=True)
        return json.dumps(
            {"success": False, "message": f"保存失败: {str(e)}"},
            ensure_ascii=False,
        )


@mcp.tool()
async def save_contract_data(
    data: str, month: str = None
) -> str:
    """
    保存合同数据到数据库
    
    Args:
        data: JSON字符串，包含合同数据列表。每个记录应包含：
            - responsible_person: 负责人
            - company_name: 公司名称（可选）
            - project_name: 项目名称
            - estimated_possible_at_start: 月初预计可能合同（可选，默认0）
            - estimated_confirmed_at_start: 月初预计确定合同（可选，默认0）
            - possible_contract: 可能合同（可选，默认0）
            - confirmed_contract: 确定合同（可选，默认0）
            - actual_contract: 实际合同（可选，默认0）
            - completion_status: 完成情况（可选）
            - is_subtotal: 是否为小计行（可选，默认0）
        month: 月份，格式：YYYY-MM（如：2026-02）。如果不提供，使用当前月份
    
    Returns:
        保存结果信息
    """
    try:
        # 初始化数据库
        init_database()
        
        # 解析JSON数据
        if isinstance(data, str):
            records = json.loads(data)
        else:
            records = data
        
        if not isinstance(records, list):
            records = [records]
        
        # 确定月份
        if not month:
            month = datetime.now().strftime("%Y-%m")
        
        # 获取数据库会话
        session = get_session()
        
        saved_count = 0
        try:
            for record in records:
                contract = ContractRecord(
                    responsible_person=record.get("responsible_person", ""),
                    company_name=record.get("company_name"),
                    project_name=record.get("project_name", ""),
                    estimated_possible_at_start=float(
                        record.get("estimated_possible_at_start", 0) or 0
                    ),
                    estimated_confirmed_at_start=float(
                        record.get("estimated_confirmed_at_start", 0) or 0
                    ),
                    possible_contract=float(
                        record.get("possible_contract", 0) or 0
                    ),
                    confirmed_contract=float(
                        record.get("confirmed_contract", 0) or 0
                    ),
                    actual_contract=float(
                        record.get("actual_contract", 0) or 0
                    ),
                    completion_status=record.get("completion_status"),
                    is_subtotal=int(record.get("is_subtotal", 0)),
                    month=month,
                )
                session.add(contract)
                saved_count += 1
            
            session.commit()
            return json.dumps(
                {
                    "success": True,
                    "message": f"成功保存 {saved_count} 条合同记录",
                    "month": month,
                    "count": saved_count,
                },
                ensure_ascii=False,
            )
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    except Exception as e:
        logger.error(f"保存合同数据失败: {e}", exc_info=True)
        return json.dumps(
            {"success": False, "message": f"保存失败: {str(e)}"},
            ensure_ascii=False,
        )


@mcp.tool()
async def save_financial_data_from_agent(
    data: str, month: str = None
) -> str:
    """
    从agent工作流保存财务数据（统一格式）
    
    支持新格式数据（包含"数据类别"字段），根据数据类别分别调用回款和合同保存函数。
    同一批数据中可以同时包含回款和合同两种类型的记录。
    
    Args:
        data: JSON字符串，包含财务数据列表。列表中可以混合包含回款和合同记录。
            每个记录应包含：
            - 数据类别: "回款" 或 "合同"（必填）
            - 负责人: 负责人姓名（必填）
            - 公司名称: 公司名称（必填）
            - 项目类型: 项目类型（必填）
            - 项目名称: 项目名称（必填）
            
            回款记录（数据类别="回款"）还应包含：
            - 月初预计可能回款: 数字，默认0
            - 月初预计确定回款: 数字，默认0
            - 可能回款: 数字，默认0
            - 确定回款: 数字，默认0
            - 实际回款: 数字，默认0
            - 未回款金额: 数字，默认0
            - 未完成原因: 字符串，可选
            - 解决办法: 字符串，可选
            
            合同记录（数据类别="合同"）还应包含：
            - 月初预计可能合同: 数字，默认0
            - 月初预计确定合同: 数字，默认0
            - 可能合同: 数字，默认0
            - 确定合同: 数字，默认0
            - 实际合同: 数字，默认0
            - 完成情况: 字符串，可选
            
        month: 月份，格式：YYYY-MM（如：2026-02）。如果不提供，使用当前月份
    
    Returns:
        JSON字符串，包含保存结果信息：
        {
            "success": true/false,
            "message": "成功保存 X 条回款记录和 Y 条合同记录",
            "month": "YYYY-MM",
            "collection_count": 回款记录数量,
            "contract_count": 合同记录数量
        }
    """
    try:
        # 初始化数据库
        init_database()
        
        # 确定月份
        if not month:
            month = datetime.now().strftime("%Y-%m")
        
        # 解析JSON数据
        if isinstance(data, str):
            try:
                records = json.loads(data)
            except json.JSONDecodeError as e:
                return json.dumps(
                    {"success": False, "message": f"JSON解析失败: {str(e)}"},
                    ensure_ascii=False,
                )
        else:
            records = data
        
        if not isinstance(records, list):
            records = [records]
        
        if not records:
            return json.dumps(
                {"success": False, "message": "没有有效的数据记录"},
                ensure_ascii=False,
            )
        
        # 检查是否是新格式（包含"数据类别"字段）
        is_new_format = False
        if records and isinstance(records[0], dict) and "数据类别" in records[0]:
            is_new_format = True
        
        # 辅助函数：处理空字符串和None值
        def get_value_or_none(value):
            """如果值为空字符串，返回None，否则返回原值"""
            if value == "" or value is None:
                return None
            return str(value).strip() if str(value).strip() else None
        
        def get_float_value(value, default=0.0):
            """转换为浮点数，空字符串或None返回默认值"""
            if value == "" or value is None:
                return default
            try:
                return float(value)
            except (ValueError, TypeError):
                return default
        
        # 分离回款和合同数据
        # 注意：同一批数据中可能同时包含回款和合同两种类型的数据
        collection_records = []
        contract_records = []
        
        if is_new_format:
            # 新格式：直接根据"数据类别"字段分类
            # 支持同一批数据中混合包含回款和合同记录
            for record in records:
                data_category = record.get("数据类别", "").strip()
                
                if data_category == "回款":
                    # 转换为 save_collection_data 期望的格式
                    collection_record = {
                        "responsible_person": record.get("负责人", "").strip(),
                        "project_type": record.get("项目类型", "").strip(),
                        "project_name": record.get("项目名称", "").strip(),
                        "estimated_possible_at_start": get_float_value(record.get("月初预计可能回款", 0)),
                        "estimated_confirmed_at_start": get_float_value(record.get("月初预计确定回款", 0)),
                        "possible_collection": get_float_value(record.get("可能回款", 0)),
                        "confirmed_collection": get_float_value(record.get("确定回款", 0)),
                        "actual_collection": get_float_value(record.get("实际回款", 0)),
                        "uncollected_amount": get_float_value(record.get("未回款金额", 0)),
                        "reason_for_non_completion": get_value_or_none(record.get("未完成原因")),
                        "solution": get_value_or_none(record.get("解决办法")),
                    }
                    collection_records.append(collection_record)
                
                elif data_category == "合同":
                    # 转换为 save_contract_data 期望的格式
                    contract_record = {
                        "responsible_person": record.get("负责人", "").strip(),
                        "company_name": record.get("公司名称", "").strip() or None,
                        "project_name": record.get("项目名称", "").strip(),
                        "estimated_possible_at_start": get_float_value(record.get("月初预计可能合同", 0)),
                        "estimated_confirmed_at_start": get_float_value(record.get("月初预计确定合同", 0)),
                        "possible_contract": get_float_value(record.get("可能合同", 0)),
                        "confirmed_contract": get_float_value(record.get("确定合同", 0)),
                        "actual_contract": get_float_value(record.get("实际合同", 0)),
                        "completion_status": get_value_or_none(record.get("完成情况")),
                    }
                    contract_records.append(contract_record)
                else:
                    logger.warning(f"未知的数据类别: {data_category}，跳过该记录")
        else:
            # 旧格式：使用原有逻辑处理
            # 按项目分组数据（同一个项目的多条记录需要合并）
            collection_groups = defaultdict(lambda: {
                "responsible_person": "",
                "project_type": "",
                "project_name": "",
                "estimated_possible_at_start": 0.0,
                "estimated_confirmed_at_start": 0.0,
                "possible_collection": 0.0,
                "confirmed_collection": 0.0,
                "actual_collection": 0.0,
                "uncollected_amount": 0.0,
                "reason_for_non_completion": None,
                "solution": None,
            })
            
            contract_groups = defaultdict(lambda: {
                "responsible_person": "",
                "company_name": "",
                "project_name": "",
                "estimated_possible_at_start": 0.0,
                "estimated_confirmed_at_start": 0.0,
                "possible_contract": 0.0,
                "confirmed_contract": 0.0,
                "actual_contract": 0.0,
                "completion_status": None,
            })
            
            # 处理每条记录
            for record in records:
                date_str = record.get("日期", "")
                company_name = record.get("公司名", "")
                responsible_person = record.get("负责人", "")
                project_category = record.get("项目分类", "")
                project_name = record.get("项目名称", "")
                type_name = record.get("类型", "")
                event_content = record.get("事件内容", "")
                
                # 获取类型对应的数据类别和字段名
                category, field_name = get_data_category_and_field(type_name)
                
                if not category or not field_name:
                    logger.warning(f"未知的类型: {type_name}，跳过该记录")
                    continue
                
                # 根据类别分组
                if category == "collection":
                    key = (responsible_person, project_name, project_category)
                    group = collection_groups[key]
                    
                    if not group["responsible_person"]:
                        group["responsible_person"] = responsible_person
                        group["project_type"] = project_category
                        group["project_name"] = project_name
                    
                    if is_numeric_field(field_name):
                        try:
                            value = float(event_content) if event_content else 0.0
                            if field_name in ["actual_collection", "confirmed_collection", 
                                             "possible_collection", "uncollected_amount",
                                             "estimated_possible_at_start", "estimated_confirmed_at_start"]:
                                group[field_name] += value
                            else:
                                group[field_name] = value
                        except (ValueError, TypeError):
                            logger.warning(f"无法将事件内容转换为数字: {event_content}")
                    else:
                        if event_content:
                            if group[field_name]:
                                group[field_name] += f"；{event_content}"
                            else:
                                group[field_name] = str(event_content)
                
                elif category == "contract":
                    key = (responsible_person, project_name)
                    group = contract_groups[key]
                    
                    if not group["responsible_person"]:
                        group["responsible_person"] = responsible_person
                        group["company_name"] = company_name
                        group["project_name"] = project_name
                    
                    if is_numeric_field(field_name):
                        try:
                            value = float(event_content) if event_content else 0.0
                            if field_name in ["actual_contract", "confirmed_contract", 
                                             "possible_contract",
                                             "estimated_possible_at_start", "estimated_confirmed_at_start"]:
                                group[field_name] += value
                            else:
                                group[field_name] = value
                        except (ValueError, TypeError):
                            logger.warning(f"无法将事件内容转换为数字: {event_content}")
                    else:
                        if event_content:
                            if group[field_name]:
                                group[field_name] += f"；{event_content}"
                            else:
                                group[field_name] = str(event_content)
            
            # 转换为记录列表
            collection_records = list(collection_groups.values())
            contract_records = list(contract_groups.values())
        
        # 调用相应的保存函数
        collection_count = 0
        contract_count = 0
        
        if collection_records:
            # 调用 save_collection_data
            collection_data_str = json.dumps(collection_records, ensure_ascii=False)
            result = await save_collection_data(collection_data_str, month)
            result_dict = json.loads(result)
            if result_dict.get("success"):
                collection_count = result_dict.get("count", len(collection_records))
            else:
                logger.warning(f"保存回款数据失败: {result_dict.get('message')}")
        
        if contract_records:
            # 调用 save_contract_data
            contract_data_str = json.dumps(contract_records, ensure_ascii=False)
            result = await save_contract_data(contract_data_str, month)
            result_dict = json.loads(result)
            if result_dict.get("success"):
                contract_count = result_dict.get("count", len(contract_records))
            else:
                logger.warning(f"保存合同数据失败: {result_dict.get('message')}")
        
        return json.dumps(
            {
                "success": True,
                "message": f"成功保存 {collection_count} 条回款记录和 {contract_count} 条合同记录",
                "month": month,
                "collection_count": collection_count,
                "contract_count": contract_count,
            },
            ensure_ascii=False,
        )
    
    except Exception as e:
        logger.error(f"保存财务数据失败: {e}", exc_info=True)
        return json.dumps(
            {"success": False, "message": f"保存失败: {str(e)}"},
            ensure_ascii=False,
        )
