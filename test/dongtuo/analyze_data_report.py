"""
利用 analyze-data-report 技能：扫描 data/ 目录，统计文件与可选内容摘要，生成 Markdown 报告。
运行: python analyze_data_report.py
"""
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# 项目 data 目录
DATA_DIR = Path(__file__).resolve().parent / "data"
REPORT_PATH = DATA_DIR / "report.md"
# 内容摘要最大字符数（每文档）
SUMMARY_CHARS = 800


def _size_fmt(size: int) -> str:
    if size < 1024:
        return f"{size} B"
    if size < 1024 * 1024:
        return f"{size / 1024:.1f} KB"
    return f"{size / (1024 * 1024):.1f} MB"


def _get_file_tree(root: Path, prefix: str = "") -> list[tuple[str, Path, bool]]:
    """返回 (显示路径, 绝对路径, 是否目录) 列表，跳过 .DS_Store。"""
    rows = []
    try:
        items = sorted(root.iterdir(), key=lambda p: (p.is_file(), p.name.lower()))
    except OSError:
        return rows
    for p in items:
        if p.name.startswith(".") or p.name == ".DS_Store":
            continue
        rel = f"{prefix}{p.name}"
        rows.append((rel, p, p.is_dir()))
        if p.is_dir():
            rows.extend(_get_file_tree(p, prefix + p.name + "/"))
    return rows


def _file_stats(root: Path) -> tuple[list[tuple[str, str, int, str]], dict[str, int], int]:
    """(文件列表 (相对路径, 后缀, 大小, 大小字符串), 按类型计数, 总字节)。"""
    files: list[tuple[str, str, int, str]] = []
    by_ext: dict[str, int] = defaultdict(int)
    total = 0
    for rel, p, is_dir in _get_file_tree(root):
        if is_dir:
            continue
        try:
            size = p.stat().st_size
        except OSError:
            size = 0
        ext = p.suffix.lower() if p.suffix else "(无后缀)"
        by_ext[ext] += 1
        total += size
        files.append((rel, ext, size, _size_fmt(size)))
    return files, dict(by_ext), total


def _extract_pdf_preview(path: Path, max_chars: int) -> str:
    try:
        import fitz
        doc = fitz.open(path)
        parts = []
        n = 0
        for page in doc:
            if n >= max_chars:
                break
            t = page.get_text().strip()
            if t:
                parts.append(t)
                n += len(t)
        doc.close()
        text = "\n".join(parts)[:max_chars]
        return text.rstrip() + ("…" if len(text) >= max_chars else "")
    except Exception:
        return ""


def _extract_docx_preview(path: Path, max_chars: int) -> str:
    try:
        import docx2txt
        text = docx2txt.process(str(path))
        if not text or not text.strip():
            return ""
        return text.strip().replace("\r\n", "\n")[:max_chars].rstrip() + ("…" if len(text.strip()) > max_chars else "")
    except Exception:
        return ""


def run() -> None:
    if not DATA_DIR.exists():
        print(f"未找到目录: {DATA_DIR}")
        return

    files, by_ext, total = _file_stats(DATA_DIR)
    doc_exts = {".pdf", ".doc", ".docx"}
    summaries: list[tuple[str, str]] = []

    for rel, ext, _, _ in files:
        if ext not in doc_exts:
            continue
        full = DATA_DIR / rel
        if not full.is_file():
            continue
        if ext == ".pdf":
            preview = _extract_pdf_preview(full, SUMMARY_CHARS)
        elif ext in (".doc", ".docx"):
            preview = _extract_docx_preview(full, SUMMARY_CHARS)
        else:
            continue
        if preview:
            summaries.append((rel, preview))

    # 写报告
    lines = [
        "# Data 分析报告",
        "",
        "## 1. 概览",
        "",
        f"- **统计时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"- **数据目录**: `{DATA_DIR}`",
        f"- **文件总数**: {len(files)}",
        f"- **总大小**: {_size_fmt(total)}",
        "",
        "### 按类型数量",
        "",
        "| 类型 | 数量 |",
        "|------|------|",
    ]
    for ext in sorted(by_ext.keys(), key=lambda x: (-by_ext[x], x)):
        lines.append(f"| {ext or '(无后缀)'} | {by_ext[ext]} |")
    lines.extend(["", "## 2. 文件清单", ""])
    lines.append("| 相对路径 | 类型 | 大小 |")
    lines.append("|----------|------|------|")
    for rel, ext, _, size_str in sorted(files, key=lambda x: x[0]):
        lines.append(f"| {rel} | {ext or '-'} | {size_str} |")
    lines.extend(["", "## 3. 内容摘要", ""])
    if summaries:
        for rel, text in summaries:
            lines.append(f"### {rel}")
            lines.append("")
            lines.append(text.replace("\n\n", "\n\n").strip())
            lines.append("")
    else:
        lines.append("（未提取到文档摘要，请确认已安装 pymupdf、docx2txt。）")
        lines.append("")
    lines.extend([
        "## 4. 建议与说明",
        "",
        "- 报告由 `analyze_data_report.py` 自动生成，对应技能：`.cursor/skills/analyze-data-report`。",
        "- 若需更新报告，重新运行该脚本即可。",
        "",
    ])

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"已生成报告: {REPORT_PATH}")


if __name__ == "__main__":
    run()
