#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dify-RAGFlow桥接服务测试脚本
"""

import asyncio
import json
import os
from pathlib import Path
from dotenv import load_dotenv
import httpx

# 加载环境变量
env_file = Path(".env")
if env_file.exists():
    load_dotenv()


async def test_bridge_health():
    """测试桥接服务健康状态"""
    bridge_host = os.getenv("BRIDGE_SERVER_HOST", "localhost")
    bridge_port = os.getenv("BRIDGE_SERVER_PORT", "8001")
    url = f"http://{bridge_host}:{bridge_port}/health"

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=10)
            response.raise_for_status()
            result = response.json()

            print("✅ 桥接服务健康检查通过")
            print(f"   状态: {result.get('status')}")
            print(f"   RAGFlow地址: {result.get('ragflow_base_url')}")
            print(f"   API密钥已配置: {result.get('api_key_configured')}")
            return True

    except Exception as e:
        print(f"❌ 桥接服务健康检查失败: {e}")
        return False


async def test_dify_retrieval():
    """测试Dify外部知识库检索接口"""
    bridge_host = os.getenv("BRIDGE_SERVER_HOST", "localhost")
    bridge_port = os.getenv("BRIDGE_SERVER_PORT", "8001")
    url = f"http://{bridge_host}:{bridge_port}/retrieval"

    # 测试请求数据（符合Dify外部知识库API格式）
    test_data = {
        "knowledge_id": "test-dataset-id",  # 替换为真实的RAGFlow数据集ID
        "query": "什么是RAGFlow？",
        "retrieval_setting": {
            "top_k": 3,  # 期望返回的结果数量
            "score_threshold": 0.3,  # 相似度阈值
        },
        "metadata_condition": {  # 可选的元数据筛选条件
            "logical_operator": "and",
            "conditions": [],
        },
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer your-ragflow-api-key",  # 使用真实的RAGFlow API密钥进行测试
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url, json=test_data, headers=headers, timeout=30
            )

            print(f"📡 发送检索请求: {test_data['query']}")
            print(f"   状态码: {response.status_code}")

            if response.status_code == 200:
                result = response.json()
                records = result.get("records", [])
                print(f"✅ 检索成功，返回 {len(records)} 条记录")

                for i, record in enumerate(records[:2], 1):  # 只显示前2条
                    print(f"   记录 {i}:")
                    print(f"     标题: {record.get('title', 'N/A')}")
                    print(f"     得分: {record.get('score', 0):.3f}")
                    content = record.get("content", "")
                    if len(content) > 100:
                        content = content[:100] + "..."
                    print(f"     内容: {content}")

            else:
                error_detail = (
                    response.json()
                    if response.headers.get("content-type", "").startswith(
                        "application/json"
                    )
                    else response.text
                )
                print(f"❌ 检索失败: {error_detail}")

    except Exception as e:
        print(f"❌ 检索请求失败: {e}")


async def test_ragflow_direct():
    """测试RAGFlow直接调用（如果MCP服务器运行中）"""
    print("ℹ️  RAGFlow直接调用测试需要MCP服务器运行")
    print("   可以通过MCP客户端调用 ragflow_direct_retrieval 工具进行测试")


async def main():
    """主测试函数"""
    print("=" * 60)
    print("🧪 Dify-RAGFlow桥接服务测试")
    print("=" * 60)

    # 检查环境配置
    ragflow_url = os.getenv("RAGFLOW_BASE_URL")

    if not ragflow_url:
        print("❌ 错误：RAGFlow配置不完整")
        print("请确保在.env文件中配置了 RAGFLOW_BASE_URL")
        return

    print(f"🔗 RAGFlow地址: {ragflow_url}")
    print("🔑 API密钥: 通过Dify请求传递")
    print("-" * 60)

    # 测试桥接服务健康状态
    print("1. 测试桥接服务健康状态...")
    health_ok = await test_bridge_health()

    if not health_ok:
        print("\n❌ 桥接服务未运行或配置错误")
        print("请先启动服务: python main.py")
        return

    print("\n2. 测试Dify外部知识库检索接口...")
    await test_dify_retrieval()

    print("\n3. RAGFlow直接调用测试...")
    await test_ragflow_direct()

    print("\n" + "=" * 60)
    print("📋 测试完成")
    print("💡 提示:")
    print("   - 测试时请将 'your-ragflow-api-key' 替换为真实的RAGFlow API密钥")
    print("   - 如果检索失败，请检查RAGFlow服务器状态和API密钥")
    print("   - 如果返回空结果，请检查数据集ID和查询内容")
    print("   - 查看服务日志获取更多调试信息")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
