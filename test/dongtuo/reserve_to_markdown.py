"""
将 data 文件夹内的文档（doc/docx/pdf）转成 Markdown，图片以 URL 形式写入。
图片会保存到 output/images/，Markdown 中使用可配置的 base_url 或相对路径。
"""
from pathlib import Path

# 路径与 URL 配置
DATA_DIR = Path(__file__).resolve().parent / "data"
OUTPUT_DIR = DATA_DIR / "markdown_output"
IMAGES_DIR = OUTPUT_DIR / "images"
# 图片 URL 前缀：若部署到网站可设为 "https://yoursite.com/files"，否则用相对路径
IMAGE_BASE_URL = ""  # 留空则使用相对路径 ./images/xxx


def _image_url(filename: str) -> str:
    """生成图片在 Markdown 中的 URL。"""
    if IMAGE_BASE_URL:
        return f"{IMAGE_BASE_URL.rstrip('/')}/images/{filename}"
    return f"./images/{filename}"


def _ensure_dirs():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)


def docx_to_md(path: Path, stem: str) -> str:
    """将 docx（或尝试 doc）转为 Markdown 文本，图片保存到 IMAGES_DIR 并返回 URL 形式。"""
    try:
        import docx2txt
    except ImportError:
        raise ImportError("请安装: pip install docx2txt")

    img_dir = IMAGES_DIR / stem
    img_dir.mkdir(parents=True, exist_ok=True)
    text = docx2txt.process(str(path), str(img_dir))
    if not text or not text.strip():
        text = "(无文本内容)\n"

    # 收集本次导出的图片，生成 Markdown 中的 URL
    base = path.stem
    url_lines = []
    if img_dir.exists():
        for i, f in enumerate(sorted(img_dir.iterdir())):
            if not f.is_file():
                continue
            ext = f.suffix.lower() if f.suffix else ".png"
            if ext not in (".png", ".jpg", ".jpeg", ".gif", ".bmp", ".emf", ".wmf"):
                ext = ".png"
            unique_name = f"{base}_{i}{ext}"
            dest = IMAGES_DIR / unique_name
            if f.resolve() != dest.resolve():
                dest.write_bytes(f.read_bytes())
            url_lines.append(f"![]({_image_url(unique_name)})")

    md = text.strip()
    if url_lines:
        md += "\n\n## 附图\n\n" + "\n\n".join(url_lines)
    return md


def pdf_to_md(path: Path, stem: str) -> str:
    """将 pdf 转为 Markdown 文本，图片保存到 IMAGES_DIR 并以 URL 形式写入。"""
    try:
        import fitz  # pymupdf
    except ImportError:
        raise ImportError("请安装: pip install pymupdf")

    doc = fitz.open(path)
    parts = []
    img_index = [0]  # 用列表以便在闭包里修改

    for page in doc:
        blk_list = page.get_text("blocks")
        for b in blk_list:
            x0, y0, x1, y1, block_text, block_no, block_type = b[:7]
            if block_text.strip():
                parts.append(block_text.strip())

        # 当前页图片
        for img in page.get_images():
            xref = img[0]
            try:
                pix = fitz.Pixmap(doc, xref)
                if pix.n - pix.alpha < 4:
                    ext = "png"
                else:
                    ext = "png"
                name = f"{stem}_p{page.number}_{img_index[0]}.{ext}"
                img_index[0] += 1
                dest = IMAGES_DIR / name
                pix.save(str(dest))
                parts.append(f"![]({_image_url(name)})")
            except Exception:
                pass

    doc.close()
    md = "\n\n".join(parts) if parts else "(无内容)"
    return md


def file_to_md(path: Path) -> tuple[str, str] | None:
    """单文件转 Markdown。返回 (stem, md_content)，失败返回 None。"""
    stem = path.stem
    suffix = path.suffix.lower()

    if suffix == ".pdf":
        content = pdf_to_md(path, stem)
    elif suffix in (".docx", ".doc"):
        content = docx_to_md(path, stem)
    else:
        return None

    return stem, content


def run():
    """扫描 data 下 doc/docx/pdf，转成 Markdown，图片以 URL 形式写入。"""
    _ensure_dirs()
    data_path = Path(DATA_DIR)
    if not data_path.exists():
        print(f"未找到目录: {DATA_DIR}")
        return

    exts = {".doc", ".docx", ".pdf"}
    files = [f for f in data_path.iterdir() if f.is_file() and f.suffix.lower() in exts]
    if not files:
        print("data 下没有 .doc / .docx / .pdf 文件")
        return

    for path in files:
        try:
            out = file_to_md(path)
            if out is None:
                continue
            stem, md = out
            out_path = OUTPUT_DIR / f"{stem}.md"
            out_path.write_text(md, encoding="utf-8")
            print(f"已生成: {out_path}")
        except Exception as e:
            print(f"跳过 {path.name}: {e}")


if __name__ == "__main__":
    run()
