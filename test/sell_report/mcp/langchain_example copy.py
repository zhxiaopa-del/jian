"""
LangChain Agent 使用 MCP 工具的工作流示例
LangChain Agent 直接使用 MCP 工具，自动编排工作流，无需单独的意图识别步骤
"""
import asyncio
import json
import sys
import io
from pathlib import Path

# 设置输出编码为 UTF-8（修复 Windows GBK 编码问题）
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

try:
    from langchain_mcp_adapters.client import MultiServerMCPClient
    from langchain.agents import create_agent
    from langchain_openai import ChatOpenAI
    from config import OPENAI_CONFIG
    LANGCHAIN_AVAILABLE = True
except ImportError as e:
    LANGCHAIN_AVAILABLE = False
    print(f"警告: 缺少依赖 - {e}")
    print("请运行: pip install langchain langchain-openai langchain-mcp-adapters")

# MCP 服务器配置（stdio 方式）
MCP_CONFIG = {
    "sell-report-mcp": {
        "transport": "stdio",
        "command": "python",
        "args": [str(Path(__file__).parent / "mcp_server.py")]
    }
}


async def main():
    """主函数：演示 LangChain Agent 直接使用 MCP 工具的工作流"""
    
    if not LANGCHAIN_AVAILABLE:
        print("[错误] LangChain 相关库未安装，无法运行")
        print("请运行: pip install langchain langchain-openai langchain-mcp-adapters")
        return
    
    print("="*60)
    print("LangChain Agent + MCP 工作流示例")
    print("="*60)
    print()
    
    # 1. 创建 MCP 客户端
    print("【步骤1】创建 MCP 客户端...")
    client = MultiServerMCPClient(MCP_CONFIG)
    
    # 2. 获取所有工具
    print("【步骤2】获取 MCP 工具...")
    tools = await client.get_tools()
    print(f"[成功] 获取到 {len(tools)} 个工具:")
    for i, tool in enumerate(tools, 1):
        print(f"   {i}. {tool.name} - {tool.description}")
    print()
    
    # 3. 创建 LLM
    print("【步骤3】创建 LLM...")
    llm = ChatOpenAI(
        model=OPENAI_CONFIG["model"],
        base_url=OPENAI_CONFIG["base_url"],
        api_key=OPENAI_CONFIG["api_key"],
        temperature=0,
        timeout=30.0
    )
    print("[成功] LLM 创建成功")
    print()
    
    # 4. 创建 Agent（系统提示：直接使用工具，无需意图识别）
    print("【步骤4】创建 LangChain Agent...")
    
    # 过滤掉 recognize_intent 工具，让 Agent 看不到它
    filtered_tools = [tool for tool in tools if tool.name != "recognize_intent"]
    print(f"[提示] 已过滤 recognize_intent 工具，剩余 {len(filtered_tools)} 个工具")
 
    agent = create_agent(llm, filtered_tools)
    print("[成功] Agent 创建成功")
    print()
    
    # 5. 使用 Agent 处理用户输入
    print("="*60)
    print("开始处理用户输入（Agent 自动编排工作流）")
    print("="*60)
    print()
    print("说明：")
    print("- 输入 'exit' 退出")
    print("- Agent 会根据你的输入自动调用相应的 MCP 工具")
    print("-" * 60)
    print()
    
    while True:
        try:
            user_input = input("\n请输入: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ['exit', 'quit', '退出']:
                print("\n再见！")
                break
            
            print("\n" + "-" * 60)
            print(f"用户输入: {user_input}")
            print("-" * 60)
            
            try:
                response = await agent.ainvoke({
                    "messages": [("user", user_input)]
                })
                
                print("\n【Agent 回复】")
                # 提取最后一条 AI 消息
                if isinstance(response, dict) and "messages" in response:
                    last_msg = response["messages"][-1]
                    if hasattr(last_msg, "content"):
                        print(last_msg.content)
                    else:
                        print(json.dumps(response, ensure_ascii=False, indent=2))
                else:
                    print(response)
                print()
                
            except Exception as e:
                print(f"[错误] 处理失败: {str(e)}")
                import traceback
                traceback.print_exc()
            
        except KeyboardInterrupt:
            print("\n\n再见！")
            break
        except Exception as e:
            print(f"\n[错误] 发生错误: {str(e)}")
            import traceback
            traceback.print_exc()
    
    # 6. 关闭客户端
    print("\n【步骤5】关闭 MCP 客户端...")
    await client.close()
    print("[成功] 完成")


if __name__ == "__main__":
    asyncio.run(main())
