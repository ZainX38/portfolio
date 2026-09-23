import unittest
from types import SimpleNamespace

from chunking import chunk_files
from symbol_retrieval import rank_chunks, ranked_symbols, symbols


def repository(files):
    files = {p: {"content": text} for p, text in files.items()}
    return SimpleNamespace(files=files, chunks=chunk_files(files, max_chars=100))


class SymbolRetrievalTests(unittest.TestCase):
    def test_qualified_symbol_beats_other_class_and_vector_score(self):
        repo = repository({"src/a.py": "class One:\n    def send(self):\n        return 'one'\n",
            "src/b.py": "class Two:\n    def send(self):\n        return 'two'\n"})
        ranked = rank_chunks(repo, "How does Two.send work?", [1.0, 0.0])
        self.assertEqual(repo.chunks[ranked[0]]["path"], "src/b.py")

    def test_related_local_helper_and_docstring_body_offset(self):
        repo = repository({"src/a.py": 'class Client:\n    def request(self):\n        """Prepare a request."""\n        return self.merge_environment_settings()\n    def merge_environment_settings(self):\n        return {}\n'})
        matches = ranked_symbols(repo, "How does Client.request merge environment settings?")
        self.assertEqual([s["name"] for _, s in matches], ["request", "merge_environment_settings"])
        self.assertEqual(matches[0][1]["body_start"], 4)

    def test_no_symbol_keeps_cosine_order_and_bad_python_is_ignored(self):
        repo = repository({"README.md": "Documentation\n", "broken.py": "def syntax error\n"})
        self.assertEqual(symbols(repo), [])
        self.assertEqual(rank_chunks(repo, "production p99 latency?", [0.1, 0.9]), [1, 0])

    def test_does_not_search_unindexed_files(self):
        repo = repository({"src/a.py": "def public():\n    return 1\n"})
        repo.files["private.py"] = {"content": "def private():\n    return 2\n"}
        self.assertEqual(ranked_symbols(repo, "How does private work?"), [])
