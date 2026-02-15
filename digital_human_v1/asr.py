import base64
import os
import wave
import uuid
import time
import logging
import queue
import threading
from typing import Optional, List

import requests as rq
import pyaudio
import numpy as np
from dotenv import load_dotenv

# --- 日志配置 ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - [%(name)s] %(message)s')
logger = logging.getLogger("ASRService")

class AudioConfig:
    """音频流及 API 配置类"""
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 16000
    CHUNK = 1024
    
    # 从环境变量加载配置（与脚本同目录的 variables.env，不依赖当前工作目录）
    def __init__(self):
        _env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "variables.env")
        if os.path.exists(_env_path):
            load_dotenv(_env_path)
        self.app_id = os.getenv("AUC_APP_ID", "").strip()
        self.access_token = os.getenv("AUC_ACCESS_TOKEN", "").strip()
        self.resource_id = os.getenv("DOUBAO_ASR_FLASH_RESOURCE_ID", "volc.bigasr.auc_turbo")
        self.mic_index = int(os.getenv("MIC_NUM", "0"))
        
        # VAD (静音检测) 参数：静音超过该秒数即判定一句结束
        sensitivity = os.getenv("ASR_SENSITIVITY", "高").strip()
        duration_map = {"高": 1.0, "中": 2.0, "低": 3.0}
        self.silence_timeout = duration_map.get(sensitivity, 1.0)
        self.dbfs_threshold = -45.0  # 默认阈值

class CloudASRClient:
    """负责与云端 API 交互"""
    URL = "https://openspeech.bytedance.com/api/v3/auc/bigmodel/recognize/flash"

    def __init__(self, config: AudioConfig):
        self.cfg = config

    def recognize(self, file_path: str) -> str:
        """极速版 ASR 识别接口"""
        if not self.cfg.app_id or not self.cfg.access_token:
            logger.error("API 凭证缺失")
            return ""

        try:
            with open(file_path, "rb") as f:
                audio_b64 = base64.b64encode(f.read()).decode("utf-8")
        except Exception as e:
            logger.error(f"读取音频文件失败: {e}")
            return ""

        headers = {
            "Content-Type": "application/json",
            "X-Api-App-Key": self.cfg.app_id,
            "X-Api-Access-Key": self.cfg.access_token,
            "X-Api-Resource-Id": self.cfg.resource_id,
            "X-Api-Request-Id": str(uuid.uuid4()),
        }
        
        body = {
            "user": {"uid": self.cfg.app_id},
            "audio": {"data": audio_b64},
            "request": {"model_name": "bigmodel", "enable_itn": True},
        }

        try:
            response = rq.post(self.URL, headers=headers, json=body, timeout=30)
            status_code = response.headers.get("X-Api-Status-Code")
            
            if status_code == "20000000":
                result = response.json()
                return result.get("result", {}).get("text", "").strip()
            else:
                logger.warning(f"ASR API 响应异常: {status_code} - {response.text}")
                return ""
        except Exception as e:
            logger.error(f"网络请求异常: {e}")
            return ""

class Recorder:
    """异步音频采集器：使用回调模式防止溢出"""
    def __init__(self, config: AudioConfig):
        self.cfg = config
        self.pa = pyaudio.PyAudio()
        self.stream: Optional[pyaudio.Stream] = None
        self._queue = queue.Queue()
        self.is_running = False

    def _callback(self, in_data, frame_count, time_info, status):
        """PyAudio 回调函数：将数据推入队列，不阻塞音频流"""
        if status:
            logger.debug(f"音频流状态异常: {status}")
        self._queue.put(in_data)
        return (None, pyaudio.paContinue)

    def start(self):
        """开启音频流"""
        if self.stream and self.stream.is_active():
            return
            
        self.stream = self.pa.open(
            format=self.cfg.FORMAT,
            channels=self.cfg.CHANNELS,
            rate=self.cfg.RATE,
            input=True,
            input_device_index=self.cfg.mic_index,
            frames_per_buffer=self.cfg.CHUNK,
            stream_callback=self._callback
        )
        self.is_running = True
        logger.info("音频流已开启")

    def stop(self):
        """关闭资源"""
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        self.pa.terminate()
        logger.info("音频流已释放")

    @staticmethod
    def calculate_dbfs(raw_data: bytes) -> float:
        """计算分贝值"""
        samples = np.frombuffer(raw_data, dtype=np.int16)
        if len(samples) == 0: return -90.0
        rms = np.sqrt(np.mean(samples.astype(np.float32)**2))
        if rms < 1.0: return -90.0
        return 20 * np.log10(rms / 32768.0)

    def collect_phrase(self) -> bytes:
        """
        基于 VAD 逻辑采集一段语音。
        核心逻辑：持续从队列获取数据，直到检测到持续静音。
        """
        frames = []
        silence_frames_threshold = int(self.cfg.silence_timeout * self.cfg.RATE / self.cfg.CHUNK)
        silence_counter = 0
        has_spoken = False

        # 清空队列中的陈旧数据
        while not self._queue.empty():
            self._queue.get()

        logger.info("正在监听说话...")
        while self.is_running:
            try:
                # 阻塞获取队列数据（超时时间设为 1s 防止死循环）
                data = self._queue.get(timeout=1.0)
                frames.append(data)
                
                dbfs = self.calculate_dbfs(data)
                
                if dbfs > self.cfg.dbfs_threshold:
                    if not has_spoken:
                        logger.debug("检测到语音输入...")
                        has_spoken = True
                    silence_counter = 0
                else:
                    if has_spoken:
                        silence_counter += 1
                
                # 如果说话后静音超过时长，则判定结束
                if has_spoken and silence_counter > silence_frames_threshold:
                    logger.info("检测到结束静音，停止采集")
                    break
                    
            except queue.Empty:
                continue

        return b"".join(frames)

class ASRService:
    """ASR 服务门面类：协调采集与识别"""
    def __init__(self):
        self.cfg = AudioConfig()
        self.recorder = Recorder(self.cfg)
        self.client = CloudASRClient(self.cfg)
        self.cache_path = "data/cache/record_temp.wav"
        os.makedirs(os.path.dirname(self.cache_path), exist_ok=True)

    def _save_wav(self, data: bytes):
        """将原始字节保存为符合标准格式的 WAV"""
        with wave.open(self.cache_path, 'wb') as wf:
            wf.setnchannels(self.cfg.CHANNELS)
            wf.setsampwidth(self.recorder.pa.get_sample_size(self.cfg.FORMAT))
            wf.setframerate(self.cfg.RATE)
            wf.writeframes(data)

    def run_once(self) -> str:
        """执行一次完整的‘录音-识别’流程"""
        try:
            self.recorder.start()
            audio_data = self.recorder.collect_phrase()
            
            # 基础过滤：小于 0.5 秒的音频忽略
            if len(audio_data) < self.cfg.RATE * 0.5 * 2:
                return ""

            self._save_wav(audio_data)
            logger.info("正在调用云端 API...")
            text = self.client.recognize(self.cache_path)
            return text
        except Exception as e:
            logger.error(f"运行流程出错: {e}")
            return ""
        finally:
            # 如果是单次任务可在此 stop，若是持续任务建议保持 start 状态
            pass

    def shutdown(self):
        self.recorder.stop()

# --- 使用示例：run_once() 的返回值即为识别结果，可直接 return 使用 ---
if __name__ == "__main__":
    service = ASRService()
    try:
        while True:
            result = service.run_once()  # 识别结果通过 return 返回
            if result:
                print(f"\n>>> 识别结果: {result}\n")
    except KeyboardInterrupt:
        logger.info("服务手动停止")
    finally:
        service.shutdown()