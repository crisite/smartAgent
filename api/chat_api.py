import logging
from collections.abc import Callable
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request

from services.chat_service import ChatService, ModelCallError, create_chat_service
from schemas.chat import ChatRequest, ChatResponse

logger = logging.getLogger(__name__)


def create_app(service_factory: Callable[[], ChatService] = create_chat_service) -> FastAPI:
    """创建 HTTP 应用。

    service_factory 只用于在应用启动时创建一次 ChatService；测试时可以传入
    一个假的工厂，避免测试请求真正调用 DeepSeek。
    """

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # lifespan 是 FastAPI 的启动/关闭生命周期钩子。
        # 这里在启动时初始化一次模型服务，所有请求复用它。
        app.state.chat_service = service_factory()
        yield

    app = FastAPI(title="Smart Agent", lifespan=lifespan)

    @app.post("/api/chat", response_model=ChatResponse)
    def chat(body: ChatRequest, request: Request):
        # Pydantic 先完成 JSON 类型校验；这里再处理空白字符串。
        question = body.question.strip()
        if not question:
            raise HTTPException(status_code=400, detail="问题不能为空")
        try:
            return request.app.state.chat_service.ask(question)
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        except ModelCallError as error:
            logger.exception("DeepSeek 模型调用失败")
            raise HTTPException(status_code=500, detail="模型调用失败，请稍后重试") from error

    return app


app = create_app()
