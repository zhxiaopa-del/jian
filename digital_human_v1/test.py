# -*- coding: utf-8 -*-
# Qwen3-ASR-0.6B 测试：
# 方式1）HTTP 调已部署服务（推荐）：需在 Linux 或 WSL2 下启动（vLLM 不支持原生 Windows）
#   vLLM:     vllm serve Qwen/Qwen3-ASR-0.6B --host 0.0.0.0 --port 8000
#   qwen-asr: qwen-asr-serve Qwen/Qwen3-ASR-0.6B --host 0.0.0.0 --port 8000
# 方式2）本机加载模型（需 qwen-asr + pip install wrapt，适合 Windows 无服务时）
import warnings
warnings.filterwarnings("ignore", category=UserWarning)

import os

# 可选：用 HTTP 调已部署的 Qwen ASR 服务，不加载 qwen_asr，避免 wrapt/tensorflow 依赖
def test_via_http(audio_path: str, base_url: str = None) -> str:
    """调用已部署的 qwen-asr-serve / vLLM ASR 服务，返回识别文本。"""
    import requests as rq
    base_url = (base_url or os.getenv("QWEN_ASR_BASE_URL") or "http://127.0.0.1:8000/v1").strip().rstrip("/")
    model = os.getenv("QWEN_ASR_MODEL", "Qwen/Qwen3-ASR-0.6B")
    url = f"{base_url}/audio/transcriptions"
    try:
        with open(audio_path, "rb") as f:
            r = rq.post(url, files={"file": (os.path.basename(audio_path), f, "audio/wav")}, data={"model": model}, timeout=60)
        if r.status_code != 200:
            url2 = f"{base_url}/chat/completions"
            import base64
            with open(audio_path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode("utf-8")
            r = rq.post(url2, json={
                "model": model,
                "messages": [{"role": "user", "content": [{"type": "audio_url", "audio_url": {"url": f"data:audio/wav;base64,{b64}"}}]}]}, timeout=60)
            if r.status_code != 200:
                return ""
            content = r.json().get("choices", [{}])[0].get("message", {}).get("content", "")
            if "Text:" in content:
                content = content.split("Text:", 1)[-1].strip()
            return content
        return r.json().get("text", "")
    except Exception:
        return ""

if __name__ == "__main__":
    audio_file = r"E:\吉安\数字人\data\cache\cache_record.wav"
    model_path = r"D:\model\Qwen3-ASR-0.6B"

    # 先尝试 HTTP：若本机 8000 已部署 qwen-asr-serve，可直接出结果且无需 wrapt
    text = test_via_http(audio_file)
    if text:
        print("识别结果(HTTP):\n", text)
        exit(0)

    # 再尝试本地加载 qwen-asr（可能触发缺少 wrapt）
    try:
        import torch
        from qwen_asr import Qwen3ASRModel
    except ImportError as e:
        print("qwen-asr 导入失败（常见原因：缺少 wrapt，或 protobuf 版本不兼容）")
        print("错误:", e)
        print("\n请在本机终端执行：")
        print("  pip install wrapt")
        print('  若仍有 AttributeError: GetPrototype，再执行： pip install "protobuf<5"')
        print("\n或先启动 ASR 服务再测 HTTP（须在 Linux/WSL2 下执行，vLLM 不支持原生 Windows）：")
        print("  vLLM:       vllm serve Qwen/Qwen3-ASR-0.6B --host 0.0.0.0 --port 8000")
        print("  qwen-asr:   qwen-asr-serve Qwen/Qwen3-ASR-0.6B --host 0.0.0.0 --port 8000")
        print("  或在 Windows 本机装 wrapt 后直接运行本脚本（走本地模型）")
        exit(1)

    try:
        model = Qwen3ASRModel.from_pretrained(
            model_path,
            dtype=torch.float32,
            device_map="cpu",
            max_inference_batch_size=1,
            max_new_tokens=256,
        )
        results = model.transcribe(audio=audio_file, language=None)
        text = results[0].text if results else "未识别到文本"
        print("识别结果(本地):\n", text)
    except Exception as e:
        print("失败:", e)
