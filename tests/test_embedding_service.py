import unittest
from unittest.mock import patch

from services.embedding_service import EmbeddingService


class FakeEmbeddingModel:
    def __init__(self, **kwargs):
        self.calls = []

    def embed_documents(self, texts):
        self.calls.append(list(texts))
        return [[float(len(text))] for text in texts]

    def embed_query(self, text):
        return [float(len(text))]


class EmbeddingServiceTest(unittest.TestCase):
    @patch("services.embedding_service.DashScopeEmbeddings", FakeEmbeddingModel)
    def test_documents_are_split_into_batches_of_at_most_twenty(self):
        service = EmbeddingService("key", "qwen3.7-text-embedding-flash")
        vectors = service.embed_documents([f"text-{index}" for index in range(21)])

        self.assertEqual(len(vectors), 21)
        self.assertEqual([len(batch) for batch in service.embeddings_model.calls], [20, 1])

    @patch("services.embedding_service.DashScopeEmbeddings", FakeEmbeddingModel)
    def test_blank_query_is_rejected(self):
        service = EmbeddingService("key", "qwen3.7-text-embedding-flash")
        with self.assertRaises(ValueError):
            service.embed_query("  ")


if __name__ == "__main__":
    unittest.main()
