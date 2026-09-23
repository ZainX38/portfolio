import unittest
from unittest.mock import Mock, patch

from config import ANSWER_MODEL, CONTEXT_TOKENS, EMBEDDING_MODEL
from llm import embed, generate


class OllamaAdapterTests(unittest.TestCase):
    def test_generation_is_bounded_and_unloads_model(self):
        response = Mock()
        response.json.return_value = {"done_reason": "stop", "message": {"content": '{"answer":"example","citations":[]}'}}
        with patch("llm.httpx.post", return_value=response) as post:
            generate([{"role": "user", "content": "example"}], 300)
        payload = post.call_args.kwargs["json"]
        self.assertEqual(payload["model"], ANSWER_MODEL)
        self.assertEqual(payload["keep_alive"], 0)
        self.assertFalse(payload["stream"])
        self.assertEqual(payload["options"]["num_ctx"], CONTEXT_TOKENS)
        self.assertEqual(payload["options"]["num_predict"], 300)

    def test_embedding_disallows_silent_truncation(self):
        response = Mock()
        response.json.return_value = {"embeddings": [[1.0, 0.0]]}
        with patch("llm.httpx.post", return_value=response) as post:
            self.assertEqual(embed(["source"]), [[1.0, 0.0]])
        payload = post.call_args.kwargs["json"]
        self.assertEqual(payload["model"], EMBEDDING_MODEL)
        self.assertFalse(payload["truncate"])
