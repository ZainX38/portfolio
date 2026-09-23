import hashlib
import json
import re
import math
from array import array
from pathlib import PurePosixPath

from config import REPOSITORY, REPOSITORY_COMMIT


def snapshot_id(snapshot):
    encoded = json.dumps(snapshot, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def validate_path(path):
    if not path or "\\" in path or path.startswith("/"):
        raise ValueError("Invalid repository path")
    if any(part in ("", ".", "..") for part in path.split("/")):
        raise ValueError("Invalid repository path")


class Repository:
    def __init__(self, bundle):
        if bundle.get("version") != 1:
            raise ValueError("Unsupported bundle version")
        self.snapshot = bundle["snapshot"]
        self.id = snapshot_id(self.snapshot)
        if self.snapshot["repository"].lower() != REPOSITORY:
            raise ValueError("Bundle belongs to a different repository. Create a new snapshot and index for DEMO_REPOSITORY.")
        if REPOSITORY_COMMIT and self.snapshot["commit"] != REPOSITORY_COMMIT:
            raise ValueError("Bundle belongs to a different commit. Create a new snapshot and index for DEMO_REPOSITORY_COMMIT.")
        if bundle["snapshot_id"] != self.id:
            raise ValueError("Snapshot checksum mismatch; rebuild the snapshot and index")
        if not re.fullmatch(r"[0-9a-f]{40}", self.snapshot["commit"]):
            raise ValueError("Invalid commit SHA")
        self.files = self.snapshot["files"]
        self.directories = {"": {}}
        for path, file in self.files.items():
            validate_path(path)
            parts = path.split("/")
            for index, name in enumerate(parts):
                parent = "/".join(parts[:index])
                entry_path = "/".join(parts[:index + 1])
                is_file = index == len(parts) - 1
                entry = {"name": name, "path": entry_path, "type": "file" if is_file else "dir"}
                if is_file:
                    entry["unavailable"] = file.get("reason")
                self.directories.setdefault(parent, {})[name] = entry
        self.chunks = bundle["chunks"]
        for chunk in self.chunks:
            file = self.files.get(chunk["path"], {})
            lines = file.get("content", "").splitlines(keepends=True)
            start, end = chunk["start_line"], chunk["end_line"]
            if not 1 <= start <= end <= len(lines):
                raise ValueError("Chunk line range is outside the snapshot")
            if chunk["text"] != "".join(lines[start - 1:end]):
                raise ValueError("Chunk content does not match snapshot")
        ids = [chunk["id"] for chunk in self.chunks]
        if len(set(ids)) != len(ids):
            raise ValueError("Duplicate chunk IDs")
        self.coverage = bundle.get("coverage")
        self.indexed_paths = set(self.coverage["indexed_paths"]) if self.coverage else set()
        if self.coverage:
            indexed = self.indexed_paths
            excluded = set(self.coverage["excluded"])
            chunk_paths = {chunk["path"] for chunk in self.chunks}
            if indexed != chunk_paths or indexed & excluded or indexed | excluded != self.files.keys():
                raise ValueError("Index coverage does not match the snapshot")
        self.embeddings = bundle.get("embeddings")
        self.vectors = []
        if self.embeddings is not None:
            index = self.embeddings
            if index["snapshot_id"] != self.id or index["chunk_ids"] != ids or len(index["vectors"]) != len(ids):
                raise ValueError("Embeddings do not match the snapshot chunks")
            for vector in index["vectors"]:
                if len(vector) != index["dimensions"] or not vector or not all(math.isfinite(value) for value in vector):
                    raise ValueError("Invalid embedding dimensions or values")
                norm = math.sqrt(sum(value * value for value in vector))
                if norm == 0:
                    raise ValueError("Zero embedding vector")
                # Compact normalized arrays avoid a vector database and reduce RAM.
                self.vectors.append(array("f", (value / norm for value in vector)))
            self.embeddings = {key: value for key, value in index.items() if key != "vectors"}

    @classmethod
    def load(cls, path):
        if not path.is_file():
            raise ValueError(f"No bundle at {path}. Create a snapshot and new index for the configured repository/commit, then set DEMO_BUNDLE_PATH.")
        return cls(json.loads(path.read_text(encoding="utf-8")))

    def contents(self, path):
        if path in self.directories:
            entries = [{**entry, "indexed": bool(self.embeddings and entry["path"] in self.indexed_paths)} for entry in self.directories[path].values()]
            return sorted(entries, key=lambda entry: (entry["type"] != "dir", entry["name"].lower()))
        file = self.files[path]
        if "content" not in file:
            raise ValueError(file["reason"])
        return {
            "name": PurePosixPath(path).name, "path": path, "content": file["content"],
            "indexed": bool(self.embeddings and path in self.indexed_paths),
            "index_note": self.coverage["excluded"].get(path, "Indexed source; answers use retrieved excerpts only") if self.coverage else "AI index is not ready",
        }
