#!/usr/bin/env python3
"""
吉安电子微服务平台MCP服务器

__author__ = "David"

"""

import asyncio
import logging
import os
import threading

from pathlib import Path
from dotenv import load_dotenv
import uvicorn

# Imports the MCP instance.
from mcp_instance import mcp

from tools.login import get_access_token
from ragflow_http_bridge import create_bridge_app


def setup_logging():
    """Setup logging configuration"""

    log_level = os.getenv("LOG_LEVEL", "INFO").upper()

    logging.basicConfig(
        level=getattr(logging, log_level),
        format="%(asctime)s file:%(filename)s line:%(lineno)d process:%(process)d thread:%(thread)d level:%(levelname)s\n%(message)s\n",
        datefmt="%Y-%m-%d %H:%M:%S.%f"[:-3],
    )


def load_environment():
    """Load environment variables from .env file"""

    env_file = Path(".env")

    if env_file.exists():
        load_dotenv()
        print(f"\nLoaded environment from {env_file}")
    else:
        raise Exception("No .env file found")


def start_bridge_server():
    """在单独线程中启动HTTP桥接服务器"""
    bridge_host = os.getenv("BRIDGE_SERVER_HOST", "0.0.0.0")
    bridge_port = int(os.getenv("BRIDGE_SERVER_PORT", "8001"))

    print(
        f"🌐 Starting Dify-RAGFlow Bridge Server on http://{bridge_host}:{bridge_port}"
    )
    print(f"📖 Bridge API Documentation: http://{bridge_host}:{bridge_port}/docs")

    app = create_bridge_app()
    uvicorn.run(app, host=bridge_host, port=bridge_port, log_level="info")


async def main():
    """Main application entry point"""

    # Load environment variables
    load_environment()

    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)

    # Imports all the tools to trigger auto-registration of tools
    import tools.get_freezing_station_data
    import tools.switch_frontend_page
    import tools.query_data
    import tools.save_financial_data
    import tools.generate_excel

    print("Starting ja_management mcp sse service...")
    print("\nTest to login jian_management: ", await get_access_token())

    # 启动HTTP桥接服务器（在单独线程中）
    bridge_thread = threading.Thread(target=start_bridge_server, daemon=True)
    bridge_thread.start()

    # 等待桥接服务器启动
    await asyncio.sleep(2)

    # Get server configuration
    host = os.getenv("MCP_SERVER_HOST", "0.0.0.0")
    port = int(os.getenv("MCP_SERVER_PORT", "8000"))

    # 获取工具列表，兼容不同fastmcp版本
    tool_dict = await mcp.get_tools()

    print(f"\navailable tool count: {len(tool_dict)}")

    # List all registered tools
    for tool_name in sorted(tool_dict.keys()):
        print(f"  • {tool_name}")

    print(f"\n🌐 MCP Server starting on http://{host}:{port}")
    print("📡 SSE endpoint: /sse")
    print("💚 Health check: /health")
    print("📖 Documentation: /docs")
    print("🛑 Press Ctrl+C to stop\n")

    # 在服务器启动前添加 CORS 中间件
    # 通过 http_app() 获取 FastAPI 应用实例并添加 CORS 支持
    try:
        from fastapi.middleware.cors import CORSMiddleware
        http_app = mcp.http_app()
        http_app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # 允许所有来源，生产环境建议限制特定域名
            allow_credentials=True,
            allow_methods=["*"],  # 允许所有 HTTP 方法
            allow_headers=["*"],  # 允许所有请求头
            expose_headers=["*"],  # 暴露所有响应头
        )
        logger.info("CORS middleware added successfully")
    except Exception as e:
        logger.warning(f"Failed to add CORS middleware: {e}")
        print(f"⚠️  Warning: Could not add CORS middleware: {e}")

    try:
        # Run the SSE server
        await mcp.run_async(transport="sse", host=host, port=port)
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
        print("\n👋 Server stopped gracefully")
    except Exception as e:
        logger.error(f"Server error: {e}")
        print(f"\n❌ Server error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
