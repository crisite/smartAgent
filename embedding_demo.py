"""用两段文本验证 Embedding 和余弦相似度。

运行前需要配置 config.yaml 中声明的 ALI_API_KEY 环境变量：
    python embedding_demo.py
"""

import math

from services.embedding_service import create_embeddings_service


def cosine_similarity(left: list[float], right: list[float]) -> float:
    """计算两个向量的余弦相似度，结果越大表示方向越接近。"""
    if len(left) != len(right):
        raise ValueError("两个向量的维度不一致")
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    if left_norm == 0 or right_norm == 0:
        raise ValueError("向量不能是全零向量")
    return sum(a * b for a, b in zip(left, right)) / (left_norm * right_norm)


def main() -> None:
    documents = [
        "通用离线导出组件支持异步导出、任务管理、分批处理和流式写出。",
        "Markdown 可以使用标题、列表和代码块组织学习笔记。",
    ]
    question = "怎样降低大量数据导出时的内存占用？"

    service = create_embeddings_service()
    document_vectors = service.embed_documents(documents)
    query_vector = service.embed_query(question)

    if len(document_vectors) != len(documents):
        raise RuntimeError("文档数量与向量数量不一致")

    scores = [cosine_similarity(query_vector, vector) for vector in document_vectors]
    print(f"文档数量：{len(document_vectors)}")
    print(f"向量维度：{len(query_vector)}")
    print(f"第一个文档向量前 5 个值：{document_vectors[0][:5]}")
    print(f"问题向量前 5 个值：{query_vector[:5]}")
    for index, score in enumerate(scores, start=1):
        print(f"文档 {index} 相似度：{score:.6f}")


if __name__ == "__main__":
    main()
