import io
import unittest
import zipfile
from unittest.mock import patch

from fastapi.testclient import TestClient

from chunking import chunk_files
from config import REPOSITORY, parse_repository
from index_repository import read_archive
from main import app
from repository import Repository, snapshot_id
from coverage import select_chunks


def make_bundle():
    snapshot = {
        "repository": REPOSITORY, "commit": "a" * 40, "branch": "main",
        "files": {"src/example.py": {"content": "def hello():\n    return 'hello'\n"}, "image.png": {"reason": "Unsupported file format"}},
    }
    return {"version": 1, "snapshot": snapshot, "snapshot_id": snapshot_id(snapshot), "chunks": chunk_files(snapshot["files"]), "embeddings": None}


class SnapshotTests(unittest.TestCase):
    def test_selected_scope_preserves_full_explorer_and_expands_without_new_source(self):
        files = {"src/main.py": {"content": "print('source')\n"}, "README.md": {"content": "Read me\n"}, "docs/extra.md": {"content": "Extra docs\n"}}
        chunks = chunk_files(files)
        core, coverage = select_chunks(files, chunks, "selected", ["src/*", "README.md"])
        self.assertEqual(set(coverage["indexed_paths"]), {"src/main.py", "README.md"})
        self.assertEqual(coverage["excluded"]["docs/extra.md"], "Outside the configured index paths")
        expanded, _ = select_chunks(files, chunks, "all")
        for chunk in core:
            self.assertIn(chunk, expanded)
        self.assertIn("docs/extra.md", files)

    def test_repository_configuration(self):
        self.assertEqual(parse_repository("https://github.com/PSF/requests.git/"), "psf/requests")
        self.assertEqual(parse_repository("other/project"), "other/project")
        for value in ("https://example.com/a/b", "a/b/tree/main", "../repo", "a/..", "a/b?token=x"):
            with self.assertRaises(ValueError):
                parse_repository(value)

    def test_different_repository_or_configured_commit_requires_new_index(self):
        bundle = make_bundle()
        with patch("repository.REPOSITORY", "another/project"):
            with self.assertRaisesRegex(ValueError, "different repository"):
                Repository(bundle)
        with patch("repository.REPOSITORY_COMMIT", "b" * 40):
            with self.assertRaisesRegex(ValueError, "different commit"):
                Repository(bundle)

    def test_old_embeddings_rejected_even_when_new_snapshot_checksum_is_valid(self):
        bundle = make_bundle()
        bundle["embeddings"] = {"snapshot_id": bundle["snapshot_id"], "chunk_ids": [c["id"] for c in bundle["chunks"]], "vectors": [[1, 0]]}
        bundle["snapshot"]["commit"] = "b" * 40
        bundle["snapshot_id"] = snapshot_id(bundle["snapshot"])
        with self.assertRaisesRegex(ValueError, "Embeddings do not match"):
            Repository(bundle)

    def test_old_clients_cannot_query_new_snapshot(self):
        previous = Repository(make_bundle())
        bundle = make_bundle()
        bundle["snapshot"]["commit"] = "b" * 40
        bundle["snapshot_id"] = snapshot_id(bundle["snapshot"])
        app.state.repository = Repository(bundle)
        client = TestClient(app)
        with patch("main.answer_question") as answer:
            for route in ("contents", "coverage"):
                self.assertEqual(client.get(f"/api/demo/{route}", params={"snapshot_id": previous.id}).status_code, 409)
            self.assertEqual(client.post("/api/demo/ask", json={"snapshot_id": previous.id, "question": "hello"}).status_code, 409)
            answer.assert_not_called()

    def test_chunks_preserve_lines_and_bound_size(self):
        content = "".join(f"line {number}\n" for number in range(200))
        chunks = chunk_files({"test.py": {"content": content}}, max_chars=100, overlap_lines=2)
        covered = set()
        for chunk in chunks:
            self.assertLessEqual(len(chunk["text"]), 100)
            self.assertEqual(chunk["text"], "".join(content.splitlines(keepends=True)[chunk["start_line"] - 1:chunk["end_line"]]))
            covered.update(range(chunk["start_line"], chunk["end_line"] + 1))
        self.assertEqual(covered, set(range(1, 201)))

    def test_mismatched_snapshot_and_chunks_rejected(self):
        bundle = make_bundle()
        bundle["snapshot"]["commit"] = "b" * 40
        with self.assertRaises(ValueError):
            Repository(bundle)
        bundle = make_bundle()
        bundle["chunks"][0]["text"] = "invented content"
        with self.assertRaises(ValueError):
            Repository(bundle)

    def test_archive_filters_and_never_extracts(self):
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as archive:
            archive.writestr("repo/src/app.py", "print('hello')\n")
            archive.writestr("repo/.env", "SECRET=not-for-indexing")
            archive.writestr("repo/node_modules/a.js", "generated")
            archive.writestr("repo/binary.txt", b"\x00\xff")
        files = read_archive(buffer.getvalue())
        self.assertIn("content", files["src/app.py"])
        for path in (".env", "node_modules/a.js", "binary.txt"):
            self.assertNotIn("content", files[path])

    def test_archive_traversal_rejected(self):
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as archive:
            archive.writestr("repo/../outside.py", "bad")
        with self.assertRaises(ValueError):
            read_archive(buffer.getvalue())

    def test_api_is_fixed_to_snapshot_and_ai_fails_closed(self):
        repository = Repository(make_bundle())
        app.state.repository = repository
        client = TestClient(app)
        params = {"snapshot_id": repository.id}
        root = client.get("/api/demo/contents", params=params).json()
        self.assertEqual(root[0]["path"], "src")
        response = client.get("/api/demo/contents", params={**params, "path": "src/example.py"})
        self.assertIn("def hello", response.json()["content"])
        self.assertEqual(client.get("/api/demo/contents", params={**params, "path": "../config.py"}).status_code, 404)
        self.assertEqual(client.get("/api/demo/contents", params={**params, "path": "image.png"}).status_code, 415)
        self.assertEqual(client.get("/api/demo/contents", params={"snapshot_id": "old"}).status_code, 409)
        self.assertEqual(client.post("/api/demo/ask", json={**params, "question": "Explain hello"}).status_code, 503)
        self.assertEqual(client.post("/api/demo/ask", json={**params, "question": "hi", "repository": "other/repo"}).status_code, 422)
        self.assertEqual(client.post("/api/demo/ask", content=b"x" * 9000).status_code, 413)


if __name__ == "__main__":
    unittest.main()
