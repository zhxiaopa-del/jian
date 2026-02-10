---
name: sell-report-mcp
description: MCP server for sales report management system. Provides tools for intent recognition, data extraction, database operations, and report generation. Use when working with sales reports, payment records, contract management, or when the user needs to interact with the sales report database.
---

# Sales Report MCP Server

MCP server providing tools for sales report management system including intent recognition, data extraction, database operations, and report generation.

## Available Tools

### 1. Intent Recognition
- **recognize_intent**: Classifies user input into 6 intent types
- Input: User text
- Output: Intent type (chat/report/insert/update/delete/query)
  - **chat**: Casual conversation, greetings, system inquiries
  - **report**: Generate, view, or export summary reports
  - **insert**: Add new data (payment or contract records)
  - **update**: Modify existing data
  - **delete**: Remove data records
  - **query**: Search and view specific data (not reports)

### 2. Data Extraction
- **extract_data**: Extracts structured data from user input
- Input: User text
- Output: Structured JSON with fields (负责人, 公司名称, 项目类型, 项目名称, etc.)
- Used for: insert, update operations

### 3. Database Operations
- **insert_data**: Insert new records (payment or contract)
  - Category: "payment" or "contract" (or Chinese: "回款" or "合同")
  - Data: Dictionary with field values (supports Chinese or English field names)
  
- **update_data**: Update existing records
  - Category: "payment" or "contract"
  - Data: Dictionary with fields to update
  
- **delete_data**: Delete records by matching fields
  - Category: "payment" or "contract"
  - Data: Dictionary with matching criteria (supports Chinese or English field names)
  
- **query_data**: Query records with filters
  - Category: "payment" or "contract"
  - Filters: Optional dictionary with filter conditions

### 4. Report Generation
- **generate_report**: Generate Excel summary reports
- Input: Year and month (integers)
- Output: Excel file path
- Generates: Monthly summary reports with payment and contract data

## Workflow

### Typical Usage Flow:

1. **Intent Recognition**: Call `recognize_intent` to determine user's intent
2. **Based on Intent**:
   - **chat**: Return friendly response
   - **report**: Call `generate_report` with year/month
   - **insert**: Call `extract_data` → Show data → Confirm → Call `insert_data`
   - **update**: Call `extract_data` → Show data → Confirm → Call `update_data`
   - **delete**: Call `extract_data` → Show data → Confirm → Call `delete_data`
   - **query**: Call `query_data` with filters

## Usage

All tools use English column names internally, but accept Chinese field names and automatically translate them. Output tables use Chinese column names for display.

## Database Schema

- Tables: `payment_records`, `contract_records`
- Columns: Use English names (responsible_person, company_name, project_type, etc.)
- Date field: `date` (DATE type, defaults to current date)

## Examples

### Insert Data
```python
recognize_intent("张三收到A公司5万元回款")  # Returns: "insert"
extract_data("张三收到A公司ERP项目5万元回款")  # Returns structured data
insert_data("回款", {...})  # Save to database
```

### Generate Report
```python
recognize_intent("生成2026年2月的汇总表")  # Returns: "report"
generate_report(2026, 2)  # Generate Excel report
```

### Query Data
```python
recognize_intent("查询张三的回款记录")  # Returns: "query"
query_data("回款", {"负责人": "张三"})  # Returns matching records
```
