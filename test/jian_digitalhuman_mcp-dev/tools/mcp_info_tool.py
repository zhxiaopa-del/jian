"""
获取吉安大平台MCP服务器状态
"""

import socket
from datetime import datetime

# 导入独立的 MCP 实例
from mcp_instance import mcp


@mcp.tool()
async def get_mcp_info() -> str:
    """
    获取吉安大平台MCP服务器状态

    Returns:
        运行状态
    """

    time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ip = socket.gethostbyname(socket.gethostname())
    return (
        f"MCP服务目前运行正常，服务名称：{mcp.name}，服务地址：{ip}，当前时间：{time}"
    )
