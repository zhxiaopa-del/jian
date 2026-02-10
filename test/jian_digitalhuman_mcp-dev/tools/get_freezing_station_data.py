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
async def get_temp_hole_data(depth: int) -> str:
    """
    获取所有测温孔某个深度（单位米）的测点数据

    Args:
        depth: 深度（单位米）

    Returns:
        所有测温孔某个深度（单位米）的测点数据
    """

    params: dict = {"type": "temp_hole", "depth": depth}
    return await get_request(
        uri="/mineMultipleProjects/digitalHumans/getIntelligentAsk", params=params
    )


@mcp.tool()
async def get_freeze_hole_data() -> str:
    """
    获取所有冻结孔的测温数据

    Args:
        None

    Returns:
        所有冻结孔的测温数据
    """

    params: dict = {"type": "freeze_hole"}
    return await get_request(
        uri="/mineMultipleProjects/digitalHumans/getIntelligentAsk", params=params
    )


@mcp.tool()
async def get_loop_temp_data() -> str:
    """
    获取制冷盐水干管去、回路温度数据

    Args:
        None

    Returns:
        制冷盐水干管去、回路温度数据
    """

    params: dict = {"type": "loop_temp"}
    return await get_request(
        uri="/mineMultipleProjects/digitalHumans/getIntelligentAsk", params=params
    )


@mcp.tool()
async def get_pip_pressure_data() -> str:
    """
    获取制冷盐水干管压力数据

    Args:
        None

    Returns:
        制冷盐水干管压力数据
    """

    params: dict = {"type": "pipe_pressure"}
    return await get_request(
        uri="/mineMultipleProjects/digitalHumans/getIntelligentAsk", params=params
    )


@mcp.tool()
async def get_energy_consumption_data(
    month: Optional[str] = None, date: Optional[str] = None
) -> str:
    """
    获取冻结站指定时间的能耗数据

    Args:
        month: 月份，格式为yyyy-MM
        date: 日期，格式为yyyy-MM-dd

    Returns:
        冻结站能耗数据
    """

    params: dict = {"type": "energy"}
    if month is not None:
        params["month"] = month
    if date is not None:
        params["date"] = date
    return await get_request(
        uri="/mineMultipleProjects/digitalHumans/getIntelligentAsk", params=params
    )


@mcp.tool()
async def get_chiller_list() -> str:
    """
    获取所有制冷机组\压缩机组\冷水机组\螺杆机的名称列表

    Args:
        None

    Returns:
        所有制冷机组\压缩机组\冷水机组\螺杆机的名称列表
    """

    params: dict = {"type": "chiller"}
    return await get_request(
        uri="/mineMultipleProjects/digitalHumans/getIntelligentAsk", params=params
    )


@mcp.tool()
async def get_chiller_data(chiller: str) -> str:
    """
    获取指定名称或编号的制冷机组\压缩机组\冷水机组\螺杆机的数据

    Args:
        chiller: 制冷机组\压缩机组\冷水机组\螺杆机的名称或编号

    Returns:
        指定制冷机组\压缩机组\冷水机组\螺杆机的数据
    """

    params: dict = {"type": "chiller", "chiller": chiller}
    return await get_request(
        uri="/mineMultipleProjects/digitalHumans/getIntelligentAsk", params=params
    )
