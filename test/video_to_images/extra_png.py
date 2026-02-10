import cv2
import os
import queue
import threading
from ultralytics import YOLO
from rembg import remove, new_session
from PIL import Image
import numpy as np

# --- 配置参数 ---
VIDEO_PATH = "data/435cbc07cca2a2c016b1a24814f0ea0e.mp4"
OUTPUT_ROOT = "extracted_people"
NUM_WORKERS = 4  # 根据你的 CPU 核心数调整，建议 4-8
MAX_QUEUE_SIZE = 100 # 限制队列大小，防止内存溢出

# 1. 加载模型
model = YOLO('yolov8n.pt') 
# 创建 rembg 会话（共享会话可以提高效率）
rembg_session = new_session()

# 任务队列
task_queue = queue.Queue(maxsize=MAX_QUEUE_SIZE)

def save_worker():
    """消费者线程：负责抠图和保存"""
    while True:
        task = task_queue.get()
        if task is None: # 结束信号
            break
        
        frame_idx, obj_id, person_crop = task
        
        # 创建文件夹
        person_folder = os.path.join(OUTPUT_ROOT, f"person_{obj_id}")
        if not os.path.exists(person_folder):
            os.makedirs(person_folder, exist_ok=True)

        # 图像处理
        try:
            # 格式转换 BGR -> RGB
            person_rgb = cv2.cvtColor(person_crop, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(person_rgb)
            
            # 抠图 (使用共享 session)
            no_bg_img = remove(pil_img, session=rembg_session)

            # 保存
            save_path = os.path.join(person_folder, f"frame_{frame_idx:05d}.png")
            no_bg_img.save(save_path)
        except Exception as e:
            print(f"处理错误 [ID:{obj_id} Frame:{frame_idx}]: {e}")
        
        task_queue.task_done()
        print(f"已完成任务：ID {obj_id} 第 {frame_idx} 帧 (剩余队列: {task_queue.qsize()})")

def extract_people_multithreaded(video_path):
    cap = cv2.VideoCapture(video_path)
    frame_count = 0
    
    if not os.path.exists(OUTPUT_ROOT):
        os.makedirs(OUTPUT_ROOT)

    # 启动工作线程
    threads = []
    for _ in range(NUM_WORKERS):
        t = threading.Thread(target=save_worker)
        t.start()
        threads.append(t)

    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            break

        # YOLO 跟踪（这一步通常在主线程运行，因为跟踪需要顺序性）
        results = model.track(frame, persist=True, classes=0, verbose=False)

        if results[0].boxes.id is not None:
            boxes = results[0].boxes.xyxy.cpu().numpy().astype(int)
            ids = results[0].boxes.id.cpu().numpy().astype(int)

            for box, obj_id in zip(boxes, ids):
                x1, y1, x2, y2 = box
                x1, y1 = max(0, x1), max(0, y1)
                person_crop = frame[y1:y2, x1:x2].copy() # 必须 copy，防止内存指针混乱

                if person_crop.size > 0:
                    # 将任务放入队列，如果队列满了会阻塞直到有空位
                    task_queue.put((frame_count, obj_id, person_crop))

        frame_count += 1
        if frame_count % 10 == 0:
            print(f"--- 主线程：已读取并检测至第 {frame_count} 帧 ---")

    # 停止信号：放入 None 告知子线程结束
    for _ in range(NUM_WORKERS):
        task_queue.put(None)

    # 等待所有线程完成
    for t in threads:
        t.join()

    cap.release()
    print("所有任务提取并处理完成！")

if __name__ == "__main__":
    # 注意：在 Windows 下，多线程运行可能会受限于 Global Interpreter Lock (GIL)
    # 但 rembg 底层主要是 ONNX (C++)，所以多线程会有明显提升
    extract_people_multithreaded(VIDEO_PATH)