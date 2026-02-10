import os
import sys
import http.client
import getpass
import platform
import subprocess
import threading
import time
from datetime import datetime
from typing import Callable
from urllib.request import urlopen
from langchain_community.chat_models import ChatTongyi
from langchain.tools import tool
from langchain.tools.tool_node import ToolCallRequest
from langchain.messages import ToolMessage
from langchain.agents.middleware import AgentMiddleware
from deepagents import create_deep_agent
from langgraph.checkpoint.memory import MemorySaver
from langchain_openai import ChatOpenAI
from langgraph.types import Command

# ==========================================================
# 1. 核心修复 - 解决编码报错
# ==========================================================
_old_putheader = http.client.HTTPConnection.putheader
def _patched_putheader(self, header, *values):
    new_values = [v.encode('utf-8').decode('latin-1') if isinstance(v, str) else v for v in values]
    return _old_putheader(self, header, *new_values)
http.client.HTTPConnection.putheader = _patched_putheader

# ==========================================================
# 2. 系统环境与路径识别
# ==========================================================
current_user = getpass.getuser()
if platform.system() == 'Windows':
    ROOT_PATH, DESKTOP_PATH = "C:/", f"C:/Users/{current_user}/Desktop"
else:
    ROOT_PATH, DESKTOP_PATH = "/", f"/Users/{current_user}/Desktop"

CURRENT_DIR = os.getcwd().replace("\\", "/")

# ==========================================================
# 3. 增强型工具集 (保留原有逻辑)
# ==========================================================
@tool
def terminal(command: str) -> str:
    """执行系统终端指令。"""
    try:
        encoding = 'gbk' if platform.system() == 'Windows' else 'utf-8'
        res = subprocess.run(command, shell=True, capture_output=True, text=True, encoding=encoding, errors='replace')
        return res.stdout if res.stdout else res.stderr if res.stderr else "执行成功"
    except Exception as e:
        return f"执行出错: {str(e)}"

@tool
def open_resource(target: str) -> str:
    """
    智能打开电脑资源。
    target 可以是: 文件夹路径、文件路径、网址(http...)或程序名。
    示例: 打开桌面、打开百度、打开某个.py文件。
    """
    try:
        if platform.system() == 'Windows':
            os.startfile(target)
        else:
            subprocess.run(['open', target] if platform.system() == 'Darwin' else ['xdg-open', target])
        return f"✅ 已为您打开: {target}"
    except Exception as e:
        return f"❌ 无法打开 {target}: {str(e)}"
@tool
def set_smart_alarm(seconds: int, message: str) -> str:
    """
    设置智能提醒。时间一到，电脑会弹出窗口并语音/文字提醒。
    seconds: 倒计时秒数。
    message: 提醒内容。
    """
    def alarm_logic():
        time.sleep(seconds)
        # Windows 专用弹出消息框 (PowerShell 实现)
        if platform.system() == 'Windows':
            ps_script = f'Add-Type -AssemblyName Microsoft.VisualBasic; [Microsoft.VisualBasic.Interaction]::MsgBox("{message}", "OKOnly,SystemModal,Information", "智能助理提醒")'
            subprocess.run(["powershell", "-Command", ps_script])
        else:
            print(f"\n\n🔔 【闹钟提醒】: {message}\n")

    threading.Thread(target=alarm_logic, daemon=True).start()
    return f"🚀 好的，我已经设定了 {seconds} 秒后的提醒：{message}"

@tool
def notepad_manager(action: str, content: str = "") -> str:
    """
    管理您的记事本。
    action: 'add' (记录), 'read' (查看), 'clear' (清空)。
    """
    try:
        if action == "add":
            with open(NOTES_FILE, "a", encoding="utf-8") as f:
                f.write(f"--- {datetime.now().strftime('%m-%d %H:%M')} ---\n{content}\n\n")
            return "📝 笔记已记下。"
        elif action == "read":
            if not os.path.exists(NOTES_FILE): return "记事本空空如也。"
            with open(NOTES_FILE, "r", encoding="utf-8") as f: return f.read()
        return "未知操作。"
    except Exception as e:
        return f"记事本报错: {e}"

@tool
def get_system_time() -> str:
    """获取当前精准时间，用于计算。"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

@tool
def write_file(path: str, content: str) -> str:
    """写入文件。"""
    try:
        path = path.replace("\\", "/")
        abs_path = os.path.abspath(path)
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        with open(abs_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"✅ 文件已保存: {abs_path}"
    except Exception as e:
        return f"❌ 失败: {str(e)}"

@tool
def list_dir(path: str) -> str:
    """列出指定目录下的文件和文件夹列表。支持 Windows 绝对路径。"""
    try:
        if not path or path == "/": path = ROOT_PATH
        target = os.path.abspath(path)
        items = os.listdir(target)
        return "\n".join(items) if items else "目录为空"
    except Exception as e:
        return f"❌ 读取目录失败: {str(e)}"

# ==========================================================
# 4. 安全中间件 - 增加删除/修改确认逻辑
# ==========================================================
class SafetyGuardMiddleware(AgentMiddleware):
    """
    安全中间件：拦截危险的工具调用，要求用户确认。
    使用 wrap_tool_call 在工具执行前进行拦截。
    """
    
    def wrap_tool_call(
        self,
        request: ToolCallRequest,
        handler: Callable[[ToolCallRequest], ToolMessage | Command],
    ) -> ToolMessage | Command:
        """
        在工具调用前进行安全检查
        """
        tool_name = request.tool_call["name"]
        tool_args = request.tool_call["args"]
        
        is_risk = False
        risk_desc = ""

        # 场景 A: 拦截终端删除操作
        if tool_name == "terminal":
            cmd = tool_args.get("command", "").lower()
            danger_keywords = ["rm ", "del ", "rd ", "rmdir ", "format "]
            if any(k in cmd for k in danger_keywords):
                is_risk = True
                risk_desc = f"危险操作：尝试执行删除指令 -> {cmd}"

        # 场景 B: 拦截覆盖/修改已有文件
        elif tool_name == "write_file":
            file_path = tool_args.get("path", "")
            if os.path.exists(file_path):
                is_risk = True
                risk_desc = f"危险操作：尝试覆盖/修改已有文件 -> {file_path}"

        # 如果检测到风险，进行拦截并询问
        if is_risk:
            print(f"\n" + "!"*15 + " 安全确认 (中间件拦截) " + "!"*15)
            print(f"AI 计划执行：{risk_desc}")
            confirm = input("❗ 您确定允许 AI 执行这个操作吗？(y/n): ").strip().lower()
            print("!"*46)
            
            if confirm not in ['y', 'yes']:
                # 用户拒绝，返回错误消息
                return ToolMessage(
                    content=f"❌ 用户已拒绝执行：{risk_desc}",
                    tool_call_id=request.tool_call["id"]
                )

        # 如果没有风险或用户同意，继续执行工具
        return handler(request)

# ==========================================================
# 5. 初始化 Agent 引擎
# ==========================================================
# 配置本地/在线模型
OPENAI_CONFIG = {
    "base_url": "http://10.3.0.16:8100/v1",
    "api_key": "222442bb160d5081b9e38506901d6889",
    "model": "qwen3-14b",
    "timeout": 60.0
}

llm = ChatOpenAI(
    model=OPENAI_CONFIG["model"],
    openai_api_key=OPENAI_CONFIG["api_key"],
    openai_api_base=OPENAI_CONFIG["base_url"],
    timeout=OPENAI_CONFIG["timeout"]
)

# 原始提示词功能全部保留
SYSTEM_PROMPT = f"""你是一个高级系统助理。
1. 环境信息：
   - 当前脚本运行目录（CWD）: {CURRENT_DIR}
   - 用户桌面路径: {DESKTOP_PATH}
   - 系统: {platform.system()}，用户: {current_user}

2. 路径规则：
   - **重要**：你的当前工作目录是 `{CURRENT_DIR}`，**不是桌面**。
   - 如果用户要求在“桌面”操作，你必须在路径前加上 `{DESKTOP_PATH}/`。
   - 想要看目录下的文件，请优先使用 `list_dir` 工具。
   - 想要写代码或创建 .py 文件，必须优先使用 `write_file` 工具。
   - 创建文件夹、运行 Python 或执行系统命令时，使用 `terminal`。
3.【核心权限】：你拥有 `set_smart_alarm`（弹窗闹钟）和 `open_resource`（打开文件/网页）等物理权限。
4.【禁止话术】：严禁对用户说“我无法操作系统”、“我没有权限”或“请您手动操作”。
5.如果用户要求打开某个资源，直接调用 `open_resource`，不要解释。
"""

agent = create_deep_agent(
    model=llm,
    tools=[terminal, write_file, list_dir],
    skills=["/skills/"],
    checkpointer=MemorySaver(),
    system_prompt=SYSTEM_PROMPT,
    middleware=[SafetyGuardMiddleware()] # 注入安全中间件
)

# ==========================================================
# 6. 对话循环
# ==========================================================
def chat():
    session_id = "safe_agent_session_001"
    print(f"\n--- 系统助手已启动 (交互确认模式已开启) ---")
    
    while True:
        try:
            query = input(f"\n用户 >> ").strip()
            if not query: continue
            if query.lower() in ['exit', 'quit']: break
            if query.lower() == 'reset':
                session_id += "_new"; print("--- 会话已重置 ---"); continue
            
            print("\n" + "·"*20 + " AI 思考与执行链 " + "·"*20)
            inputs = {"messages": [{"role": "user", "content": query}]}
            config = {"configurable": {"thread_id": session_id}}
            
            final_response = ""
            for chunk in agent.stream(inputs, config, stream_mode="values"):
                if "messages" in chunk:
                    last_msg = chunk["messages"][-1]
                    if last_msg.type == "ai":
                        if last_msg.content: print(f"【思考】: {last_msg.content}")
                        final_response = last_msg.content
                    elif last_msg.type == "tool":
                        print(f"【反馈】: {last_msg.content.strip()}")

            print("·"*54)
            print(f"\n助手总结 >> {final_response}")

        except PermissionError as pe:
            print(f"\n🛡️ 安全拦截: {str(pe)}")
        except Exception as e:
            print(f"\n❌ 系统报错: {e}")

if __name__ == "__main__":
    chat()