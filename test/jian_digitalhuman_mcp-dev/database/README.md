# 财务数据管理模块

## 概述

本模块提供了财务数据（回款和合同）的数据库存储和Excel生成功能。

## 数据库表结构

### 1. 回款记录表 (collection_records)

| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | Integer | 主键，自增 |
| responsible_person | String(100) | 负责人 |
| project_type | String(100) | 项目类型 |
| project_name | String(200) | 项目名称 |
| estimated_possible_at_start | Numeric(15,2) | 月初预计可能回款 |
| estimated_confirmed_at_start | Numeric(15,2) | 月初预计确定回款 |
| possible_collection | Numeric(15,2) | 可能回款 |
| confirmed_collection | Numeric(15,2) | 确定回款 |
| actual_collection | Numeric(15,2) | 实际回款 |
| uncollected_amount | Numeric(15,2) | 未回款金额 |
| reason_for_non_completion | Text | 未完成原因 |
| solution | Text | 解决办法 |
| month | String(20) | 月份，格式：YYYY-MM |
| is_subtotal | Integer | 是否为小计行：0-否，1-是 |
| created_at | DateTime | 创建时间 |
| updated_at | DateTime | 更新时间 |

### 2. 合同记录表 (contract_records)

| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | Integer | 主键，自增 |
| responsible_person | String(100) | 负责人 |
| company_name | String(200) | 公司名称（可选） |
| project_name | String(200) | 项目名称 |
| estimated_possible_at_start | Numeric(15,2) | 月初预计可能合同 |
| estimated_confirmed_at_start | Numeric(15,2) | 月初预计确定合同 |
| possible_contract | Numeric(15,2) | 可能合同 |
| confirmed_contract | Numeric(15,2) | 确定合同 |
| actual_contract | Numeric(15,2) | 实际合同 |
| completion_status | Text | 完成情况 |
| month | String(20) | 月份，格式：YYYY-MM |
| is_subtotal | Integer | 是否为小计行：0-否，1-是 |
| created_at | DateTime | 创建时间 |
| updated_at | DateTime | 更新时间 |

## 数据库文件位置

数据库文件默认保存在：`data/financial_data.db`

## 使用示例

### 保存回款数据

```python
data = [
    {
        "responsible_person": "李晓林",
        "project_type": "动环项目",
        "project_name": "项目A",
        "estimated_possible_at_start": 100000.00,
        "estimated_confirmed_at_start": 80000.00,
        "possible_collection": 90000.00,
        "confirmed_collection": 75000.00,
        "actual_collection": 70000.00,
        "uncollected_amount": 5000.00,
        "reason_for_non_completion": "客户资金紧张",
        "solution": "已沟通，预计下月回款"
    }
]

result = await save_collection_data(
    data=json.dumps(data),
    month="2026-02"
)
```

### 保存合同数据

```python
data = [
    {
        "responsible_person": "李晓林",
        "company_name": "XX公司",
        "project_name": "项目B",
        "estimated_possible_at_start": 200000.00,
        "estimated_confirmed_at_start": 180000.00,
        "possible_contract": 190000.00,
        "confirmed_contract": 175000.00,
        "actual_contract": 170000.00,
        "completion_status": "进行中"
    }
]

result = await save_contract_data(
    data=json.dumps(data),
    month="2026-02"
)
```

### 从Agent工作流保存数据（推荐）

这是处理agent统一格式数据的推荐方法：

```python
data = [
    {
        "日期": "2026-02-01",
        "公司名": "北京工程项目",
        "负责人": "丁辉",
        "项目分类": "工程",
        "项目名称": "北京工程项目",
        "类型": "实际回款",
        "事件内容": 50000
    },
    {
        "日期": "2026-02-01",
        "公司名": "上海项目",
        "负责人": "丁辉",
        "项目分类": "工程",
        "项目名称": "上海项目",
        "类型": "未完成原因",
        "事件内容": "老板出差，合同还是没签成"
    }
]

result = await save_financial_data_from_agent(
    data=json.dumps(data),
    month="2026-02"  # 可选，如果不提供会从日期字段提取
)
```

**支持的类型映射：**

回款相关类型：
- `实际回款` → actual_collection
- `确定回款` → confirmed_collection
- `可能回款` → possible_collection
- `月初预计可能回款` → estimated_possible_at_start
- `月初预计确定回款` → estimated_confirmed_at_start
- `未回款金额` → uncollected_amount
- `未完成原因` → reason_for_non_completion
- `解决办法` → solution

合同相关类型：
- `实际合同` → actual_contract
- `确定合同` → confirmed_contract
- `可能合同` → possible_contract
- `月初预计可能合同` → estimated_possible_at_start
- `月初预计确定合同` → estimated_confirmed_at_start
- `完成情况` → completion_status

**数据聚合规则：**
- 同一个项目（负责人+项目名称+项目分类）的多条记录会自动合并
- 数值类型字段会累加（如多次"实际回款"会累加）
- 文本类型字段会追加（用"；"分隔）

### 生成Excel文件

```python
result = await generate_excel_from_template(
    month="2026-02",
    output_path="data/2026年2月份预计回款、合同表.xlsx"
)
```

## MCP工具

本模块提供了以下MCP工具：

1. **save_financial_data_from_agent** - 从agent工作流保存财务数据（统一格式，推荐使用）
2. **save_collection_data** - 保存回款数据（直接格式）
3. **save_contract_data** - 保存合同数据（直接格式）
4. **generate_excel_from_template** - 从数据库生成Excel文件

这些工具可以通过MCP服务器调用，agent可以使用它们来存储和生成财务报表。
