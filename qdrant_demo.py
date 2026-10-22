"""向量化少量 Markdown chunk，写入 Qdrant 并打印 Top-K 命中。"""

from langchain_core.documents import Document

from loader.markdown_loader import MarkdownLoader
from loader.pdf_loader import PdfLoader
from services.embedding_service import create_embeddings_service
from services.vector_store_service import VectorStoreService


def main() -> None:
    # chunks = MarkdownLoader().load("04-大模型接入与智能素材开发篇.md")[:8]
    loader = PdfLoader()
    documents = loader.load(filename='Python廖雪峰.pdf')
    chunks: list[Document] = []
    for document in documents:
        chunk = document.to_langchain_document()
        chunks.append(chunk)
    if not chunks:
        raise RuntimeError("Markdown Loader 没有返回可索引的片段")

    embeddings = create_embeddings_service()
    vectors = embeddings.embed_documents([chunk.page_content for chunk in chunks])
    vector_size = len(vectors[0])

    store = VectorStoreService(
        url="http://localhost:6333/",
        collection_name="smart_agent_pdf_demo",
        vector_size=vector_size,
    )
    store.ensure_collection()


    stored = store.upsert_documents(chunks, vectors)

    question = "如何定义一个什么事也不做的空函数"
    query_vector = embeddings.embed_query(question)
    matches = store.search(query_vector, limit=3)

    print(f"collection: {store.collection_name}")
    print(f"向量维度: {vector_size}")
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
