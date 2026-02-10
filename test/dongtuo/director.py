from operator import add
import os
from typing import List, TypedDict, Annotated
from langchain_core.messages import AnyMessage, HumanMessage, AIMessage, SystemMessage
from dotenv import load_dotenv
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.config import get_stream_writer
from langchain_community.chat_models import ChatTongyi
import matplotlib.pyplot as plt
import ast
from matplotlib import rcParams
import matplotlib

matplotlib.use("TkAgg")
# 设置中文字体
rcParams['font.sans-serif'] = ['SimHei']  # 黑体
rcParams['axes.unicode_minus'] = False  # 解决负号显示问题

import pandas as pd

def format_student_info(student_info: dict):
    """
    student_info: MCP 返回的档案字典
    返回 ASCII 表格字符串
    """
    df = pd.DataFrame([student_info])
    table_str = df.to_string(index=False)
    return table_str

def plot_grades(grades_dict, student_name):
    subjects = [k for k in grades_dict.keys() if k not in ("学生编号", "学生姓名")]
    scores = [grades_dict[sub] for sub in subjects]

    plt.figure(figsize=(10, 6))
    plt.bar(subjects, scores, color='skyblue')
    plt.ylim(0, 100)
    plt.title(f"{student_name} 成绩分布")
    plt.xlabel("科目")
    plt.ylabel("分数")
    for i, score in enumerate(scores):
        plt.text(i, score + 1, str(score), ha='center')
    plt.show()


load_dotenv()

llm = ChatTongyi(
    model_name="qwen-turbo",
    api_key=os.getenv("DASHSCOPE_API_KEY"),

)


class State(TypedDict):
    message: Annotated[List[AnyMessage], add]
    type: str


nodes = {"travel_node", "joke_node",  "other_node"}


def other_node(state: State):
    print(">>> other_node")
    Writer = get_stream_writer()
    Writer({"node": ">>> other_node"})
    return {"message": [HumanMessage(content="我无法回答这个问题")], "type": "other"}


def supervisor_node(state: State):
    print(">>> supervisor_node")
    Writer = get_stream_writer()
    Writer({"node": ">>> supervisor_node"})
    user_msg = state["message"][0].content if hasattr(state["message"][0], "content") else str(state["message"][0])
    # 根据用户问题，对问题进行分类，分类结果保存到type当中
    prompt = """你是一个专业的客服助手，负责对用户的问题进行分类，并将任务分给其他AGENT,
    如果用户的问题是和学生档案或者成绩相关的，那就返回travel。
    如果用户的问题是希望讲一个笑话，那就返回joke 。
    如果用户的问题是希望对一个对联，那就返回couplet 。
    如果是其他的问题，返回other。
    除了这几个选项外，不要返回任何其他的内容。

"""

    prompts = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": user_msg}
    ]
    if "type" in state:
        Writer({"supervisor_step": f'已获得{state["type"]}智能体获得结果'})
        return {"type": END}

    else:
        response = llm.invoke(prompts)
        typeRes = response.content.strip()
        Writer({"supervisor_step": f'分类结果是{typeRes}'})
        type_node = f"{typeRes}_node"
        if type_node in nodes:
            return {"type": type_node}
        else:
            return {"type": "other_node"}


import asyncio
from mcp.client.stdio import stdio_client
from mcp import ClientSession, StdioServerParameters

def travel_node(state: dict):
    """
    MCP 学生查询节点
    state["message"][0]：用户输入，可以是学号或姓名
    """
    print(">>> student_node")
    Writer = get_stream_writer()
    Writer({"node": ">>> student_node"})

    user_input = state["message"][0]

    # 判断请求类型
    system_prompt_type = """
    你是一个专业的学生信息助手。
    输入可能是学生姓名或学号。
    如果用户想查询学生档案，返回 'info'。
    如果用户想查询学生成绩，返回 'grades'。
    不要返回其他内容。
    """
    prompts_type = [
        {"role": "system", "content": system_prompt_type},
        {"role": "user", "content": user_input}
    ]
    response_type = llm.invoke(prompts_type)
    request_type = response_type.content.strip() if hasattr(response_type, "content") else "info"
    Writer({"type_detected": request_type})

    # 提取学号或姓名
    system_prompt_extract = f"""
    你是一个专业助手。
    从以下用户输入中提取学生的学号或姓名，只返回学号或姓名字符串，不要其他内容。
    用户输入: "{user_input}"
    """
    prompts_extract = [{"role": "system", "content": system_prompt_extract}]
    response_extract = llm.invoke(prompts_extract)
    query = response_extract.content.strip() if hasattr(response_extract, "content") else user_input
    Writer({"query_extracted": query})

    # MCP Server 配置
    server_params = StdioServerParameters(
        command="python",
        args=["C:/Users/Admin/Desktop/力道demo-20251019/student_mcp/student_serve.py"],
        env=None
    )

    async def query_student(query, request_type):
        from mcp.client.stdio import stdio_client
        from mcp import ClientSession
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()

                tool_name = "get_student_info" if request_type == "info" else "get_student_grades"
                result = await session.call_tool(tool_name, {"query": query})

                if result.content:
                    text_result = result.content[0].text

                    try:
                        data_dict = ast.literal_eval(text_result)

                        if request_type == "grades" and "grades" in data_dict:
                            plot_grades(data_dict["grades"], data_dict["name"])

                        elif request_type == "info":
                            # 输出档案表格
                            df = pd.DataFrame([data_dict])
                            fig, ax = plt.subplots(figsize=(10, 2))
                            ax.axis('tight')
                            ax.axis('off')
                            table = ax.table(cellText=df.values, colLabels=df.columns, loc='center')
                            plt.tight_layout()
                            plt.show()  # 或 plt.savefig("student_info.png")
                    except Exception as e:
                        Writer({"plot_error": str(e)})

                    return text_result
                return "未查询到结果"

    result_text = asyncio.run(query_student(query, request_type))
    Writer({"result": result_text})
    return {"result": result_text}


def joke_node(state: State):
    Writer = get_stream_writer()
    Writer({"node": ">>> joke_node"})
    system_prompt = """你是一个笑话大师，根据用户的问题，写一个不超过100字的笑话。"""
    user_msg = state["message"][0].content if hasattr(state["message"][0], "content") else str(state["message"][0])
    prompts = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_msg}
    ]
    response = llm.invoke(prompts)
    print(">>> joke_node")
    Writer({"joke_result": response.content})
    return {"message": [HumanMessage(content=response.content)], "type": "joke"}




def routing_function(state: State):
    if state["type"] == "travel_node":
        return "travel_node"
    elif state["type"] == "joke_node":
        return "joke_node"
    elif state["type"] == END:
        return END
    else:
        return "other_node"


# 创建状态图


builder = StateGraph(state_schema=State)
# 添加节点
builder.add_node("supervisor_node", supervisor_node)
builder.add_node("travel_node", travel_node)
builder.add_node("joke_node", joke_node)
builder.add_node("other_node", other_node)

# 添加EDGEs
builder.add_edge(START, "supervisor_node")
builder.add_conditional_edges("supervisor_node", routing_function,
                              ["joke_node", "other_node", "travel_node"])
builder.add_edge("joke_node", END)
builder.add_edge("other_node", END)
builder.add_edge("travel_node", END)

# 构建graph
checkpointer = InMemorySaver()
graph = builder.compile(checkpointer=checkpointer)

# 执行任务的测试代码
if __name__ == "__main__":
    if __name__ == "__main__":
        config = {
            "configurable": {
                "thread_id": "1"
            }
        }

        last_chunk = None
        for chunk in graph.stream({"message": ["查询李四的成绩"]}, config, stream_mode="custom"):
            last_chunk = chunk  # 每次覆盖，最终保留最后一个

        if last_chunk is not None:
            print(last_chunk)  # 输出最后一个 chunk 的内容

