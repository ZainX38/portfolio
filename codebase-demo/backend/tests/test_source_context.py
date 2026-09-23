import unittest

from rag import SYSTEM_PROMPT, build_context
from source_context import header, implementation_context
from test_symbol_retrieval import repository


class SourceContextTests(unittest.TestCase):
    def test_long_docstring_does_not_hide_complete_implementation(self):
        text = 'class Client:\n    def send(self):\n        """' + ('long documentation ' * 120) + '"""\n        adapter = self.get_adapter()\n        return adapter.send()\n'
        repo = repository({"src/client.py": text})
        spans = implementation_context(repo, repo.chunks, "How does Client.send work?", 500)
        self.assertEqual(len(spans), 1)
        self.assertEqual(spans[0]["scope"], "complete body")
        self.assertIn("return adapter.send()", spans[0]["text"])
        self.assertEqual(spans[0]["start_line"], 4)

    def test_oversized_body_is_bounded_and_explicitly_partial(self):
        text = "def choose_body():\n" + "    unrelated = 1\n" * 100 + "    if json:\n        body = encode(json)\n    return body\n"
        repo = repository({"src/body.py": text})
        spans = implementation_context(repo, repo.chunks, "How does choose_body encode JSON?", 350)
        self.assertIn("partial body", spans[0]["scope"])
        self.assertIn("encode(json)", spans[0]["text"])
        self.assertLessEqual(sum(len((header(s) + s["text"] + "\n\n").encode()) for s in spans), 350)
        for span in spans:
            self.assertEqual(span["text"], "".join(text.splitlines(keepends=True)[span["start_line"]-1:span["end_line"]]))

    def test_expansion_does_not_include_unindexed_lines(self):
        repo = repository({"src/a.py": "def choose_body():\n    return '" + "x" * 200 + "'\n"})
        spans = implementation_context(repo, repo.chunks, "How does choose_body work?", 2000)
        self.assertEqual(spans, [])

    def test_context_budget_and_helper_are_preserved(self):
        repo = repository({"src/a.py": "class Client:\n    def send(self):\n        return self.choose_adapter()\n    def choose_adapter(self):\n        return 'https'\n"})
        question = "How does Client.send choose an adapter?"
        spans = build_context(repo.chunks, question, 700, repository=repo)
        self.assertEqual(len(spans), 2)
        from config import CONTEXT_TOKENS
        total = sum(len((header(s) + s["text"] + "\n\n").encode()) for s in spans)
        self.assertLessEqual(total + max(600, len(SYSTEM_PROMPT.encode())) + len(question.encode()) + 700 + 512, CONTEXT_TOKENS)
