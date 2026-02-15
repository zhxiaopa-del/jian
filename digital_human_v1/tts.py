# -*- coding: utf-8 -*-
"""
豆包 TTS：流式合成，支持保存 mp3 或直接流式播放。
可直接与 LLM 流式输出结合，实现边生成边播放。
"""
import base64
import json
import os
import re
import uuid
import queue
import threading
import requests as rq
from dotenv import load_dotenv
from function import current_time

# ----------------- 配置 -----------------
class TtsConfig:
    URL = "https://openspeech.bytedance.com/api/v3/tts/unidirectional"
    SAMPLE_RATE = 24000

    def __init__(self):
        _env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "variables.env")
        if load_dotenv and os.path.exists(_env_path):
            load_dotenv(_env_path)
        self.app_id = os.getenv("AUC_APP_ID", "").strip()
        self.access_token = os.getenv("AUC_ACCESS_TOKEN", "").strip()
        self.resource_id = os.getenv("TTS_RESOURCE_ID", "seed-tts-1.0").strip()
        self.speaker = os.getenv("TTS_SPEAKER", "zh_female_shuangkuaisisi_moon_bigtts").strip()
        self.voice_path = os.path.join(os.path.dirname(__file__), "data", "cache", "tts_output.mp3")
        # 语速：1.0 正常，1.5 约 1.5 倍速；可在 variables.env 中设置 TTS_SPEED
        try:
            self.speed = float(os.getenv("TTS_SPEED", "1.5").strip())
        except ValueError:
            self.speed = 1.5

_cfg = TtsConfig()
voice_path = _cfg.voice_path

# ----------------- 内部函数 -----------------
def _headers_payload(text, fmt="mp3"):
    if not _cfg.app_id or not _cfg.access_token:
        return None, None
    headers = {
        "Content-Type": "application/json",
        "X-Api-App-Id": _cfg.app_id,
        "X-Api-Access-Key": _cfg.access_token,
        "X-Api-Resource-Id": _cfg.resource_id,
        "X-Api-Request-Id": str(uuid.uuid4()),
    }
    payload = {
        "user": {"uid": "tts_001"},
        "req_params": {
            "text": text,
            "model": "seed-tts-1.1",
            "speaker": _cfg.speaker,
            "audio_params": {
                "format": fmt,
                "sample_rate": _cfg.SAMPLE_RATE,
                "speed": _cfg.speed,
            },
        },
    }
    return headers, payload

def _stream_chunks(resp):
    """解析流式响应，逐条 yield (code, data_bytes)。"""
    for line in resp.iter_lines(decode_unicode=True):
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        code = obj.get("code", -1)
        if code == 20000000 and obj.get("data") is None:
            return
        b64 = obj.get("data")
        if b64:
            yield code, base64.b64decode(b64)

# ----------------- TTS 函数 -----------------
def tts_doubao_stream_play_chunk(text_chunk):
    """
    边接收文本 chunk 边播放。分块逻辑在此与上游队列缓冲统一处理，
    LLM 仅传原始流，不在此做按句切分。
    """
    import pyaudio
    headers, payload = _headers_payload(text_chunk, "pcm")
    if not headers:
        print("未配置 AUC_APP_ID / AUC_ACCESS_TOKEN")
        return False
    try:
        pa = pyaudio.PyAudio()
        out = pa.open(format=pyaudio.paInt16, channels=1, rate=_cfg.SAMPLE_RATE, output=True, frames_per_buffer=1024)
        r = rq.post(_cfg.URL, json=payload, headers=headers, stream=True, timeout=60)
        if r.status_code != 200:
            print(f"TTS 错误: {r.status_code} {r.text[:200]}")
            out.close()
            pa.terminate()
            return False
        for _, chunk in _stream_chunks(r):
            out.write(chunk)
        out.stop_stream()
        out.close()
        pa.terminate()
        return True
    except Exception as e:
        print(f"流式播放异常: {e}")
        try:
            pa.terminate()
        except Exception:
            pass
        return False

def get_tts_play(text_chunk):
    """后台线程播放文本 chunk"""
    from threading import Thread
    Thread(target=lambda: tts_doubao_stream_play_chunk(text_chunk), daemon=True).start()

def tts_to_file(text, filepath, fmt="mp3"):
    """将整段文本合成并保存为文件，供后端返回 audioUrl。"""
    if not text or not (text := text.strip()):
        return False
    headers, payload = _headers_payload(text, fmt)
    if not headers:
        return False
    try:
        r = rq.post(_cfg.URL, json=payload, headers=headers, stream=True, timeout=60)
        if r.status_code != 200:
            return False
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "wb") as f:
            for _, chunk in _stream_chunks(r):
                f.write(chunk)
        return True
    except Exception as e:
        print(f"TTS 保存失败: {e}")
        return False

def _is_timing_line(block):
    """是否为 LLM 的耗时/统计行（只打印不送 TTS）"""
    s = (block or "").strip()
    return "块耗时:" in s or "首字:" in s or "流结束:" in s

def _split_sentences(buffer):
    """按句切分，返回 (剩余 buffer, 已完整句列表)。切分符：。！？；，、,!?;~ 换行"""
    out = []
    pattern = re.compile(r"([。！？；\n!?;~])")
    while buffer:
        m = pattern.search(buffer)
        if not m:
            return buffer, out
        end = m.end()
        sent = buffer[:end].strip()
        buffer = buffer[end:].lstrip()
        if sent:
            out.append(sent)
    return "", out

# ----------------- LLM 流式 → TTS 播放 -----------------
# def chat_stream_tts(llm_instance, user_text):
#     """
#     从 LLM 流式输出，收到一块就播一块。
#     与 llm 一致：使用 chat_stream；耗时行（[块耗时:]、[首字:]、[流结束:]）只打印不送 TTS。
#     """
#     chunk_no = 0
#     tts_count = 0
#     print(f"[{current_time()}] 用户输入:", user_text)
#     print(f"[{current_time()}] 助手回复（流式播放）:")
#     for chunk in llm_instance.chat_stream(user_text):
#         chunk_no += 1
#         if not (chunk or chunk.strip()):
#             continue
#         print(chunk, end="", flush=True)
#         if _is_timing_line(chunk):
#             continue
#         tts_doubao_stream_play_chunk(chunk)
#         tts_count += 1
#     print(f"\n[{current_time()}] 总块数 {chunk_no}（TTS 播放 {tts_count} 块）")
# ----------------- LLM 流式 → TTS 播放（队列 + 缓冲，更连贯） -----------------
def chat_stream_tts(llm_instance, user_text):
    """
    从 LLM 流式输出，经队列 + buffer 再送 TTS，避免一字一蹦、显得更自然。
    主线程往队列塞块，播放线程取块并做小段合并后再播；耗时行只打印不送 TTS。
    """
    q = queue.Queue()
    tts_count = [0]

    def _player():
        buffer = ""
        while True:
            try:
                chunk = q.get()
                if chunk is None:
                    if buffer.strip():
                        tts_doubao_stream_play_chunk(buffer)
                        tts_count[0] += 1
                    break
                buffer += chunk
                rest, sentences = _split_sentences(buffer)
                buffer = rest
                for s in sentences:
                    if s.strip():
                        tts_doubao_stream_play_chunk(s)
                        tts_count[0] += 1
            except Exception as e:
                print(f"[TTS 播放线程] {e}")
        if buffer.strip():
            tts_doubao_stream_play_chunk(buffer)
            tts_count[0] += 1

    player_thread = threading.Thread(target=_player, daemon=True)
    player_thread.start()

    chunk_no = 0
    print(f"[{current_time()}] 用户输入:", user_text)
    print(f"[{current_time()}] 助手回复（流式播放）:")
    try:
        for chunk in llm_instance.chat_stream(user_text):
            chunk_no += 1
            if not (chunk or chunk.strip()):
                continue
            print(chunk, end="", flush=True)
            if _is_timing_line(chunk):
                continue
            q.put(chunk)
    except Exception as e:
        print(f"\n[LLM 流式异常] {e}")
    finally:
        q.put(None)
        player_thread.join()
        print(f"\n[{current_time()}] 总块数 {chunk_no}（TTS 播放 {tts_count[0]} 段）")

# ----------------- 测试 -----------------
if __name__ == "__main__":
    from llm import llm_client
    user_input = "你好，做一个自我介绍"
    chat_stream_tts(llm_client, user_input)
