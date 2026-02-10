import httpx
from httpx import Response
import os
from typing import Dict, Any, Optional
import json
from datetime import datetime
import logging
from .request_api import get_request, post_request

from mcp_instance import mcp

logger = logging.getLogger(__name__)


@mcp.tool()
async def get_data_class_list() -> str:
    """
    获取数据分类列表

    Args:
        None

    Returns:
        数据分类列表
    """

    params: dict = {}

    print("获取可查询的数据类型列表：")
    result = await get_request(
        uri="/dataentity/getDataClassList", params=params
    )

    # result 是字典，使用 .get() 方法安全访问
    if isinstance(result, dict):
        return json.dumps(
            result.get("data", result), ensure_ascii=False
        )  # 如果没有 data 字段，返回整个 result
    return result


@mcp.tool()
async def get_data_query_condition_fields(data_class_name: str) -> str:
    """
    获取某个分类数据的查询条件字段列表

    Args:
        dataentityName: 数据分类名称

    Returns:
        某个分类数据的查询条件字段列表及字段描述（字段名、字段类型、字段描述、 示例值）
    """

    params: dict = {"dataentityName": data_class_name}

    print(f"获取查询{data_class_name}数据类型的参数信息：")
    result = await get_request(
        uri="/dataentityParams/getDataQueryConditionFields",
        params=params,
    )

    # result 是字典，使用 .get() 方法安全访问
    if isinstance(result, dict):
        return json.dumps(
            result.get("data", result), ensure_ascii=False
        )  # 如果没有 data 字段，返回整个 result
    return result


@mcp.tool()
async def get_data_query_result(data_class_name: str, condition: str) -> object:
    """
    获取某个分类数据的查询结果

    Args:
        data_class_name: 数据分类名称
        condition: 查询条件 json字符串

    Returns:
        某个分类数据的查询结果
    """

    data: dict = {
        "data_class_name": data_class_name,
        "condition": json.loads(condition),
    }

    print("获取某个分类数据的查询结果 data:", data)

    result = await post_request(
        uri="/datasource/getDataQueryResult", data=data
    )

    print("获取某个分类数据的查询结果 result:", result)

    # result 是字典，使用 .get() 方法安全访问
    if isinstance(result, dict):
        return result.get("data", result)  # 如果没有 data 字段，返回整个 result
    return result
