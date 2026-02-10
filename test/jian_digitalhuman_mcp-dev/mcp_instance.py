#!/usr/bin/env python3
"""
MCP Instance
"""

import os
from fastmcp import FastMCP
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

# 创建 MCP 服务器实例
server_name = os.getenv("MCP_SERVER_NAME", "mcp-sse-service")
server_port = os.getenv("MCP_SERVER_PORT", "8000")
server_version = os.getenv("MCP_SERVER_VERSION", "1.0.0")

# Try to pass version in constructor, fallback to basic constructor if not supported
try:
    mcp: FastMCP = FastMCP(server_name, debug=True, port=int(os.getenv("MCP_SERVER_PORT", "8000")), version=server_version)
except TypeError:
    # If version parameter is not supported in constructor, create without it
    mcp: FastMCP = FastMCP(server_name, debug=True, port=int(os.getenv("MCP_SERVER_PORT", "8000")))

# 注意：CORS 中间件将在 main.py 中服务器启动时通过 http_app 添加
# 这样可以避免干扰 fastmcp 的内部响应处理

# 添加健康检查端点
@mcp.custom_route("/health", methods=["GET"])
async def health_check(request: Request) -> JSONResponse:
    """健康检查端点，用于验证服务器是否正常运行"""
    return JSONResponse(
        content={
            "status": "healthy",
            "server_name": server_name,
            "version": server_version,
            "transport": "sse",
        }
    )
