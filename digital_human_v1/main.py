# -*- coding: utf-8 -*-
"""
纯语音闲聊：ASR → LLM 流式 → TTS（队列 + 句切分），文字与语音逐句对齐。
"""
import os
import sys
import time

# --------------- 1. 路径 ---------------
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if os.getcwd() != PROJECT_ROOT:
    os.chdir(PROJECT_ROOT)
    sys.path.insert(0, PROJECT_ROOT)

# --------------- 2. 依赖 ---------------
import asr
import tts
import llm

llm_client = llm.llm_client

# --------------- 3. 主流程 ---------------
def main():
    print("=" * 50)
    print("纯语音闲聊：麦克风 → 识别 → 回复语音播报 | 说「退出」或 Ctrl+C 结束")
    print("=" * 50)

    try:
        asr_service = asr.ASRService()
    except Exception as e:
        print("ASR 初始化失败:", e)
        return

    while True:
        try:
            print("\n请说话...（说完停顿约 1 秒）")
            t0 = time.perf_counter()
            user_text = (asr_service.run_once() or "").strip()
            print("[耗时] 语音识别: {:.2f}s".format(time.perf_counter() - t0))
        except KeyboardInterrupt:
            print("\n已退出")
            break

        if not user_text:
            print("[未识别到，请再说一次]")
            continue
        if user_text.strip().lower() in ("quit", "exit", "退出"):
            print("再见～")
            break

        print("你说:", user_text)
        try:
            t0 = time.perf_counter()
            tts.chat_stream_tts(llm_client, user_text)
            print("[耗时] 本轮: {:.2f}s".format(time.perf_counter() - t0))
        except Exception as e:
            print("\nLLM/TTS 出错:", e)
            tts.tts_doubao_stream_play_chunk("抱歉，我这边出错了，稍后再试吧。")

    asr_service.shutdown()


if __name__ == "__main__":
    main()
