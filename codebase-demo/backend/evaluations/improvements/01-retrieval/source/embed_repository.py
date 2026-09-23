"""Embed an existing snapshot with resumable local caching; never re-fetch GitHub."""

import argparse
from contextlib import closing
import hashlib
import json
from pathlib import Path
import sqlite3
import tempfile
import time

from config import BUNDLE_PATH, PRESET_DIR, EMBEDDING_MODEL
from chunking import chunk_files
from coverage import select_chunks
from llm import embed, model_digest
from repository import Repository


def cache_key(snapshot, digest, text):
    # No reuse across repositories or commits, including legacy cache entries.
    return hashlib.sha256(json.dumps([snapshot, digest, text]).encode()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=BUNDLE_PATH)
    parser.add_argument("--output", type=Path, default=PRESET_DIR / "bundle-indexed.json")
    parser.add_argument("--cache", type=Path, default=PRESET_DIR / "embedding-cache.sqlite")
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--scope", choices=["selected", "all"], default="all")
    parser.add_argument("--include", action="append", default=[], help="Path glob for selected scope; repeat to include more paths")
    args = parser.parse_args()
    if args.output.exists() or args.input.resolve() == args.output.resolve():
        parser.error("Choose a new output path; existing bundles are never overwritten.")
    if not 1 <= args.batch_size <= 32:
        parser.error("Batch size must be between 1 and 32")
    bundle = json.loads(args.input.read_text(encoding="utf-8"))
    repository = Repository(bundle)
    # Rebuild chunks from saved source so extending a partial index never
    # resolves a newer branch or loses previously unindexed files.
    if args.include and args.scope != "selected":
        parser.error("--include requires --scope selected")
    chunks, coverage = select_chunks(repository.files, chunk_files(repository.files), args.scope, args.include)
    if not chunks:
        parser.error("No chunks selected; adjust the configured index paths")
    bundle["chunks"] = chunks
    bundle["coverage"] = coverage
    bundle["embeddings"] = None
    print(f"Indexing {len(chunks)} chunks from {len(coverage['indexed_paths'])} files ({args.scope} scope)", flush=True)
    digest = model_digest(EMBEDDING_MODEL)
    args.cache.parent.mkdir(parents=True, exist_ok=True)
    vectors = []
    started = time.monotonic()
    with closing(sqlite3.connect(args.cache)) as cache:
        cache.execute("CREATE TABLE IF NOT EXISTS embeddings (key TEXT PRIMARY KEY, vector TEXT NOT NULL)")
        for start in range(0, len(chunks), args.batch_size):
            batch = chunks[start:start + args.batch_size]
            texts = [f"{chunk['path']}\n{chunk['text']}" for chunk in batch]
            keys = [cache_key(repository.id, digest, text) for text in texts]
            saved = [cache.execute("SELECT vector FROM embeddings WHERE key = ?", (key,)).fetchone() for key in keys]
            missing = [index for index, row in enumerate(saved) if row is None]
            if missing:
                new_vectors = embed([texts[index] for index in missing], keep_alive="5m")
                for index, vector in zip(missing, new_vectors):
                    encoded = json.dumps(vector)
                    cache.execute("INSERT OR REPLACE INTO embeddings VALUES (?, ?)", (keys[index], encoded))
                    saved[index] = (encoded,)
                cache.commit()
            vectors.extend(json.loads(row[0]) for row in saved)
            print(f"Embedded {len(vectors)}/{len(chunks)} chunks ({time.monotonic() - started:.0f}s)", flush=True)
    if model_digest(EMBEDDING_MODEL) != digest:
        raise ValueError("Embedding model changed during indexing; rerun with a stable model")
    bundle["embeddings"] = {
        "model": EMBEDDING_MODEL, "digest": digest,
        "snapshot_id": repository.id, "dimensions": len(vectors[0]),
        "chunk_ids": [chunk["id"] for chunk in chunks], "vectors": vectors,
    }
    Repository(bundle)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=args.output.parent, suffix=".tmp", delete=False) as temporary:
        json.dump(bundle, temporary, ensure_ascii=False)
        temporary_path = Path(temporary.name)
    temporary_path.replace(args.output)
    print(f"Saved indexed bundle: {args.output.resolve()}", flush=True)


if __name__ == "__main__":
    main()
