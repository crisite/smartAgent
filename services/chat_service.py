from langchain_core.prompts import ChatPromptTemplate
from langchain_deepseek import ChatDeepSeek
from pydantic import SecretStr

from prompt import SYSTEM_PROMPT
from settings import load_settings


class ModelCallError(RuntimeError):
    """模型请求失败，与用户输入错误区分。"""


class ChatService:
    """封装一次模型服务实例及其问答链。"""
    def __init__(
        self,
        api_key: str,
        model: str,
        *,
        base_url: str = "https://api.deepseek.com",
        timeout: float = 60,
        max_retries: int = 1,
    ):
        if not api_key or not api_key.strip():
            raise ValueError("API Key 不能为空")
        if not model or not model.strip():
            raise ValueError("模型名称不能为空")
        self.model = model
        llm = ChatDeepSeek(
            api_key=SecretStr(api_key.strip()),
            model=model,
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries,
        )
        prompt = ChatPromptTemplate([
            ('system', SYSTEM_PROMPT),
            ('human', '{user_input}')
        ])
        self.chain = prompt | llm


    def ask(self, question: str) -> dict:
        question = question.strip()

        if not question:
            raise ValueError("问题不能为空")
        try:
            result = self.chain.invoke(input={'user_input': question})
        except Exception as error:
            raise ModelCallError("模型调用失败，请稍后重试") from error

        usage = None
        metadata = result.usage_metadata
        if metadata is not None:
            names = ("input_tokens", "output_tokens", "total_tokens")
            if all(name in metadata for name in names):
                usage = {name: metadata[name] for name in names}

        return {
            "answer": str(result.text),
            "usage": usage,
            "model": result.response_metadata.get("model_name") or self.model,
        }


def create_chat_service() -> ChatService:
    """按项目配置创建 ChatService；CLI 和 API 共用此入口。"""
    settings = load_settings()
    return ChatService(
        settings.api_key,
        settings.model,
        base_url=settings.base_url,
        timeout=settings.timeout,
        max_retries=settings.max_retries,
    )
