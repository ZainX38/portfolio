from contextlib import closing
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from fastapi import HTTPException
from fastapi.testclient import TestClient

from config import EMBEDDING_MODEL, PROVIDER
from llm import index_matches_configuration
from limits import UsageLimits
from main import app
from rag import SYSTEM_PROMPT, answer_question, build_context, retrieve
from repository import Repository
from test_snapshot import make_bundle


def indexed_repository():
    bundle = make_bundle()
    bundle["embeddings"] = {
        "provider": PROVIDER, "model": EMBEDDING_MODEL, "digest": "test-digest", "snapshot_id": bundle["snapshot_id"],
        "dimensions": 2, "chunk_ids": [chunk["id"] for chunk in bundle["chunks"]], "vectors": [[1.0, 0.0]],
    }
    return Repository(bundle)


def generated_answer(*args, **kwargs):
    kwargs["before_generation"]()
    return {"answer": "hello", "references": []}


class RagTests(unittest.TestCase):
    def test_api_enforces_quota_before_model_calls(self):
        with tempfile.TemporaryDirectory() as folder:
            repository = indexed_repository()
            limits = UsageLimits(Path(folder) / "usage.sqlite", 10, 10, 1)
            app.state.repository = repository
            app.state.limits = limits
            try:
                with patch("main.provider_configured", return_value=True), patch("main.MAX_QUESTION_CHARS", 1000), patch("main.MAX_OUTPUT_TOKENS", 500), patch("main.answer_question", side_effect=generated_answer) as answer:
                    client = TestClient(app)
                    body = {"question": "hello", "snapshot_id": repository.id}
                    self.assertEqual(client.post("/api/demo/ask", json={**body, "question": ""}).status_code, 422)
                    self.assertEqual(client.post("/api/demo/ask", json=body).json()["questions_remaining"], 2)
                    self.assertEqual(client.post("/api/demo/ask", json=body).json()["questions_remaining"], 1)
                    self.assertEqual(client.post("/api/demo/ask", json=body).json()["questions_remaining"], 0)
                    rejected = client.post("/api/demo/ask", json=body)
                    self.assertEqual(rejected.status_code, 429)
                    self.assertEqual(rejected.json()["detail"]["questions_remaining"], 0)
                    self.assertEqual(client.get("/api/demo/repository").json()["questions_remaining"], 0)
                    self.assertEqual(answer.call_count, 3)
            finally:
                app.state.limits = None

    def test_missing_provider_configuration_does_not_consume_allowance(self):
        with tempfile.TemporaryDirectory() as folder:
            repository = indexed_repository()
            app.state.repository = repository
            app.state.limits = UsageLimits(Path(folder) / "usage.sqlite", 10, 10, 1)
            client = TestClient(app)
            body = {"question": "hello", "snapshot_id": repository.id}
            try:
                with patch("main.provider_configured", return_value=False), patch("main.answer_question") as answer:
                    self.assertEqual(client.post("/api/demo/ask", json=body).status_code, 503)
                    answer.assert_not_called()
                with patch("main.provider_configured", return_value=True):
                    self.assertEqual(client.get("/api/demo/repository").json()["questions_remaining"], 3)
                with patch("main.provider_configured", return_value=True), patch("main.answer_question", side_effect=ValueError("embedding failed")):
                    self.assertEqual(client.post("/api/demo/ask", json=body).status_code, 503)
                with patch("main.provider_configured", return_value=True), patch("main.answer_question", side_effect=generated_answer):
                    self.assertEqual(client.post("/api/demo/ask", json=body).json()["questions_remaining"], 2)
            finally:
                app.state.limits = None

    def test_retrieval_and_context_use_snapshot(self):
        repository = indexed_repository()
        chunks = retrieve(repository, [1.0, 0.0])
        self.assertEqual(chunks[0]["path"], "src/example.py")
        excerpts = build_context(chunks, "What does hello return?", 500)
        self.assertIn("return 'hello'", excerpts[0]["text"])

    def test_legacy_ollama_index_cannot_be_used_for_openai_queries(self):
        repository = indexed_repository()
        repository.embeddings.pop("provider")
        with patch("llm.PROVIDER", "openai"), patch("llm.EMBEDDING_MODEL", repository.embeddings["model"]):
            self.assertFalse(index_matches_configuration(repository))

    def test_large_first_result_leaves_room_for_adjacent_implementation(self):
        first = "# Background documentation\n" * 100
        second = "def apply_header(request):\n    request.headers['Authorization'] = 'Basic example'\n    return request\n"
        chunks = [
            {"id": "chunk-1", "path": "source.py", "start_line": 1, "end_line": 100, "text": first},
            {"id": "chunk-2", "path": "source.py", "start_line": 101, "end_line": 103, "text": second},
        ]
        question = "How is the authorization header applied?"
        excerpts = build_context(chunks, question, 500)
        self.assertEqual([item["id"] for item in excerpts], ["chunk-1", "chunk-2"])
        self.assertIn("request.headers", excerpts[1]["text"])
        source = (first + second).splitlines(keepends=True)
        for excerpt in excerpts:
            self.assertEqual(excerpt["text"], "".join(source[excerpt["start_line"] - 1:excerpt["end_line"]]))
        context = "\n\n".join(f"[{item['id']}] {item['path']}:{item['start_line']}-{item['end_line']}\n{item['text']}" for item in excerpts)
        from config import CONTEXT_TOKENS
        self.assertLessEqual(len(context.encode()) + len(SYSTEM_PROMPT.encode()) + len(question.encode()) + 500 + 512, CONTEXT_TOKENS)

    def test_grounded_references_come_from_exact_context_spans(self):
        repository = indexed_repository()
        with patch("rag.model_digest", return_value="test-digest"), patch("rag.embed", return_value=[[1.0, 0.0]]), patch("rag.generate", return_value={"answer": "It returns hello.", "citations": ["source-1"]}):
            answer = answer_question(repository, "What does hello return?", 500)
        reference = answer["references"][0]
        self.assertEqual(reference["path"], "src/example.py")
        self.assertEqual(reference["start_line"], 2)
        self.assertEqual(reference["end_line"], 2)
        self.assertIn("a" * 40, reference["url"])

    def test_invented_citations_and_model_changes_fail_closed(self):
        repository = indexed_repository()
        with patch("rag.model_digest", return_value="changed"):
            with self.assertRaises(ValueError):
                answer_question(repository, "hello", 500)
        with patch("rag.model_digest", return_value="test-digest"), patch("rag.embed", return_value=[[1.0, 0.0]]), patch("rag.generate", return_value={"answer": "Invented", "citations": ["unknown"]}):
            with self.assertRaises(ValueError):
                answer_question(repository, "hello", 500)

    def test_no_citations_returns_insufficient_evidence(self):
        with patch("rag.model_digest", return_value="test-digest"), patch("rag.embed", return_value=[[1.0, 0.0]]), patch("rag.generate", return_value={"answer": "Unsupported claim", "citations": []}):
            answer = answer_question(indexed_repository(), "hello", 500)
        self.assertIn("cannot determine", answer["answer"])

    def test_daily_limit_survives_restart_after_generation_is_accepted(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "usage.sqlite"
            limits = UsageLimits(path, 1, 3, 1)
            with self.assertRaises(ValueError):
                with limits.reserve("visitor") as reservation:
                    reservation.accept()
                    raise ValueError("model failed")
            restarted = UsageLimits(path, 1, 3, 1)
            with self.assertRaises(HTTPException) as error:
                with restarted.reserve("another-visitor"):
                    self.fail("Daily quota must not reset")
            self.assertEqual(error.exception.status_code, 429)

    def test_concurrency_and_per_ip_limits(self):
        with tempfile.TemporaryDirectory() as folder:
            limits = UsageLimits(Path(folder) / "usage.sqlite", 10, 1, 1)
            with limits.reserve("visitor") as reservation:
                with self.assertRaises(HTTPException):
                    with limits.reserve("another-visitor"):
                        self.fail("Concurrency limit bypassed")
                reservation.accept()
            with self.assertRaises(HTTPException):
                with limits.reserve("visitor"):
                    self.fail("IP limit bypassed")
            with limits.reserve("another-visitor") as reservation:
                reservation.accept()

    def test_anonymous_daily_limit_survives_restart(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "usage.sqlite"
            visitor = "persistent-visitor"
            with UsageLimits(path, 10, 10, 1).reserve("ip", visitor) as reservation:
                self.assertEqual(reservation.accept(), 2)
            with UsageLimits(path, 10, 10, 1).reserve("ip", visitor) as reservation:
                self.assertEqual(reservation.accept(), 1)
            with UsageLimits(path, 10, 10, 1).reserve("ip", visitor) as reservation:
                self.assertEqual(reservation.accept(), 0)
            restarted = UsageLimits(path, 10, 10, 1)
            self.assertEqual(restarted.remaining(visitor), 0)
            with self.assertRaises(HTTPException):
                with restarted.reserve("ip", visitor):
                    self.fail("Anonymous quota must not reset")
            with closing(sqlite3.connect(path)) as database, database:
                database.execute(
                    "INSERT INTO visitor_daily_usage VALUES (?, ?, ?)",
                    ("previous-day-visitor", "2000-01-01", 3),
                )
            self.assertEqual(restarted.remaining("previous-day-visitor"), 3)


if __name__ == "__main__":
    unittest.main()
