"""
为Dify提供RAGFlow HTTP桥接服务
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any

import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class RetrievalSetting(BaseModel):
    """检索设置"""

    top_k: int = Field(default=5, description="检索结果的最大数量")
    score_threshold: float = Field(
        default=0.5, description="结果与查询相关性的分数限制，范围：0~1"
    )


class MetadataCondition(BaseModel):
    """元数据筛选条件"""

    logical_operator: str = Field(
        default="and", description="逻辑操作符，取值为 and 或 or"
    )
    conditions: List[Dict[str, Any]] = Field(description="条件列表")


class DifyRetrievalRequest(BaseModel):
    """Dify外部知识库检索请求"""

    knowledge_id: str = Field(description="知识库唯一 ID")
    query: str = Field(description="用户的查询")
    retrieval_setting: RetrievalSetting = Field(description="知识检索参数")
    metadata_condition: Optional[MetadataCondition] = Field(
        None, description="元数据筛选"
    )


class RAGFlowBridge:
    """RAGFlow桥接服务类"""

    def __init__(self):
        self.base_url = os.getenv("RAGFLOW_BASE_URL", "http://localhost")
        self.port = os.getenv("RAGFLOW_PORT", "80")
        logger.info(f"RAGFlow url: {self.base_url}:{self.port}")

    async def retrieve_chunks(
        self,
        question: str,
        api_key: str,
        dataset_ids: List[str],
        top_k: int = 20,  # RAGFlow默认值
        similarity_threshold: float = 0.2,  # RAGFlow默认值
        # page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """
        从RAGFlow检索文档块

        参数映射：
        - Dify.query -> RAGFlow.question
        - Dify.knowledge_id -> RAGFlow.dataset_ids[0]
        - Dify.retrieval_setting.top_k -> RAGFlow.top_k (但RAGFlow的top_k是参与向量计算的数量)
        - Dify.retrieval_setting.score_threshold -> RAGFlow.similarity_threshold
        """
        url = f"{self.base_url}:{self.port}/api/v1/retrieval"

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        }

        # 构建RAGFlow请求数据
        data = {
            "question": question,
            "dataset_ids": dataset_ids,  # 必需参数
            "top_k": top_k,
            "similarity_threshold": similarity_threshold,
            # "page": 1,
            "page_size": page_size,
        }

        logger.info(
            f"Calling RAGFlow API with data: {json.dumps(data, ensure_ascii=False)}"
        )

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url, json=data, headers=headers, timeout=30
                )
                response.raise_for_status()
                result = response.json()

                logger.info(f"RAGFlow API response code: {result.get('code')}")
                return result

        except httpx.RequestError as e:
            logger.error(f"RAGFlow request failed: {e}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse RAGFlow response: {e}")
            raise
        except Exception as e:
            logger.error(f"RAGFlow retrieval error: {e}")
            raise

    def convert_to_dify_format(
        self, ragflow_response: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        将RAGFlow响应转换为Dify外部知识库API格式

        RAGFlow响应格式：
        {
            "code": 0,
            "data": {
                "chunks": [
                    {
                        "content": "ragflow content",
                        "document_keyword": "1.txt",
                        "highlight": "<em>ragflow</em> content",
                        "id": "chunk_id",
                        "document_id": "doc_id",
                        "kb_id": "kb_id",
                        "similarity": 0.966,
                        "vector_similarity": 0.889,
                        "term_similarity": 1.0,
                        "important_keywords": ["keyword1"]
                    }
                ]
            }
        }

        Dify期望格式：
        {
            "records": [
                {
                    "content": "文本内容",
                    "score": 0.966,
                    "title": "文档标题",
                    "metadata": {...}
                }
            ]
        }
        """
        if ragflow_response.get("code") != 0:
            # RAGFlow返回错误
            error_msg = ragflow_response.get("message", "Unknown error")
            logger.error(f"RAGFlow error: {error_msg}")
            return {"error_code": 2001, "error_msg": f"RAGFlow error: {error_msg}"}

        data = ragflow_response.get("data", {})
        chunks = data.get("chunks", [])

        records = []
        for chunk in chunks:
            # 优先使用高亮内容，如果没有则使用原始内容
            content = chunk.get("content", "")

            # 构建符合Dify格式的记录
            record = {
                "content": content,  # 必需：文本块内容
                "score": float(chunk.get("similarity", 0.0)),  # 必需：相关性分数
                "title": chunk.get("document_keyword", ""),  # 必需：文档标题
                "metadata": {  # 可选：元数据
                    "document_id": chunk.get("document_id", ""),
                    "kb_id": chunk.get("kb_id", ""),
                    "chunk_id": chunk.get("id", ""),
                    "vector_similarity": float(chunk.get("vector_similarity", 0.0)),
                    "term_similarity": float(chunk.get("term_similarity", 0.0)),
                    "important_keywords": chunk.get("important_keywords", []),
                },
            }

            records.append(record)

        logger.info(f"Converted {len(records)} records to Dify format")
        return {"records": records}


def create_bridge_app() -> FastAPI:
    """创建桥接服务FastAPI应用"""
    app = FastAPI(
        title="Dify-RAGFlow Bridge API",
        description="桥接服务：为Dify提供RAGFlow知识库访问",
        version="1.0.0",
    )

    # 创建全局桥接实例
    ragflow_bridge = RAGFlowBridge()

    @app.post("/retrieval")
    async def dify_external_knowledge_retrieval(
        request: DifyRetrievalRequest, http_request: Request
    ):
        """
        Dify外部知识库检索接口

        为Dify提供符合其外部知识库API规范的检索服务，底层调用RAGFlow API
        """
        try:
            print(request)
            print(http_request)

            # 验证Authorization头
            auth_header = http_request.headers.get("authorization")
            if not auth_header:
                raise HTTPException(
                    status_code=403,
                    detail={
                        "error_code": 1001,
                        "error_msg": "无效的 Authorization 头格式。预期格式为 Bearer <api-key>。",
                    },
                )

            if not auth_header.startswith("Bearer "):
                raise HTTPException(
                    status_code=403,
                    detail={
                        "error_code": 1001,
                        "error_msg": "无效的 Authorization 头格式。预期格式为 Bearer <api-key>。",
                    },
                )

            api_key = auth_header[7:]  # 移除 "Bearer " 前缀

            # 验证API密钥非空
            if not api_key:
                raise HTTPException(
                    status_code=403,
                    detail={"error_code": 1002, "error_msg": "授权失败"},
                )

            logger.info(
                f"Processing retrieval request for knowledge_id: {request.knowledge_id}, query: {request.query}"
            )

            # 记录metadata_condition（RAGFlow不直接支持，但记录日志以便调试）
            if request.metadata_condition:
                logger.info(
                    f"Metadata condition received (not supported by RAGFlow): {request.metadata_condition}"
                )

            # 参数映射和处理
            dify_top_k = request.retrieval_setting.top_k
            dify_score_threshold = request.retrieval_setting.score_threshold or 0.2

            # RAGFlow的top_k实际是参与向量计算的数量，通常设置较大值
            # 而page_size控制返回的结果数量，这里用Dify的top_k作为page_size
            ragflow_top_k = dify_top_k
            ragflow_page_size = dify_top_k  # 返回结果数量

            # 调用RAGFlow API，使用Dify传递的API密钥
            ragflow_response = await ragflow_bridge.retrieve_chunks(
                question=request.query,  # Dify.query -> RAGFlow.question
                api_key=api_key,  # Dify Authorization -> RAGFlow Authorization
                dataset_ids=[
                    request.knowledge_id
                ],  # Dify.knowledge_id -> RAGFlow.dataset_ids
                top_k=ragflow_top_k,  # 向量计算数量
                similarity_threshold=dify_score_threshold,  # Dify.score_threshold -> RAGFlow.similarity_threshold
                page_size=ragflow_page_size,  # 返回结果数量
            )

            # 转换为Dify格式
            dify_response = ragflow_bridge.convert_to_dify_format(ragflow_response)

            # 检查是否有错误
            if "error_code" in dify_response:
                if dify_response["error_code"] == 2001:
                    raise HTTPException(status_code=404, detail=dify_response)
                else:
                    raise HTTPException(status_code=500, detail=dify_response)

            logger.info(
                f"Successfully retrieved {len(dify_response.get('records', []))} records"
            )

            return JSONResponse(content=dify_response)

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"External knowledge retrieval failed: {e}")
            error_response = {
                "error_code": 500,
                "error_msg": f"Internal server error: {str(e)}",
            }
            raise HTTPException(status_code=500, detail=error_response)

    @app.get("/health")
    async def health_check():
        """健康检查端点"""
        return {
            "status": "healthy",
            "ragflow_base_url": ragflow_bridge.base_url,
            "note": "API密钥通过Dify请求传递，无需预配置",
        }

    @app.get("/")
    async def root():
        """根端点"""
        return {
            "message": "Dify-RAGFlow Bridge API",
            "version": "1.0.0",
            "endpoints": {
                "retrieval": "POST /retrieval",
                "health": "GET /health",
                "docs": "GET /docs",
            },
        }

    return app
