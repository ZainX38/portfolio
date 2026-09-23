"""Live audit: instrument the real pipeline; never fabricate HTTP responses.

Run from backend: uv run --env-file .env python evaluations/run_deepseek.py
Only the outgoing chat model is selected for the authorized comparison. All
other request parameters and production functions remain unchanged.
"""
import hashlib
import json
import math
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config
import llm
import rag
from repository import Repository

OUT = Path(__file__).parent
repo = Repository.load(config.BUNDLE_PATH)
cases = json.loads((OUT / "requests.json").read_text())["cases"]
questions = [c["question"] for c in cases] + [
    "How does _basic_auth_str encode usernames and passwords in src/requests/auth.py?",
    "How does HTTPDigestAuth handle a 401 challenge and resend the request?",
    "How do requests.get, requests.api.request and Session.request work together?",
    "How does Session.prepare_request merge session cookies, headers and authentication with a Request?",
    "In Session.request, how are environment settings merged before the prepared request is sent?",
    "How does Session.send choose an adapter, dispatch response hooks, persist cookies and handle redirects?",
    "When does SessionRedirectMixin.should_strip_auth remove Authorization on redirects? Include scheme and port exceptions.",
    "How does rebuild_method change POST and HEAD requests for 301, 302 and 303 redirects?",
    "How does resolve_redirects handle request bodies, cookies and rewinding for 307 and 308 responses?",
    "How does PreparedRequest.prepare_body choose between JSON, form data and streaming bodies?",
    "How does Response.json determine encoding and handle invalid JSON?",
    "What does Response.raise_for_status do for 3xx, 4xx and 5xx status codes?",
    "How does HTTPAdapter.send convert timeout values and translate urllib3 exceptions?",
    "What is the exact current production traffic and p99 latency of applications using Requests?",
    "Where does Requests implement automatic OAuth2 access-token refresh, and what refresh endpoint does it call?",
]
(OUT / "deepseek-cases.json").write_text(json.dumps({"repository": "psf/requests", "questions": questions}, indent=2))
tags = llm.httpx.get(config.OLLAMA_URL + "/api/tags", trust_env=False).json()
metadata = {"time_utc": datetime.now(timezone.utc).isoformat(), "configured_model": config.ANSWER_MODEL,
    "bundle": str(config.BUNDLE_PATH), "bundle_sha256": hashlib.sha256(config.BUNDLE_PATH.read_bytes()).hexdigest(),
    "commit": repo.snapshot["commit"], "snapshot_id": repo.id, "chunks": len(repo.chunks),
    "files": len(repo.files), "coverage": repo.coverage, "embeddings": repo.embeddings,
    "context_tokens": config.CONTEXT_TOKENS, "output_tokens": config.MAX_OUTPUT_TOKENS,
    "system_prompt": rag.SYSTEM_PROMPT, "tags": tags}
(OUT / "deepseek-metadata.json").write_text(json.dumps(metadata, indent=2))
original_post, original_retrieve, original_context = llm.httpx.post, rag.retrieve, rag.build_context
record = {}
selected_model = None

def traced_post(url, **kwargs):
    if url.endswith("/api/chat"):
        kwargs["json"] = {**kwargs["json"], "model": selected_model}
        record["chat_request"] = kwargs["json"]
    started = time.perf_counter()
    response = original_post(url, **kwargs)
    if url.endswith("/api/chat"):
        record["chat_seconds"] = time.perf_counter() - started
        record["http_status"] = response.status_code
        record["raw_response"] = response.json()
    return response

def traced_retrieve(repository, vector, count=5):
    chunks = original_retrieve(repository, vector, count)
    norm = math.sqrt(sum(v*v for v in vector))
    query = [v/norm for v in vector]
    by_id = {c["id"]: i for i,c in enumerate(repository.chunks)}
    record["retrieved"] = [{**c, "similarity": sum(a*b for a,b in zip(query, repository.vectors[by_id[c["id"]]]))} for c in chunks]
    return chunks

def traced_context(*args, **kwargs):
    excerpts = original_context(*args, **kwargs)
    record["excerpts"] = excerpts
    return excerpts

llm.httpx.post, rag.retrieve, rag.build_context = traced_post, traced_retrieve, traced_context
available = {m["name"] for m in tags["models"]}
with (OUT / "deepseek-results.jsonl").open("w", encoding="utf-8") as output:
    for selected_model in ["deepseek-coder-v2:16b", "qwen3.5:4b"]:
        if selected_model not in available:
            continue
        for number, question in enumerate(questions, 1):
            record = {"model": selected_model, "id": number, "question": question}
            started = time.perf_counter()
            try:
                result = rag.answer_question(repo, question, config.MAX_OUTPUT_TOKENS)
                record["result"] = result
                record["citation_ranges_valid"] = all(
                    r["path"] in repo.files and 1 <= r["start_line"] <= r["end_line"] <= len(repo.files[r["path"]]["content"].splitlines())
                    for r in result["references"])
                if number <= len(cases):
                    case = cases[number-1]
                    paths = {r["path"] for r in result["references"]}
                    record["legacy_heuristic_pass"] = all(w in result["answer"].lower() for w in case["expected"]) and (case["path"] in paths if case["path"] else not paths)
            except Exception as exc:
                record["error"] = f"{type(exc).__name__}: {exc}"
            record["seconds"] = time.perf_counter() - started
            output.write(json.dumps(record, ensure_ascii=False) + "\n")
            output.flush()
            print(f'{selected_model} {number}/{len(questions)} {record["seconds"]:.1f}s {record.get("error", "answered")}', flush=True)
