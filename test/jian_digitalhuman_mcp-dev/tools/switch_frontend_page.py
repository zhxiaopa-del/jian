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


# @mcp.tool()
# async def get_all_frontend_pages() -> str:
#     """
#     获取数据大屏功能页面列表
#     """

#     pages = [
#         {"name": "项目总览", "path": "ProjectOverview"},
#         {"name": "报表中心", "path": "ReportCenter"},
#         {"name": "安全管理", "path": "SafetyManage"},
#         {"name": "视频监控", "path": "video"},
#         {"name": "智能冻结", "path": "IntelligentFreeze"},
#         {"name": "冻结模拟", "path": "IntelligentFreeze,freezeSimulation"},
#         {"name": "冻结站监测", "path": "IntelligentFreeze,freezeSite"},
#         {"name": "工艺流程图", "path": "IntelligentFreeze,processFlow"},
#         {"name": "螺杆机系统", "path": "IntelligentFreeze,screwMachine"},
#         {"name": "测温系统", "path": "IntelligentFreeze,temperatureMeasurement"},
#         {"name": "盐水系统", "path": "IntelligentFreeze,salineWater"},
#         {"name": "智能钻孔", "path": "IntelligentDrilling"},
#         {"name": "钻孔总览", "path": "IntelligentDrilling,drillingOverview"},
#         {"name": "形象进度", "path": "IntelligentDrilling,progressVisual"},
#         {"name": "质量报表", "path": "IntelligentDrilling,qualityReport"},
#     ]

#     print("获取数据大屏功能页面列表")
#     print(pages)
#     return pages

@mcp.tool()
async def get_all_frontend_pages() -> str:
    """
    获取数据大屏功能页面列表
    """

    print("获取可查询的大屏页面列表：")
    result = await get_request(
        uri="/datapage/getAllPages",
        params={}
    )

    print("result:", result)

    # result 是字典，使用 .get() 方法安全访问
    if isinstance(result, dict):
        return json.dumps(
            result.get("data", result), ensure_ascii=False
        )  # 如果没有 data 字段，返回整个 result

    
    return result


@mcp.tool()
async def switch_frontend_page(page_path: str) -> str:
    """
    打开或切换数据大屏功能页面

    Args:
        page_path: 数据大屏功能页面路径
    Returns:
        操作结果
    """

    data: dict = {"pagePath": page_path}

    result = await post_request(
        uri="/datapage/switchPage", data=data
    )

    print(f"切换数据大屏功能页面:{page_path}")
    print(result)
    if isinstance(result, dict):
        return json.dumps(
            result.get("data", result), ensure_ascii=False
        )  # 如果没有 data 字段，返回整个 result
    return result
