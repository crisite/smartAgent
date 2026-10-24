"""向量化少量 Markdown chunk，写入 Qdrant 并打印 Top-K 命中。"""

from langchain_core.documents import Document

from loader.pdf_loader import PdfLoader
from services.embedding_service import create_embeddings_service
from services.vector_store_service import VectorStoreService
from settings import load_qdrant_settings


def main() -> None:
    # chunks = MarkdownLoader().load("04-大模型接入与智能素材开发篇.md")[:8]
    loader = PdfLoader()
    documents = loader.load(filename='Python廖雪峰.pdf')[:8]
    chunks: list[Document] = []
    for document in documents:
        chunk = document.to_langchain_document()
        chunks.append(chunk)
    if not chunks:
        raise RuntimeError("Markdown Loader 没有返回可索引的片段")

    embeddings = create_embeddings_service()
    vectors = embeddings.embed_documents([chunk.page_content for chunk in chunks])
    qdrant_settings = load_qdrant_settings()
    actual_vector_size = len(vectors[0])
    if actual_vector_size != qdrant_settings.vector_size:
        raise ValueError(
            f"配置的 Qdrant 向量维度为 {qdrant_settings.vector_size}，"
            f"但 Embedding 模型返回 {actual_vector_size} 维；请检查 config.yaml"
        )

    store = VectorStoreService(
        url=qdrant_settings.url,
        collection_name=qdrant_settings.collection_name,
        vector_size=qdrant_settings.vector_size,
    )
    store.ensure_collection()


    stored = store.upsert_documents(chunks, vectors)

    question = "如何定义一个什么事也不做的空函数"
    query_vector = embeddings.embed_query(question)
    matches = store.search(query_vector, limit=3)

    print(f"collection: {store.collection_name}")
    print(f"向量维度: {qdrant_settings.vector_size}")
    print(f"本次写入: {stored} 个片段")
    print("Top-K 检索结果:")
    for index, match in enumerate(matches, start=1):
        print(
            f"{index}. score={match['score']:.4f} "
            f"source={match['source']} title={match['title'] or '-'}"
        )
        print(match["page_content"][:240].replace("\n", " "))


if __name__ == "__main__":
    main()
