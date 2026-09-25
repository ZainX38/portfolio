from contextlib import closing, redirect_stdout
import io
import hashlib
import json
from pathlib import Path
import tempfile
import sqlite3
import unittest
from unittest.mock import patch

from chunking import chunk_files
from config import PROVIDER
from embed_repository import main
from repository import Repository, snapshot_id
from test_snapshot import make_bundle


class IndexingTests(unittest.TestCase):
    def test_expanding_scope_reuses_unchanged_embeddings(self):
        bundle = make_bundle()
        bundle["snapshot"]["files"]["docs/extra.md"] = {"content": "Additional documentation\n"}
        bundle["snapshot_id"] = snapshot_id(bundle["snapshot"])
        bundle["chunks"] = chunk_files(bundle["snapshot"]["files"])
        with tempfile.TemporaryDirectory() as folder:
            directory = Path(folder)
            source, core, expanded, cache = [directory / name for name in ("source.json", "core.json", "expanded.json", "cache.sqlite")]
            source.write_text(json.dumps(bundle), encoding="utf-8")
            def run_index(input_path, output_path, scope):
                argv = ["embed_repository.py", "--input", str(input_path), "--output", str(output_path), "--cache", str(cache), "--scope", scope]
                if scope == "selected":
                    argv.extend(["--include", "src/*"])
                with patch("sys.argv", argv), patch("embed_repository.provider_configured", return_value=True), patch("embed_repository.model_digest", return_value="test-digest"), patch("embed_repository.embed", side_effect=lambda texts, **kwargs: [[1, 0] for _ in texts]) as model, redirect_stdout(io.StringIO()):
                    main()
                return model
            initial_model = run_index(source, core, "selected")
            self.assertEqual(len(initial_model.call_args.args[0]), 1)
            expanded_model = run_index(core, expanded, "all")
            self.assertEqual(len(expanded_model.call_args.args[0]), 1)
            self.assertIn("docs/extra.md", expanded_model.call_args.args[0][0])
            self.assertEqual(Repository.load(core).id, Repository.load(expanded).id)
            self.assertEqual(len(Repository.load(expanded).indexed_paths), 2)

    def test_cache_never_reuses_vectors_across_snapshots(self):
        bundle = make_bundle()
        with tempfile.TemporaryDirectory() as folder:
            directory = Path(folder)
            source, cache = directory / "source.json", directory / "cache.sqlite"
            chunk = bundle["chunks"][0]
            legacy_key = hashlib.sha256(f"test-digest\n{chunk['path']}\n{chunk['text']}".encode()).hexdigest()
            with closing(sqlite3.connect(cache)) as database:
                database.execute("CREATE TABLE embeddings (key TEXT PRIMARY KEY, vector TEXT NOT NULL)")
                database.execute("INSERT INTO embeddings VALUES (?, ?)", (legacy_key, "[0, 1]"))
                database.commit()
            initial_repository = bundle["snapshot"]["repository"]
            # Identical path/text in a new commit or repository must hit the model.
            # Repeating the exact snapshot may resume from its own saved vectors.
            cases = [(initial_repository, "a", 1), (initial_repository, "a", 0), (initial_repository, "b", 1), ("other/project", "b", 1)]
            for index, (name, commit, calls) in enumerate(cases):
                bundle["snapshot"].update(repository=name, commit=commit * 40)
                bundle["snapshot_id"] = snapshot_id(bundle["snapshot"])
                source.write_text(json.dumps(bundle), encoding="utf-8")
                output = directory / f"indexed-{index}.json"
                argv = ["embed_repository.py", "--input", str(source), "--output", str(output), "--cache", str(cache)]
                with patch("sys.argv", argv), patch("repository.REPOSITORY", name), patch("embed_repository.provider_configured", return_value=True), patch("embed_repository.model_digest", return_value="test-digest"), patch("embed_repository.embed", return_value=[[1, 0]]) as model, redirect_stdout(io.StringIO()):
                    main()
                    self.assertEqual(model.call_count, calls)
                    indexed = Repository.load(output)
                    self.assertEqual(list(indexed.vectors[0]), [1, 0])
                    self.assertEqual(indexed.embeddings["provider"], PROVIDER)
