"""Coordinate document loading, embedding, and Qdrant upserts."""

from collections.abc import Sequence

from langchain_core.documents import Document

from loader.custom_txt_loader import TxtLoader
from loader.markdown_loader import MarkdownLoader
from loader.pdf_loader import PdfLoader
from schemas.document import DocumentChunk
from services.embedding_service import EmbeddingService, create_embeddings_service
from services.vector_store_service import VectorStoreService
from settings import QdrantSettings, load_qdrant_settings


class IndexingService:
    """Index chunks from any supported loader using one shared pipeline."""

    def __init__(
        self,
        embedding_service: EmbeddingService | None = None,
        vector_store: VectorStoreService | None = None,
        *,
        qdrant_settings: QdrantSettings | None = None,
    ):
        self.qdrant_settings = qdrant_settings or load_qdrant_settings()
        self.embedding_service = embedding_service or create_embeddings_service()
        self.vector_store = vector_store or VectorStoreService(
            url=self.qdrant_settings.url,
            collection_name=self.qdrant_settings.collection_name,
            vector_size=self.qdrant_settings.vector_size,
        )

    def index_chunks(self, chunks: Sequence[DocumentChunk]) -> int:
        """Embed and upsert chunks; return zero without external calls if empty."""
        if not chunks:
            return 0

        documents: list[Document] = [chunk.to_langchain_document() for chunk in chunks]
        vectors = self.embedding_service.embed_documents(
            [document.page_content for document in documents]
        )
        if len(vectors) != len(documents):
            raise ValueError(
                f"Embedding 返回 {len(vectors)} 个向量，但输入有 {len(documents)} 个片段"
            )

        for index, vector in enumerate(vectors):
            if len(vector) != self.qdrant_settings.vector_size:
                raise ValueError(
                    f"第 {index + 1} 个向量维度为 {len(vector)}，"
                    f"配置的 Qdrant collection 要求 {self.qdrant_settings.vector_size}"
                )

        self.vector_store.ensure_collection()
        return self.vector_store.upsert_documents(documents, vectors)

    def index_markdown(self, filename: str) -> int:
        """Load and index one Markdown file."""
        return self.index_chunks(MarkdownLoader().load(filename))

    def index_pdf(self, filename: str) -> int:
        """Load and index one PDF file."""
        return self.index_chunks(PdfLoader().load(filename))

    def index_txt(self, filename: str) -> int:
        """Load and index one text file."""
        return self.index_chunks(TxtLoader().load(filename))
