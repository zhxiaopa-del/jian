---
name: analyze-data-report
description: Scans project data directory (doc, docx, pdf, images), collects file inventory and optional content summary, generates a structured Markdown report. Use when the user asks to analyze data, generate a data report, or summarize the contents of the data folder.
---

# Data Analysis and Report Generation

## Purpose

Analyze the project `data/` directory: list files by type and size, summarize document content when possible, and output a single Markdown report (e.g. `data/report.md` or `reports/data_analysis_report.md`).

## Workflow

1. **Scan** `data/` (and subdirs such as `images/`, `pdf_output/`).
2. **Collect**:
   - File tree or flat list: name, path, type, size.
   - Counts by type (pdf, docx, doc, png, etc.).
   - Total size.
3. **Optional content summary** (if dependencies allow):
   - PDF: first N characters via pymupdf.
   - DOCX: first N characters via docx2txt.
4. **Write** one Markdown report with the structure below.

## Report Template

Use this structure in the generated report:

```markdown
# Data 分析报告

## 1. 概览
- 统计时间
- 数据目录路径
- 文件总数、按类型数量、总大小

## 2. 文件清单
（表格或列表：文件名、类型、大小、路径）

## 3. 内容摘要（可选）
（对主要文档的简短摘要或首段）

## 4. 建议与说明
（如：缺失项、命名规范、后续可做的分析）
```

## Implementation

- Prefer reusing existing project logic (e.g. `reserve_to_markdown` for docx/pdf text) when generating content summary.
- Output path: `data/report.md` or `reports/data_analysis_report.md` (create `reports/` if needed).
- Keep the script runnable with: `python analyze_data_report.py` (or `python scripts/analyze_data_report.py`).

## When to Use

- User says "分析 data 数据" / "生成数据报告" / "分析一下 data 并生成报告".
- User asks for a summary or inventory of the `data/` folder.
