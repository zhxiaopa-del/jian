"""
手动下载 rembg 模型文件
"""
import os
import requests
from pathlib import Path

# 模型文件信息
MODEL_URL = "https://github.com/danielgatis/rembg/releases/download/v0.0.0/u2net.onnx"
MODEL_DIR = Path.home() / ".u2net"
MODEL_PATH = MODEL_DIR / "u2net.onnx"

def download_with_progress(url, filepath, proxies=None, timeout=600, max_retries=3):
    """带进度条下载文件，支持重试"""
    print(f"开始下载: {url}")
    print(f"保存到: {filepath}")
    
    # 创建目录
    filepath.parent.mkdir(parents=True, exist_ok=True)
    
    # 设置请求头
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    for attempt in range(max_retries):
        try:
            print(f"\n尝试 {attempt + 1}/{max_retries}...")
            response = requests.get(url, stream=True, headers=headers, proxies=proxies, timeout=timeout)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            percent = (downloaded / total_size) * 100
                            mb_downloaded = downloaded / (1024 * 1024)
                            mb_total = total_size / (1024 * 1024)
                            print(f"\r进度: {percent:.1f}% ({mb_downloaded:.1f}/{mb_total:.1f} MB)", end='', flush=True)
            
            print(f"\n✅ 下载完成: {filepath}")
            print(f"文件大小: {filepath.stat().st_size / (1024*1024):.2f} MB")
            return True
            
        except requests.exceptions.Timeout:
            print(f"\n⚠️ 下载超时 (尝试 {attempt + 1}/{max_retries})")
            if attempt < max_retries - 1:
                print("正在重试...")
                if filepath.exists():
                    filepath.unlink()  # 删除不完整的文件
            else:
                print(f"\n❌ 下载超时，请检查网络连接或使用代理")
                return False
        except requests.exceptions.RequestException as e:
            print(f"\n⚠️ 下载失败: {e} (尝试 {attempt + 1}/{max_retries})")
            if attempt < max_retries - 1:
                print("正在重试...")
                if filepath.exists():
                    filepath.unlink()
            else:
                print(f"\n❌ 下载失败: {e}")
                return False
    
    return False

if __name__ == "__main__":
    # 检查是否已存在
    if MODEL_PATH.exists():
        print(f"模型文件已存在: {MODEL_PATH}")
        print(f"文件大小: {MODEL_PATH.stat().st_size / (1024*1024):.2f} MB")
        response = input("是否重新下载? (y/n): ").strip().lower()
        if response != 'y':
            print("跳过下载")
            exit(0)
        MODEL_PATH.unlink()
    
    # 设置代理（如果需要）
    proxies = None
    http_proxy = os.environ.get('HTTP_PROXY') or os.environ.get('http_proxy')
    https_proxy = os.environ.get('HTTPS_PROXY') or os.environ.get('https_proxy')
    
    if http_proxy or https_proxy:
        proxies = {
            'http': http_proxy,
            'https': https_proxy or http_proxy
        }
        print(f"使用代理: {proxies}")
    
    # 下载（增加超时时间和重试次数）
    success = download_with_progress(MODEL_URL, MODEL_PATH, proxies=proxies, timeout=600, max_retries=3)
    
    if success:
        print(f"\n✅ 模型文件已保存到: {MODEL_PATH}")
        print("现在可以运行 extra_png.py 了")
    else:
        print("\n❌ 下载失败，请尝试：")
        print("1. 检查网络连接")
        print("2. 设置代理: $env:HTTP_PROXY='http://127.0.0.1:7897'")
        print("3. 手动下载: https://github.com/danielgatis/rembg/releases/download/v0.0.0/u2net.onnx")
        print(f"   保存到: {MODEL_PATH}")
