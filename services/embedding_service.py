from collections.abc import Sequence
from langchain_community.embeddings.dashscope import DashScopeEmbeddings
from settings import load_embedding_settings


class EmbeddingService:
    def __init__(
        self,
        api_key: str,
        model: str,
        *,
        max_retries: int = 2,
        max_batch_size: int = 20,
    ):
        if not api_key or not api_key.strip():
            raise ValueError("API Key 不能为空")
        if not model or not model.strip():
            raise ValueError("模型名称不能为空")
        if max_retries < 1:
            raise ValueError("max_retries 必须是正整数")
        if not 1 <= max_batch_size <= 20:
            raise ValueError("max_batch_size 必须是 1 到 20 的整数")
        self.model_name = model.strip()
        self.max_batch_size = max_batch_size
        self.embeddings_model = DashScopeEmbeddings(
            model=self.model_name,
            dashscope_api_key=api_key.strip(),
            max_retries=max_retries,
        )

    def embed_query(self, text: str) -> list[float]:
        if not text or not text.strip():
            raise ValueError("待向量化的问题不能为空")
        return self.embeddings_model.embed_query(text.strip())

    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        values = [text.strip() for text in texts]
        if any(not text for text in values):
            raise ValueError("文档内容不能为空")
        vectors: list[list[float]] = []
        for start in range(0, len(values), self.max_batch_size):
            batch = values[start : start + self.max_batch_size]
            vectors.extend(self.embeddings_model.embed_documents(batch))
        return vectors

def create_embeddings_service() -> EmbeddingService:
    config = load_embedding_settings()
    return EmbeddingService(
        config.api_key,
        config.model,
        max_retries=config.max_retries,
        max_batch_size=config.max_batch_size,
    )

