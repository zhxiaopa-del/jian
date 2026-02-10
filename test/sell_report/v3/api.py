from fastapi import FastAPI, Body
from typing import Union
from fastapi.middleware.cors import CORSMiddleware
from extra_query_by_agent import DataExtractor
from datetime import datetime
import uvicorn
from intend_by_agent import IntentRecognizer
from json_to_database import SimpleDBManager
from generate_report import generate_report_main

app = FastAPI()

db_config = {
        "host": "localhost", "user": "root", "password": "qwer1234", "database": "sell_report"
    }

#前端启动的方法是，打开hbuilder，那个绿色的
#然后找到test2那个项目下面唯一一个index.html文件，
#打开它以后，在里面随便找个地方狠狠的单击一下，然后看最上面。运行-运行到浏览器-chrome

#流程，前端对话请求，然后说问题，调用chat_extraction，然后把数据给前端，
#四个数据补全后，携带所有数据返回后端再进行保存。调用第二个接口submit_data。

#这个代码是控制跨域的，可以理解成，我允许哪个网站访问我的接口,注意前端启动的端口是不是8848。应该不会变这里。
#如果不是8848 改一下下面的端口号就行。
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许的前端源地址
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有HTTP方法
    allow_headers=["*"],  # 允许所有请求头
)

@app.get("/intent")
def intent_classifier(context: str):
    try:
        intent_recognizer = IntentRecognizer()
        result = intent_recognizer.recognize_intent(context)

        return {
            "code": 200,
            "message": "成功识别意图",
            "timestamp": datetime.now().isoformat(),
            "data": result
        }
    except Exception as e:
        return {
            "code": 500,
            "message": f"识别意图时出错: {str(e)}",
            "timestamp": datetime.now().isoformat(),
            "data": None
        }

#前端发送给后端用户的初始描述。
@app.get("/chat_extraction")
def read_root(context: str):
    try:
        extractor = DataExtractor()
        print(context)
        result = extractor.extract_with_dialog(context)
        
        if result:
            return {
                "code": 200,
                "message": f"成功提取 {len(result)} 条记录",
                "timestamp": datetime.now().isoformat(),
                "data": result
            }
        else:
            return {
                "code": 400,
                "message": "未能提取到有效数据",
                "timestamp": datetime.now().isoformat(),
                "data": None
            }
    except Exception as e:
        return {
            "code": 500,
            "message": f"提取数据时出错: {str(e)}",
            "timestamp": datetime.now().isoformat(),
            "data": None
        }



@app.post("/add_data")
async def add_data(data: dict = Body(...)):
    try:
        print(f"接收到的完整JSON: {data}")
        # 像操作字典一样获取数据
        db = SimpleDBManager(db_config)
        result = db.insert(data.get("数据类别"), data)
        # 调用你的数据库存储，将对应字段存进去就ok了
        # 调用数据库吧 皮卡丘
     
        return {
            "code": 200,
            "message": "数据已接收并保存成功",
            "timestamp": datetime.now().isoformat(),
            "data": result
        }
    except Exception as e:
        return {
            "code": 500,
            "message": f"保存数据时出错: {str(e)}",
            "timestamp": datetime.now().isoformat(),
            "data": None
        }
    
@app.post("/update_data")
async def update_data(data: dict = Body(...)):
    try:
        print(f"接收到的完整JSON: {data}")
        db = SimpleDBManager(db_config)
        result = db.update(data.get("数据类别"), data)
        return {
            "code": 200,
            "message": "数据已接收并保存成功",
            "timestamp": datetime.now().isoformat(),
            "data": result
        }
    except Exception as e:
        return {
            "code": 500,
            "message": f"保存数据时出错: {str(e)}",
            "timestamp": datetime.now().isoformat(),
            "data": None
        }

@app.post("/delete_data")
async def delete_data(data: dict = Body(...)):
    try:
        print(f"接收到的完整JSON: {data}")
        db = SimpleDBManager(db_config)
        result = db.delete(data.get("数据类别"), data)
        return {
            "code": 200,
            "message": "数据已接收并保存成功",
            "timestamp": datetime.now().isoformat(),
            "data": result
        }
    except Exception as e:
        return {
            "code": 500,
            "message": f"保存数据时出错: {str(e)}",
            "timestamp": datetime.now().isoformat(),
            "data": None
        }

@app.get("/select_data")
async def select_data(data: dict = Body(...)):
    try:
        print(f"接收到的完整JSON: {data}")
        db = SimpleDBManager(db_config)
        result = db.select(data.get("数据类别"), data)
        return {
            "code": 200,
            "message": "数据已接收并保存成功",
            "timestamp": datetime.now().isoformat(),
            "data": result
        }
    except Exception as e:
        return {
            "code": 500,
            "message": f"保存数据时出错: {str(e)}",
            "timestamp": datetime.now().isoformat(),
            "data": None
        }
        
@app.get("/report_generation")
def report_generation(year: int, month: int,context: str):
    try:

        generate_report_main(year, month,context)
        return {
            "code": 200,
            "message": "报告已生成",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "code": 500,
            "message": f"生成报告时出错: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }
    
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8765)