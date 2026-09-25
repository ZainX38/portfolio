import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from config import ANSWER_MODEL, CONTEXT_TOKENS, EMBEDDING_MODEL
from llm import embed, generate


class OpenAIAdapterTests(unittest.TestCase):
    def test_generation_uses_one_bounded_stateless_responses_call(self):
        client = Mock()
        client.responses.create.return_value = SimpleNamespace(
            status="completed", output_text='{"answer":"example","citations":[]}'
        )
        with patch("llm.OPENAI_API_KEY", "test-key"), patch("llm.OpenAI", return_value=client) as sdk:
            result = generate([
                {"role": "system", "content": "system"},
                {"role": "user", "content": "example"},
            ], 400)
        self.assertEqual(result["answer"], "example")
        sdk.assert_called_once_with(api_key="test-key", timeout=180, max_retries=0)
        client.responses.create.assert_called_once()
        payload = client.responses.create.call_args.kwargs
        self.assertEqual(payload["model"], ANSWER_MODEL)
        self.assertEqual(payload["max_output_tokens"], 400)
        self.assertEqual(payload["reasoning"], {"effort": "none"})
        self.assertFalse(payload["store"])
        self.assertNotIn("tools", payload)
        self.assertNotIn("previous_response_id", payload)
        self.assertEqual(payload["input"], "example")

    def test_embedding_uses_configured_model_and_preserves_order(self):
        client = Mock()
        client.embeddings.create.return_value = SimpleNamespace(data=[
            SimpleNamespace(embedding=[1.0, 0.0]),
            SimpleNamespace(embedding=[0.0, 1.0]),
        ])
        with patch("llm.OPENAI_API_KEY", "test-key"), patch("llm.OpenAI", return_value=client):
            self.assertEqual(embed(["one", "two"]), [[1.0, 0.0], [0.0, 1.0]])
        client.embeddings.create.assert_called_once_with(
            model=EMBEDDING_MODEL, input=["one", "two"], encoding_format="float"
        )

    def test_missing_key_fails_before_any_sdk_request(self):
        with patch("llm.OPENAI_API_KEY", ""), patch("llm.OpenAI") as sdk:
            with self.assertRaisesRegex(ValueError, "not configured"):
                generate([{"role": "user", "content": "example"}], 400)
        sdk.assert_not_called()


class OllamaAdapterTests(unittest.TestCase):
    def test_generation_is_bounded_and_unloads_model(self):
        response = Mock()
        response.json.return_value = {"done_reason": "stop", "message": {"content": '{"answer":"example","citations":[]}'}}
        with patch("llm.PROVIDER", "ollama"), patch("llm.httpx.post", return_value=response) as post:
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
        with patch("llm.PROVIDER", "ollama"), patch("llm.httpx.post", return_value=response) as post:
            self.assertEqual(embed(["source"]), [[1.0, 0.0]])
        payload = post.call_args.kwargs["json"]
        self.assertEqual(payload["model"], EMBEDDING_MODEL)
        self.assertFalse(payload["truncate"])
