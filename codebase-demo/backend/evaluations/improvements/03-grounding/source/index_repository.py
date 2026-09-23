"""Fetch a fixed public repository snapshot. No repository code is executed."""

import argparse
from datetime import datetime, timezone
import io
import json
import os
from pathlib import Path, PurePosixPath
import stat
import tempfile
from urllib.parse import quote
import zipfile

import httpx

from chunking import chunk_files
from config import (
    BUNDLE_PATH, MAX_ARCHIVE_BYTES, MAX_CHUNKS, MAX_FILE_BYTES,
    MAX_FILES, MAX_SOURCE_BYTES, REPOSITORY, REPOSITORY_COMMIT,
)
from repository import Repository, snapshot_id, validate_path


EXCLUDED_DIRS = {".git", "node_modules", "vendor", "dist", "build", ".next", ".venv", "venv", "__pycache__"}
TEXT_SUFFIXES = {
    ".py", ".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs", ".json", ".md",
    ".mdx", ".txt", ".yaml", ".yml", ".toml", ".css", ".html", ".sh",
    ".ps1", ".sql", ".go", ".rs", ".java", ".rb", ".xml", ".ini", ".cfg", ".rst",
}


def exclusion_reason(path, size, mode):
    file = PurePosixPath(path)
    if stat.S_ISLNK(mode):
        return "Symbolic links are not followed"
    if any(part in EXCLUDED_DIRS for part in file.parts):
        return "Dependency or generated file"
    if file.name.startswith(".env") or file.suffix in {".pem", ".key", ".p12"} or file.name in {"id_rsa", "id_ed25519", "credentials.json"}:
        return "Potential credential file excluded"
    if file.name.endswith((".min.js", ".min.css", ".lock")) or file.name == "package-lock.json":
        return "Generated or lock file"
    if size > MAX_FILE_BYTES:
        return "File exceeds the demo size limit"
    if file.suffix.lower() not in TEXT_SUFFIXES and file.name not in {"LICENSE", "Dockerfile", "Makefile", ".gitignore"}:
        return "Unsupported file format"
    return None


def read_archive(archive_bytes):
    files = {}
    total_bytes = 0
    with zipfile.ZipFile(io.BytesIO(archive_bytes)) as archive:
        entries = [entry for entry in archive.infolist() if not entry.is_dir()]
        if len(entries) > MAX_FILES:
            raise ValueError("Repository exceeds the file-count limit")
        for entry in sorted(entries, key=lambda item: item.filename):
            # Read bytes directly from the archive; never extract paths to disk.
            path = entry.filename.split("/", 1)[1]
            validate_path(path)
            if path in files:
                raise ValueError("Duplicate archive path")
            reason = exclusion_reason(path, entry.file_size, entry.external_attr >> 16)
            if reason:
                files[path] = {"reason": reason}
                continue
            total_bytes += entry.file_size
            if total_bytes > MAX_SOURCE_BYTES:
                raise ValueError("Repository exceeds the source-size limit")
            content_bytes = archive.read(entry)
            try:
                content = content_bytes.decode("utf-8")
                if "\x00" in content:
                    raise UnicodeError()
            except UnicodeError:
                files[path] = {"reason": "Not a UTF-8 text file"}
                continue
            files[path] = {"content": content}
    return files


def fetch_snapshot():
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "codebase-portfolio-demo"}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    with httpx.Client(headers=headers, timeout=60) as client:
        response = client.get(f"https://api.github.com/repos/{REPOSITORY}")
        response.raise_for_status()
        metadata = response.json()
        if metadata.get("private"):
            raise ValueError("Only a public repository can be indexed")
        branch = metadata["default_branch"]
        response = client.get(f"https://api.github.com/repos/{REPOSITORY}/commits/{quote(REPOSITORY_COMMIT or branch, safe='')}")
        response.raise_for_status()
        commit = response.json()["sha"]

    # A pinned archive avoids a GitHub API request for every source file.
    # Never forward the optional API token to the archive host.
    archive = bytearray()
    with httpx.stream("GET", f"https://codeload.github.com/{REPOSITORY}/zip/{commit}", timeout=120) as response:
        response.raise_for_status()
        for block in response.iter_bytes():
            archive.extend(block)
            if len(archive) > MAX_ARCHIVE_BYTES:
                raise ValueError("Repository archive exceeds the download limit")
    return {
        "repository": REPOSITORY,
        "branch": branch,
        "commit": commit,
        "files": read_archive(archive),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=BUNDLE_PATH)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Output already exists. Choose a new --output to preserve the previous snapshot.")
    snapshot = fetch_snapshot()
    chunks = chunk_files(snapshot["files"])
    if not chunks or len(chunks) > MAX_CHUNKS:
        raise ValueError("Empty index or chunk-count limit exceeded")
    bundle = {
        "version": 1,
        "snapshot_id": snapshot_id(snapshot),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "snapshot": snapshot,
        "chunking": {"version": 1, "max_chars": 3000, "overlap_lines": 5},
        "chunks": chunks,
        "embeddings": None,
    }
    Repository(bundle)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    # Publish only a fully written and validated bundle, never half an index.
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=args.output.parent, suffix=".tmp", delete=False) as temporary:
        json.dump(bundle, temporary, ensure_ascii=False)
        temporary_path = Path(temporary.name)
    temporary_path.replace(args.output)
    available = sum("content" in file for file in snapshot["files"].values())
    print(f"Saved {snapshot['repository']} at {snapshot['commit']}")
    print(f"{available} text files, {len(snapshot['files']) - available} excluded files, {len(chunks)} chunks")
    print(f"Bundle: {args.output.resolve()}")
    print("Snapshot saved. Run embed_repository.py to create a fresh index.")


if __name__ == "__main__":
    main()
