# 销售报表管理系统

一个基于 FastAPI 和 LLM 的智能销售报表管理系统，支持自然语言交互、数据提取、数据库操作和报表生成。

## 📋 项目简介

本项目是一个智能化的销售报表管理系统，通过大语言模型（LLM）实现自然语言交互，自动识别用户意图，提取结构化数据，并支持回款和合同数据的增删改查操作。系统可以自动生成 Excel 格式的汇总报表。

## ✨ 主要功能

- **意图识别**：自动识别用户输入的意图类型（chat/report/insert/update/delete/query）
- **数据提取**：使用 LLM 从自然语言中提取结构化数据（负责人、公司名称、项目类型等）
- **数据库操作**：支持回款和合同数据的增删改查
- **报表生成**：自动生成 Excel 格式的汇总报表，支持按公司、项目类型等多维度汇总
- **Web API**：提供 RESTful API 接口，支持前端调用
- **MCP 支持**：支持 Model Context Protocol，可与 LangChain 等框架集成

## 🛠️ 技术栈

- **后端框架**：FastAPI
- **数据库**：MySQL (使用 PyMySQL)
- **数据处理**：Pandas, OpenPyXL
- **AI/LLM**：OpenAI API (兼容其他 OpenAI 兼容的 API)
- **前端**：HTML + JavaScript (Tailwind CSS)

## 📦 安装依赖

### 1. 克隆项目

```bash
git clone <repository-url>
cd sell_report
```

### 2. 安装 Python 依赖

```bash
pip install -r requirements.txt
```

### 3. 配置数据库

修改 `config.py` 中的数据库配置：

```python
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "your_password",
    "database": "sell_report",
    "charset": "utf8mb4"
}
```

### 4. 创建数据库表

数据库表会在首次运行时自动创建，或手动执行 SQL 脚本创建表结构。

### 5. 配置 LLM API

修改 `config.py` 中的 OpenAI 配置：

```python
OPENAI_CONFIG = {
    "base_url": "http://your-llm-api-url/v1",
    "api_key": "your-api-key",
    "model": "your-model-name",
    "timeout": 60.0
}
```

## 🚀 快速开始

### 启动 API 服务器

```bash
python api.py
```

服务器将在 `http://localhost:8765` 启动。

### 访问 API 文档

启动服务器后，访问以下地址查看 API 文档：

- Swagger UI: `http://localhost:8765/docs`
- ReDoc: `http://localhost:8765/redoc`

### 启动前端

1. 打开 `html/index.html` 文件
2. 使用浏览器打开（推荐 Chrome）
3. 或使用 HBuilder 等工具运行

## 📡 API 接口说明

### 1. 意图识别

**接口**：`GET /intent`

**参数**：
- `context` (string): 用户输入的文本内容

**返回**：
```json
{
    "code": 200,
    "message": "success",
    "intent": "insert",
    "data": [...],
    "timestamp": "2026-02-06T12:29:59.988859"
}
```

**支持的意图类型**：
- `chat`: 普通对话
- `report`: 生成报表
- `insert`: 插入数据
- `update`: 更新数据
- `delete`: 删除数据
- `query`: 查询数据

### 2. 数据提取

**接口**：`GET /chat_extraction`

**参数**：
- `context` (string): 用户输入的文本内容

**返回**：
```json
{
    "code": 200,
    "message": "成功提取 1 条记录",
    "data": [
        {
            "数据类别": "回款",
            "负责人": "张三",
            "公司名称": "A公司",
            "项目类型": "软件开发",
            "项目名称": "ERP系统",
            "实际回款": 10000
        }
    ],
    "timestamp": "2026-02-06T12:29:59.988859"
}
```

### 3. 新增数据

**接口**：`POST /add_data`

**请求体**：
```json
{
    "数据类别": "回款",
    "负责人": "张三",
    "公司名称": "A公司",
    "项目类型": "软件开发",
    "项目名称": "ERP系统",
    "实际回款": 10000
}
```

### 4. 更新数据

**接口**：`POST /update_data`

**请求体**：同新增数据接口

### 5. 删除数据

**接口**：`POST /delete_data`

**请求体**：
```json
{
    "数据类别": "回款",
    "负责人": "张三",
    "公司名称": "A公司",
    "项目名称": "ERP系统"
}
```

### 6. 查询数据

**接口**：`POST /select_data`

**请求体**：
```json
{
    "数据类别": "回款",
    "负责人": "张三"
}
```

### 7. 生成报表

**接口**：`GET /report_generation`

**参数**：
- `year` (int): 年份
- `month` (int): 月份

## 📁 项目结构

```
sell_report/
├── api.py                 # FastAPI 主应用
├── config.py              # 配置文件（数据库、LLM等）
├── requirements.txt       # Python 依赖包
├── README.md             # 项目说明文档
│
├── chat_by_agent.py      # 聊天对话模块
├── intend_by_agent.py    # 意图识别模块
├── extra_query_by_agent.py  # 数据提取模块
├── json_to_database.py   # 数据库操作模块
├── generate_report.py    # 报表生成模块
├── db_connection.py      # 数据库连接管理
│
├── html/
│   └── index.html        # 前端页面
│
├── mcp/                  # MCP 服务器相关
│   ├── mcp_server.py     # MCP 服务器
│   ├── year_month_extractor.py  # 年月提取器
│   └── ...
│
└── data/                 # 数据目录
    ├── 明细表.xlsx       # 明细数据
    └── 2026年2月份汇总表.xlsx  # 生成的报表
```

## 💡 使用示例

### 示例 1：插入回款记录

**用户输入**：`"张三收款一万元"`

**系统处理流程**：
1. 意图识别 → `insert`
2. 数据提取 → 提取出负责人、金额等信息
3. 如果必填字段缺失，弹出表单补全
4. 提交后保存到数据库

### 示例 2：生成报表

**用户输入**：`"生成2026年2月的报表"`

**系统处理流程**：
1. 意图识别 → `report`
2. 年月提取 → 提取出 2026年2月
3. 生成 Excel 报表 → 保存到 `data/` 目录

### 示例 3：查询数据

**用户输入**：`"查询张三的所有回款记录"`

**系统处理流程**：
1. 意图识别 → `query`
2. 数据提取 → 提取查询条件
3. 执行查询 → 返回匹配的记录

## 🔧 配置说明

### 数据库配置

在 `config.py` 中配置数据库连接信息：

```python
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "your_password",
    "database": "sell_report",
    "charset": "utf8mb4"
}
```

### LLM API 配置

在 `config.py` 中配置 LLM API：

```python
OPENAI_CONFIG = {
    "base_url": "http://your-api-url/v1",
    "api_key": "your-api-key",
    "model": "your-model-name",
    "timeout": 60.0
}
```

### API 端口配置

在 `api.py` 文件末尾修改端口：

```python
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8765)
```

## 🐛 常见问题

### 1. 数据库连接失败

- 检查数据库服务是否启动
- 确认 `config.py` 中的数据库配置是否正确
- 确认数据库用户权限

### 2. LLM API 调用失败

- 检查网络连接
- 确认 API 地址和密钥是否正确
- 检查 API 服务是否可用

### 3. 前端无法连接后端

- 确认后端服务已启动
- 检查 CORS 配置
- 确认前端请求的端口号与后端一致

### 4. 报表生成失败

- 确认数据库中有对应年月的数据
- 检查 `data/` 目录的写入权限
- 确认 Excel 文件未被其他程序占用

## 📝 开发说明

### 添加新的意图类型

1. 在 `intend_by_agent.py` 中添加意图识别逻辑
2. 在 `api.py` 的 `/intent` 接口中添加对应的处理分支
3. 更新 `IntentEnum` 枚举

### 扩展数据字段

1. 修改数据库表结构
2. 更新 `config.py` 中的 `COLUMN_MAPPING`
3. 更新 `extra_query_by_agent.py` 中的提取逻辑

## 📄 许可证

本项目采用 MIT 许可证。

## 👥 贡献

欢迎提交 Issue 和 Pull Request！

## 📞 联系方式

如有问题或建议，请通过 Issue 联系。

---

**注意**：本项目中的 API 密钥和数据库密码仅为示例，实际使用时请修改为安全的值，并妥善保管。
