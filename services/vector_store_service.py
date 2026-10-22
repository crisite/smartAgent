from collections.abc import Sequence
import json
from uuid import NAMESPACE_URL, uuid5

from langchain_core.documents import Document


class VectorStoreService:
    def __init__(self, url: str, collection_name: str, vector_size: int, *, client=None):
        if not url or not url.strip():
            raise ValueError("Qdrant URL 不能为空")
        if not collection_name or not collection_name.strip():
            raise ValueError("collection 名称不能为空")
        if isinstance(vector_size, bool) or vector_size <= 0:
            raise ValueError("向量维度必须是正整数")

        if client is None:
            from qdrant_client import QdrantClient

            client = QdrantClient(
                url=url.strip().rstrip("/"),
                trust_env=False,
            )
        self.client = client
        self.collection_name = collection_name.strip()
        self.vector_size = vector_size

    def ensure_collection(self) -> None:
        from qdrant_client import models

        if self.client.collection_exists(self.collection_name):
            collection = self.client.get_collection(self.collection_name)
            vectors = collection.config.params.vectors
            configured_size = vectors.get("size") if isinstance(vectors, dict) else vectors.size
            if configured_size != self.vector_size:
                raise ValueError(
                    f"collection 向量维度为 {configured_size}，当前模型维度为 {self.vector_size}；"
                    "请使用新的 collection 名称或重建 collection"
                )
            return

        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config=models.VectorParams(
                size=self.vector_size,
                distance=models.Distance.COSINE,
            ),
        )

    def upsert_documents(
        self, documents: Sequence[Document], vectors: Sequence[Sequence[float]]
    ) -> int:
        from qdrant_client import models

        if len(documents) != len(vectors):
            raise ValueError("文档数量与向量数量不一致")
        if not documents:
            return 0

        points = []
        for document, vector in zip(documents, vectors):
            if len(vector) != self.vector_size:
                raise ValueError(
                    f"向量维度为 {len(vector)}，collection 要求 {self.vector_size}"
                )
            metadata = dict(document.metadata)
            identity = json.dumps(
                [document.page_content, metadata],
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            )
            points.append(
                models.PointStruct(
                    id=str(uuid5(NAMESPACE_URL, identity)),
                    vector=list(vector),
                    payload={"page_content": document.page_content, "metadata": metadata},
                )
            )

        self.client.upsert(
            collection_name=self.collection_name,
            points=points,
            wait=True,
        )
        return len(points)

    def search(self, query_vector: Sequence[float], *, limit: int = 5) -> list[dict]:
        if isinstance(limit, bool) or limit <= 0:
            raise ValueError("limit 必须是正整数")
        if len(query_vector) != self.vector_size:
            raise ValueError(
                f"查询向量维度为 {len(query_vector)}，collection 要求 {self.vector_size}"
            )

        response = self.client.query_points(
            collection_name=self.collection_name,
            query=list(query_vector),
            limit=limit,
            with_payload=True,
        )
        results = []
        for point in response.points:
            payload = point.payload or {}
            metadata = payload.get("metadata") or {}
            title = metadata.get("title") or " / ".join(
                metadata[key] for key in ("h1", "h2", "h3", "h4", "h5", "h6")
                if metadata.get(key)
            ) or None
            results.append(
                {
                    "page_content": payload.get("page_content", ""),
                    "source": metadata.get("source", "unknown"),
                    "title": title,
                    "score": float(point.score),
                    "metadata": metadata,
                }
            )
        return results
