from fastapi import FastAPI, Body,Query
from typing import Union
from fastapi.middleware.cors import CORSMiddleware
from extra_query_by_agent import DataExtractor
from datetime import datetime
import uvicorn
from intend_by_agent import IntentRecognizer
from json_to_database import SimpleDBManager
from generate_report import generate_report_main
from chat_by_agent import chat_with_model
# 导入年月提取器（如果存在）
from pydantic import BaseModel
from typing import Any, Optional
from datetime import datetime
from enum import Enum
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



class IntentEnum(str, Enum):
    CHAT = "chat"
    REPORT = "report"
    INSERT = "insert"
    UPDATE = "update"
    DELETE = "delete"
    QUERY = "query"

class ResponseModel(BaseModel):
    code: int = 200
    message: str
    intent: Optional[str] = None  # 明确告诉前端识别出的意图
    data: Any = None
    timestamp: str = datetime.now().isoformat()

# 2. 建议将数据库实例放在外面（单例模式），避免重复连接开销
db = SimpleDBManager(db_config)
# 后台-判断意图-分支逻辑
@app.get("/intent",summary="判断意图",description="判断意图（chat/report/insert/update/delete/query），然后根据意图进行相应的处理",tags=["意图判断"])
def intent_classifier(context: str = Query(default="张三存款一万元",description="前端对话请求，然后说问题",
        example="张三存款一万元/你好/A公司签了合同，金额5万/删除回款记录/修改回款金额为10万/查询所有回款记录/帮我统计一下这个月的回款情况/今天天气不错")):
    try:
        # 1. 意图识别
        recognizer = IntentRecognizer()
        intent_str = recognizer.recognize_intent(context)
        print(f"识别到的意图: {intent_str}")

        # 2. 初始化返回基础数据
        result_data = None
        message = intent_str

        # 3. 分支逻辑处理
        if intent_str == IntentEnum.CHAT:
            result_data = chat_with_model(context)

        elif intent_str == IntentEnum.REPORT:
            result_data = generate_report_main(context)

        elif intent_str == IntentEnum.INSERT:
            print(intent_str)
            extractor = DataExtractor()
            result_data = extractor.extract_with_dialog(context)

 
        elif intent_str in [IntentEnum.DELETE, IntentEnum.UPDATE,IntentEnum.QUERY]:
            extractor = DataExtractor()
            extracted_data = extractor.extract_with_dialog(context)
            if extracted_data and len(extracted_data) > 0:
                first_data = extracted_data[0]
                table_name = first_data.get("数据类别")
                exclude_values = [None, "", 0, "0", 0.0]
                data_modify = {
                            k: v for k, v in first_data.items() 
                            if k != "数据类别" and v not in exclude_values
                        }
                result_data = db.select(table_name, data_modify)
                print(result_data)
      
            else:
                result_data = {"error": "未能提取到有效数据"}


        else:
            # 未知意图处理
            return ResponseModel(
                code=400, 
                message="未能识别有效意图", 
                intent="unknown",
                timestamp=datetime.now().isoformat()
            )

        # 4. 统一返回
        return ResponseModel(
            code=200,
            message="success",
            intent=intent_str,
            timestamp=datetime.now().isoformat(),
            data=result_data,
        )

    except Exception as e:
        return ResponseModel(
            code=500,
            message=f"服务器内部错误: {str(e)}",
            intent="error",
            timestamp=datetime.now().isoformat()
        )



@app.post("/add_data", summary="新增记录", response_model=ResponseModel)
async def add_data(
    data: dict = Body(
        ..., 
        description="要插入的数据字典，必须包含'数据类别'字段",
        example={
            "数据类别": "回款",
            "公司名称": "某某科技有限公司",
            "负责人": "张三",
            "确定回款": 50000,
            "项目类型": "软件开发",
            "项目名称": "saas"
        }
    )
):
    try:
        table_name = data.get("数据类别")
        data_modify = {k: v for k, v in data.items() if k != "数据类别" and v is not None}
        result = db.insert(table_name, data_modify)
        return ResponseModel(message="数据新增成功", data=result)
    except Exception as e:
        return ResponseModel(code=500, message=f"新增失败: {str(e)}")


@app.post("/update_data", summary="修改记录", response_model=ResponseModel)
async def update_data(
    data: dict = Body(
        ...,
        description="更新数据，需包含'数据类别'和定位记录的标识（如项目名称或ID）",
        example={
            "数据类别": "回款",
            "id":"3",
            "公司名称": "某某科技有限公司",
            "负责人": "张三",
            "确定回款": 1,
            "项目类型": "软件开发",
            "项目名称": "saas"
        }
    )
):
    try:
        table_name = data.get("数据类别")
        if not table_name:
            return ResponseModel(code=400, message="缺少关键字段: 数据类别")

        result = db.update(table_name, data)
        return ResponseModel(message="数据更新成功", data=result)
    except Exception as e:
        return ResponseModel(code=500, message=f"更新失败: {str(e)}")


@app.post("/delete_data", summary="删除记录", response_model=ResponseModel)
async def delete_data(
    data: dict = Body(
        ...,
        description="删除条件，需包含'数据类别'和删除依据",
        example={
            "数据类别": "回款",
            "公司名称": "某某科技有限公司",
            "负责人": "张三",
            "确定回款": 1,
            "项目类型": "软件开发",
            "项目名称": "saas"
        }
    )
):
    try:
        table_name = data.get("数据类别")
        if not table_name:
            return ResponseModel(code=400, message="缺少关键字段: 数据类别")

        result = db.delete(table_name, data)
        return ResponseModel(message="数据删除成功", data=result)
    except Exception as e:
        return ResponseModel(code=500, message=f"删除失败: {str(e)}")


@app.post("/select_data", summary="查询记录", response_model=ResponseModel)
async def select_data(
    data: dict = Body(
        ...,
        description="查询过滤条件。若只传'数据类别'则查询该类别的全部数据",
        example={
            "数据类别": "回款",
            "公司名称": "某某科技有限公司",
            "负责人": "张三",
            "确定回款": 1,
            "项目类型": "软件开发",
            "项目名称": "saas"
        }
    )
):
    try:
        table_name = data.get("数据类别")
        if not table_name:
            return ResponseModel(code=400, message="缺少关键字段: 数据类别")

        # 提取查询条件，排除"数据类别"字段
        query_params = {k: v for k, v in data.items() if k != "数据类别"}
        
        result = db.select(table_name, query_params if query_params else None)
        return ResponseModel(message="数据查询成功", data=result)
    except Exception as e:
        return ResponseModel(code=500, message=f"查询失败: {str(e)}")
        

    
if __name__ == "__main__":
    uvicorn.run(app, host="10.3.0.36", port=8765)