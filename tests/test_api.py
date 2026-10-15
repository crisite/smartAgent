import unittest

from fastapi.testclient import TestClient

from api.chat_api import create_app


class FakeChatService:
    def ask(self, question: str) -> dict:
        return {
            "answer": f"收到：{question}",
            "usage": None,
            "model": "fake-model",
        }


class ChatApiTest(unittest.TestCase):
    def test_chat_returns_typed_response(self):
        with TestClient(create_app(lambda: FakeChatService())) as client:
            response = client.post("/api/chat", json={"question": "  你好  "})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["answer"], "收到：你好")
        self.assertIsNone(response.json()["usage"])

    def test_blank_question_returns_bad_request(self):
        with TestClient(create_app(lambda: FakeChatService())) as client:
            response = client.post("/api/chat", json={"question": "   "})

        self.assertEqual(response.status_code, 400)


if __name__ == "__main__":
    unittest.main()
