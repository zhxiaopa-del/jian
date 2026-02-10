"""
根据检索结果中的 image_id 从 RAGFlow 拉取切片图片并保存到本地，便于查看。
RAGFlow 官方 HTTP API 未文档化「按 image_id 取图」接口，本脚本先尝试「按 file_id 下载」接口。
"""
from pathlib import Path
import re
import httpx

from similarity_question import (
    BASE_URL,
    API_KEY,
    DEFAULT_DATASET_ID,
    retrieve_similar_topk,
)

# 图片保存目录（项目下）
IMAGES_DIR = Path(__file__).resolve().parent / "data" / "ragflow_images"
IMAGES_DIR.mkdir(parents=True, exist_ok=True)


def _safe_filename(image_id: str, suffix: str = ".png") -> str:
    """用 image_id 生成合法文件名。"""
    safe = re.sub(r"[^\w\-]", "_", image_id)
    return f"{safe}{suffix}" if not safe.endswith(suffix) else safe


def fetch_image_by_file_id(image_id: str) -> tuple[bytes | None, str | None]:
    """
    尝试用 RAGFlow「下载文件」接口 GET /api/v1/file/get/{file_id} 拉取图片。
    使用 image_id 作为 file_id。成功返回 (bytes, content_type)，失败返回 (None, error_msg)。
    """
    url = f"{BASE_URL.rstrip('/')}/api/v1/file/get/{image_id}"
    headers = {"Authorization": f"Bearer {API_KEY}"}
    try:
        with httpx.Client(timeout=15) as client:
            resp = client.get(url, headers=headers)
        if resp.status_code != 200:
            return None, f"HTTP {resp.status_code}"
        ct = (resp.headers.get("content-type") or "").lower()
        if "application/json" in ct:
            try:
                body = resp.json()
                code = body.get("code")
                msg = body.get("message", body)
                return None, f"API code={code} message={msg}"
            except Exception:
                return None, "API returned JSON error"
        return resp.content, ct or None
    except Exception as e:
        return None, str(e)


def extension_from_content_type(content_type: str | None) -> str:
    if not content_type:
        return ".png"
    if "jpeg" in content_type or "jpg" in content_type:
        return ".jpg"
    if "png" in content_type:
        return ".png"
    if "webp" in content_type:
        return ".webp"
    if "gif" in content_type:
        return ".gif"
    return ".png"


def fetch_and_save_chunk_images(
    question: str,
    dataset_id: str = DEFAULT_DATASET_ID,
    top_k: int = 3,
    out_dir: Path | None = None,
) -> list[dict]:
    """
    检索与 question 相似的 top_k 切片，对每个带 image_id 的切片尝试拉取图片并保存到 out_dir。
    返回列表，每项为 { "chunk": chunk, "image_id": str, "saved_path": Path | None, "error": str | None }。
    """
    out_dir = out_dir or IMAGES_DIR
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    chunks = retrieve_similar_topk(question, dataset_id=dataset_id, top_k=top_k)
    results = []

    for i, ch in enumerate(chunks):
        image_id = (ch.get("image_id") or "").strip()
        doc_name = ch.get("document_keyword") or ch.get("docnm_kwd") or "未知文档"
        chunk_id = ch.get("id", "")

        if not image_id:
            results.append({
                "chunk": ch,
                "image_id": "",
                "saved_path": None,
                "error": "该切片无 image_id",
            })
            continue

        data, ct = fetch_image_by_file_id(image_id)
        if data is None:
            results.append({
                "chunk": ch,
                "image_id": image_id,
                "saved_path": None,
                "error": ct or "未知错误",
            })
            continue

        ext = extension_from_content_type(ct)
        filename = _safe_filename(image_id, ext)
        path = out_dir / filename
        path.write_bytes(data)
        results.append({
            "chunk": ch,
            "image_id": image_id,
            "saved_path": path,
            "error": None,
        })

    return results


def run_fetch_and_show(
    question: str,
    top_k: int = 3,
    dataset_id: str = DEFAULT_DATASET_ID,
    open_html: bool = False,
) -> None:
    """拉取检索结果对应的切片图片，打印路径，并可选生成 HTML 索引页供浏览器查看。"""
    print(f"🔍 检索与「{question}」相似的 Top{top_k} 切片并拉取图片...\n")
    results = fetch_and_save_chunk_images(question, dataset_id=dataset_id, top_k=top_k)

    for i, r in enumerate(results, 1):
        ch = r["chunk"]
        doc_name = ch.get("document_keyword") or ch.get("docnm_kwd") or "未知文档"
        sim = ch.get("similarity") or ch.get("vector_similarity")
        sim_str = f"{sim:.4f}" if sim is not None else "-"
        print(f"【Top {i}】 相似度: {sim_str} | 来源: {doc_name}")
        print(f"   image_id: {r['image_id'] or '-'}")
        if r["saved_path"]:
            print(f"   ✅ 已保存: {r['saved_path']}")
        else:
            print(f"   ❌ {r['error']}")
        print()

    # 生成简易 HTML 索引，方便浏览器一次看所有图
    saved = [r for r in results if r["saved_path"] is not None]
    if saved:
        index_path = IMAGES_DIR / "index.html"
        index_path.write_text(
            _make_index_html(saved),
            encoding="utf-8",
        )
        print(f"📄 索引页已生成: {index_path}")
        print(f"   在浏览器打开该文件即可查看所有已下载的切片图片。")
        if open_html:
            import webbrowser
            webbrowser.open(index_path.as_uri())
    else:
        print("未成功下载任何图片。若 RAGFlow 未暴露按 image_id 的图片接口，需在 RAGFlow 前端抓包确认实际请求 URL 后再适配。")

    return results


def _make_index_html(results: list[dict]) -> str:
    """生成一个简单的 HTML 页面，列出每张图片和对应切片摘要。"""
    rows = []
    for i, r in enumerate(results, 1):
        path = r["saved_path"]
        if not path:
            continue
        ch = r["chunk"]
        doc_name = ch.get("document_keyword") or ch.get("docnm_kwd") or "未知文档"
        content = (ch.get("content") or "")[:200].replace("\n", " ").strip()
        name = path.name
        rows.append(f"""
        <div class="item">
            <h3>Top {i} · {doc_name}</h3>
            <p class="content">{content}…</p>
            <img src="{name}" alt="{name}" />
        </div>""")
    body = "\n".join(rows)
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8" />
    <title>RAGFlow 检索切片图片</title>
    <style>
        body {{ font-family: sans-serif; max-width: 900px; margin: 1rem auto; padding: 0 1rem; }}
        .item {{ margin: 1.5rem 0; padding: 1rem; border: 1px solid #eee; border-radius: 8px; }}
        .item h3 {{ margin-top: 0; }}
        .content {{ color: #555; font-size: 0.95rem; }}
        .item img {{ max-width: 100%; height: auto; display: block; margin-top: 0.5rem; }}
    </style>
</head>
<body>
    <h1>RAGFlow 检索结果 · 切片图片</h1>
    {body}
</body>
</html>"""


if __name__ == "__main__":
    QUESTION = "煤矿企业如何保障从业人员在安全生产与职业病危害防治中的监督权利？"
    run_fetch_and_show(QUESTION, top_k=3)
