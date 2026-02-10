---
name: langchain-mcp-workflow
description: LangChain Agent 工作流规范，使用 MCP 工具处理销售报表任务。优化速度，避免不必要的调用。
---

# LangChain MCP 工作流规范

## 核心原则

1. **直接调用工具**：不使用 MCP 协议层，直接调用工具函数，提高速度
2. **智能路由**：根据意图自动选择工具，减少不必要的调用
3. **批量处理**：一次提取多条数据，批量操作
4. **缓存结果**：相同查询缓存结果，避免重复调用

## 工作流规范

### 标准流程

```
用户输入
   ↓
recognize_intent (必须第一步)
   ↓
根据意图路由
   ↓
┌─────────┬──────────┬─────────┬─────────┬─────────┬─────────┐
│  chat   │  report  │ insert  │ update  │ delete  │  query  │
└─────────┴──────────┴─────────┴─────────┴─────────┴─────────┘
   │          │          │          │          │          │
直接回复   生成报表   提取+保存   提取+更新   提取+删除   提取+查询
```

### 详细规则

#### 1. chat（闲聊）
- **操作**：直接回复，不调用任何工具
- **速度**：最快（无工具调用）

#### 2. report（生成报表）
- **步骤**：
  1. 从输入中提取 year 和 month（使用正则，不调用 LLM）
  2. 直接调用 `generate_report(year, month)`
- **优化**：避免使用 extract_data，直接用正则提取年月

#### 3. insert（新增数据）
- **步骤**：
  1. 调用 `extract_data` 提取数据
  2. 检查必填字段
  3. 调用 `insert_data` 保存
- **优化**：批量处理多条数据

#### 4. update（修改数据）
- **步骤**：
  1. 调用 `extract_data` 提取数据
  2. 调用 `update_data` 更新
- **优化**：确保数据包含定位字段（负责人+公司+项目）

#### 5. delete（删除数据）
- **步骤**：
  1. 调用 `extract_data` 提取删除条件
  2. 调用 `delete_data` 删除
- **优化**：删除前先查询确认，避免误删

#### 6. query（查询数据）
- **步骤**：
  1. 调用 `extract_data` 提取查询条件
  2. 调用 `query_data` 查询
- **优化**：使用缓存，相同查询直接返回

## 速度优化策略

### 1. 避免不必要的 LLM 调用
- 使用正则表达式提取年月（report）
- 使用规则匹配作为后备（intent recognition）

### 2. 批量操作
- 一次提取多条数据，批量插入/更新/删除

### 3. 缓存机制
- 缓存意图识别结果（相同输入）
- 缓存查询结果（相同条件）

### 4. 超时设置
- LLM 调用设置超时（30秒）
- 数据库操作设置超时（10秒）

### 5. 并行处理
- 多个独立操作并行执行
- 使用 asyncio 并发处理

## Agent 系统提示词

```
你是一个销售报表助手。当用户提出请求时，请遵循以下工作流：

**第一步：意图识别（必须）**
- 调用 recognize_intent 识别用户意图

**第二步：根据意图执行**

1. **chat**：直接友好回复，不调用其他工具

2. **report**：
   - 从输入中提取年份和月份（使用正则表达式）
   - 调用 generate_report({"year": 2026, "month": 2})

3. **insert**：
   - 调用 extract_data 提取数据
   - 检查必填字段（负责人、公司名称、项目类型、项目名称）
   - 调用 insert_data({"category": "回款", "data": {...}})

4. **update**：
   - 调用 extract_data 提取数据
   - 调用 update_data({"category": "回款", "data": {...}})

5. **delete**：
   - 调用 extract_data 提取删除条件
   - 调用 delete_data({"category": "回款", "data": {...}})

6. **query**：
   - 调用 extract_data 提取查询条件
   - 调用 query_data({"category": "回款", "filters": {...}})

**重要规则**：
- 所有工具参数必须是 JSON 字符串格式
- 不要重复调用相同的工具（除非必要）
- 优先使用正则表达式提取简单信息（如年月），避免调用 extract_data
- 批量操作时，一次处理多条数据
```

## 使用示例

### 快速模式（推荐）

```python
from langchain_example import create_mcp_tools
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI

# 创建工具（直接调用，速度快）
tools = create_mcp_tools()

# 创建 LLM（设置超时）
llm = ChatOpenAI(
    model="qwen3-14b",
    base_url="http://10.3.0.16:8100/v1",
    api_key="222442bb160d5081b9e38506901d6889",
    temperature=0,
    timeout=30.0
)

# 创建 Agent
agent = create_agent(llm, tools)

# 使用
response = await agent.ainvoke({
    "messages": [("user", "生成2026年2月的汇总表")]
})
```

## 性能对比

### 直接调用模式（当前）
- 意图识别：~1秒
- 数据提取：~2秒
- 数据库操作：~0.5秒
- **总计**：~3.5秒

### MCP 协议模式（慢）
- 意图识别：~3秒（协议开销）
- 数据提取：~5秒（协议开销）
- 数据库操作：~2秒（协议开销）
- **总计**：~10秒

## 注意事项

1. **工具参数格式**：必须是 JSON 字符串
2. **错误处理**：所有工具调用都要处理异常
3. **超时设置**：避免长时间等待
4. **日志记录**：记录每次工具调用，便于调试
