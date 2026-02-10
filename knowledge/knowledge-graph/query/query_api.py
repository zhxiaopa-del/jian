from fastapi import FastAPI, HTTPException
import uvicorn
from typing import List,Optional
from pydantic import BaseModel
from graphrag_utils import(init,entity_match,recall_triples,format_llm_prompt,rank_triples,TOP_N,TOP_N_TRIPLES)

app=FastAPI(title="文本相似度检索api")

class SearchRequest(BaseModel):
    question: str
    entities: Optional[List[str]]=[]

class GraphRAGRequest(BaseModel):
    question: str
    entities: Optional[List[str]]=[]
    top_n_triple: int = TOP_N_TRIPLES

@app.post("/neo4j/graphrag",response_description="通过提取的实体以及问题，获得匹配度最高的路径信息")
def query_graphrag(payload:GraphRAGRequest):
    try:
        question=payload.question.strip()
        if not question:
            raise HTTPException (
                status_code=400,
                detail={
                    "code":400,
                    "message":"请输入问题",
                    "data":None
                }
            )

        core_entities=entity_match(question,payload.entities)
        if not core_entities:
            # raise HTTPException (
            #     status_code=400,
            #     detail={
            #         "code":400,
            #         "message":"未定位到核心实体",
            #         "data":{
            #         "core_entities":[],
            #         "raw_triple_count":0,
            #         "top_triple_count":0,
            #         "top_triples":[],
            #         "llm_prompt":format_llm_prompt([])
            #     }
            #     }
            # )
            raise HTTPException(
                status_code=400,
                detail={
                    "code": 400,
                    "message": "未定位到核心实体",
                    "data": {
                        "llm_prompt": format_llm_prompt([])
                    }
                }
            )

        raw_triples=recall_triples(core_entities)
        top_triples=rank_triples(question,raw_triples,payload.top_n_triple)
        llm_prompt=format_llm_prompt(top_triples)
        # print(f"llm_prompt:{llm_prompt}")
        # return{
        #     "code":200,
        #     "message":"GraphRAG查询成功",
        #     "data":{
        #         "core_entities":core_entities,
        #         "raw_triple_count":len(raw_triples),
        #         "top_triple_count":len(top_triples),
        #         "top_triples":top_triples,
        #         "llm_prompt":llm_prompt
        #     }
        # }
        return{
            "code":200,
            "message":"GraphRAG查询成功",
            "data":{
                "llm_prompt":llm_prompt
            }
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "code":500,
                "message":f"GraphRAG查询失败:{str(e)}",
                "data":None
            }
        )

if __name__=="__main__":
    print("接口启动")
    init()
    uvicorn.run(app, host="0.0.0.0", port=8000)
