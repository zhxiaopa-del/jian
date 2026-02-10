import fitz  # PyMuPDF
from pathlib import Path
import easyocr
import numpy as np
from PIL import Image
import io

# 配置路径
DATA_DIR = Path(__file__).resolve().parent / "data"
IMAGES_DIR = DATA_DIR / "images"
PDF_OUTPUT_DIR = DATA_DIR / "pdf_output"
IMAGE_BASE_URL = "" 

# URL 行高（现在只需要一行字的高度）
LINE_HEIGHT = 20 

# 初始化 OCR (首次运行会下载模型，支持中英文)
reader = easyocr.Reader(['ch_sim', 'en'])

def _image_url(filename: str) -> str:
    if IMAGE_BASE_URL:
        return f"{IMAGE_BASE_URL.rstrip('/')}/images/{filename}"
    return f"./images/{filename}"

def get_ocr_text(pix):
    """从 Pixmap 中识别文字"""
    try:
        # 将 Pixmap 转为字节流再转为 PIL Image
        img_data = pix.tobytes("png")
        img = Image.open(io.BytesIO(img_data))
        img_np = np.array(img)
        
        # 识别文字
        results = reader.readtext(img_np, detail=0)
        # 合并结果并清理掉多余符号
        full_text = "".join(results).replace("\n", "").replace(" ", "")
        return full_text if full_text else "图片内容"
    except Exception as e:
        print(f"OCR 识别失败: {e}")
        return "图片"

def process_pdf_remove_images_keep_ocr_url(pdf_path: Path):
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    PDF_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    src_doc = fitz.open(pdf_path)
    new_doc = fitz.open()
    stem = pdf_path.stem
    saved_images = {} # {xref: (filename, ocr_text)}

    print(f"正在处理: {pdf_path.name}")

    for page_num in range(len(src_doc)):
        src_page = src_doc[page_num]
        img_instances = src_page.get_image_info(xrefs=True)
        img_instances.sort(key=lambda x: x['bbox'][3])

        # 动态计算新页面高度：原高度 - 所有图片高度 + (图片数量 * 行高)
        total_img_height = sum([(inst['bbox'][3] - inst['bbox'][1]) for inst in img_instances])
        new_height = src_page.rect.height - total_img_height + (len(img_instances) * LINE_HEIGHT)
        
        new_page = new_doc.new_page(width=src_page.rect.width, height=max(new_height, 100))

        current_src_y = 0     
        current_dest_y = 0    

        for idx, inst in enumerate(img_instances):
            xref = inst['xref']
            bbox = fitz.Rect(inst['bbox'])
            
            # 1. 提取并识别图片 (xref 相同则不重复 OCR)
            if xref not in saved_images:
                try:
                    pix = fitz.Pixmap(src_doc, xref)
                    if pix.n - pix.alpha > 3: pix = fitz.Pixmap(fitz.csRGB, pix)
                    
                    # OCR 识别
                    description = get_ocr_text(pix)
                    
                    img_name = f"{stem.replace(' ', '')}_p{page_num}_{idx}.png"
                    pix.save(str(IMAGES_DIR / img_name))
                    saved_images[xref] = (img_name, description)
                    pix = None
                except:
                    saved_images[xref] = ("error.png", "识别失败")

            img_filename, ocr_desc = saved_images[xref]

            # 2. 拷贝图片“上方”的文字（不包括图片本身）
            # 切片范围：从上一个 src_y 到当前图片的最顶端 bbox.y0
            section_height = bbox.y0 - current_src_y
            if section_height > 0:
                clip_rect = fitz.Rect(0, current_src_y, src_page.rect.width, bbox.y0)
                dest_rect = fitz.Rect(0, current_dest_y, src_page.rect.width, current_dest_y + section_height)
                new_page.show_pdf_page(dest_rect, src_doc, page_num, clip=clip_rect)
                current_dest_y += section_height

            # 3. 插入一行 OCR 描述 URL (图片被“删除”，只留这一行)
            url_text = f"![{ocr_desc}]({_image_url(img_filename)})".replace(" ", "")
            text_box = fitz.Rect(0, current_dest_y, src_page.rect.width, current_dest_y + LINE_HEIGHT)
            
            new_page.insert_textbox(
                text_box,
                url_text,
                fontsize=8,
                fontname="china-ss", # 瘦瘦的宋体
                color=(0.3, 0.3, 0.3), # 深灰色
                align=fitz.TEXT_ALIGN_CENTER
            )
            
            current_dest_y += LINE_HEIGHT
            # 源坐标跳过整个图片的高度
            current_src_y = bbox.y1 

        # 4. 拷贝剩余部分
        remaining_height = src_page.rect.height - current_src_y
        if remaining_height > 0:
            clip_rect = fitz.Rect(0, current_src_y, src_page.rect.width, src_page.rect.height)
            dest_rect = fitz.Rect(0, current_dest_y, src_page.rect.width, current_dest_y + remaining_height)
            new_page.show_pdf_page(dest_rect, src_doc, page_num, clip=clip_rect)

    out_path = PDF_OUTPUT_DIR / f"{stem}_ocr_final.pdf"
    new_doc.save(str(out_path), deflate=True)
    new_doc.close()
    src_doc.close()
    print(f"处理完成！图片已删除，文字已提取并上移填充。文件：{out_path}")

if __name__ == "__main__":
    pdf_files = list(DATA_DIR.glob("*.pdf"))
    for pdf in pdf_files:
        if "ocr_final" in pdf.name: continue
        try:
            process_pdf_remove_images_keep_ocr_url(pdf)
        except Exception as e:
            print(f"发生错误: {e}")