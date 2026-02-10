#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
启动纯HTTP桥接服务
只启动Dify-RAGFlow桥接服务器，不启动MCP服务器
"""

import os
import logging
from pathlib import Path
from dotenv import load_dotenv
import uvicorn

from ragflow_http_bridge import create_bridge_app

# 加载环境变量
env_file = Path(".env")
if env_file.exists():
    load_dotenv()

# 设置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


def main():
    """主函数"""
    print("=" * 60)
    print("🌉 Dify-RAGFlow HTTP桥接服务")
    print("=" * 60)

    # 检查环境变量
    if not env_file.exists():
        print("❌ 错误：未找到.env文件")
        print("请复制env_template.txt为.env并配置相关参数")
        return

    # 获取配置
    ragflow_url = os.getenv("RAGFLOW_BASE_URL", "http://localhost:8080")
    bridge_host = os.getenv("BRIDGE_SERVER_HOST", "0.0.0.0")
    bridge_port = int(os.getenv("BRIDGE_SERVER_PORT", "8001"))

    print(f"🔗 RAGFlow服务器: {ragflow_url}")
    print(f"🌉 桥接服务器: http://{bridge_host}:{bridge_port}")
    print(f"📖 API文档: http://{bridge_host}:{bridge_port}/docs")
    print(f"❤️  健康检查: http://{bridge_host}:{bridge_port}/health")
    print("-" * 60)
    print("💡 提示:")
    print("   - RAGFlow API密钥通过Dify请求传递")
    print("   - 在Dify中配置外部知识库时使用RAGFlow的API密钥")
    print("   - 知识库ID使用RAGFlow的数据集ID")
    print("=" * 60)

    # 创建并启动应用
    app = create_bridge_app()

    try:
        uvicorn.run(app, host=bridge_host, port=bridge_port, log_level="info")
    except KeyboardInterrupt:
        print("\n👋 服务已停止")


if __name__ == "__main__":
    main()
