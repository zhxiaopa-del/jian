# Agent 使用指南

## 为什么慢？

### 原因分析

1. **MCP 协议开销**：通过 stdio/HTTP 协议调用工具会增加延迟
2. **LLM 调用慢**：每次工具调用都需要 LLM 推理，本地模型可能较慢
3. **重复调用**：Agent 可能会重复调用相同的工具
4. **串行执行**：工具调用是串行的，无法并行

### 速度对比

| 方式 | 平均响应时间 | 说明 |
|------|------------|------|
| 直接调用工作流 | ~2-3秒 | 最快，推荐 |
| LangChain Agent（直接调用工具） | ~5-8秒 | 中等 |
| LangChain Agent（MCP 协议） | ~10-15秒 | 最慢 |

## 推荐方案

### 方案一：直接使用工作流（最快，推荐）

```python
from workflow import WorkflowProcessor

processor = WorkflowProcessor()
result = processor.process("张三收到A公司5万元回款", auto_confirm=True)
```

**优点**：
- ✅ 速度最快（~2-3秒）
- ✅ 无需额外依赖
- ✅ 代码简洁
- ✅ 完全控制流程

### 方案二：简化版 Agent（快速）

```python
from simple_agent import simple_agent

result = simple_agent("张三收到A公司5万元回款", auto_confirm=True)
```

**优点**：
- ✅ 速度快（~2-3秒）
- ✅ 封装好的接口
- ✅ 无需 LangChain

### 方案三：LangChain Agent（如果需要智能路由）

```python
# 需要安装: pip install langchain langchain-openai
from langchain_example import create_mcp_tools, main
import asyncio

# 使用
asyncio.run(main())
```

**优点**：
- ✅ 智能工具选择
- ✅ 自动处理复杂场景
- ⚠️ 速度较慢（~5-8秒）

## 速度优化技巧

### 1. 直接调用工具（最快）

```python
# ❌ 慢：通过 MCP 协议
from mcp_client import call_tool
result = await call_tool("recognize_intent", {"context": "你好"})

# ✅ 快：直接调用
from mcp_server import recognize_intent
result = recognize_intent("你好")
```

### 2. 批量处理

```python
# ❌ 慢：逐个处理
for data in data_list:
    insert_data("回款", data)

# ✅ 快：批量处理
for data in data_list:
    db_manager.insert("回款", data)  # 内部已优化
```

### 3. 缓存结果

```python
# 缓存意图识别结果
intent_cache = {}
def cached_recognize_intent(text):
    if text not in intent_cache:
        intent_cache[text] = recognize_intent(text)
    return intent_cache[text]
```

### 4. 设置超时

```python
# LLM 调用设置超时
llm = ChatOpenAI(timeout=30.0)  # 避免无限等待
```

### 5. 避免不必要的调用

```python
# ❌ 慢：每次都调用 extract_data
year = extract_data("2026年2月")  # 不需要 LLM

# ✅ 快：使用正则表达式
import re
year_match = re.search(r'(\d{4})年', "2026年2月")
year = int(year_match.group(1)) if year_match else datetime.now().year
```

## Skills 规范

已创建 `LANGCHAIN_SKILL.md` 文件，包含：
- 工作流规范
- 速度优化策略
- Agent 系统提示词
- 使用示例

## 推荐使用方式

**日常使用**：使用 `workflow.py` 或 `simple_agent.py`（速度快）

**复杂场景**：使用 `langchain_example.py`（需要智能路由时）

**MCP 集成**：在 Claude Desktop 中配置 MCP 服务器（最佳体验）
