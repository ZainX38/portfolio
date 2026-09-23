"""Additional live diagnostic cases; preserve the original run and configuration.

Run from backend: uv run --env-file .env python evaluations/continue_deepseek.py
Existing diagnostic records are skipped, including failures (no hidden retries).
"""
import hashlib
import json
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
MODEL = "deepseek-coder-v2:16b"
QUESTIONS = {
    19: "In src/requests/models.py, what status-code conditions inside Response.raise_for_status cause HTTPError? Does a 302 cause it?",
    20: "In src/requests/models.py, how does Response.json use guess_json_utf and RequestsJSONDecodeError?",
    21: "In src/requests/sessions.py, what does should_strip_auth return for a same-host http port 80 to https port 443 redirect, and why?",
}

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    previous = json.loads((OUT / "deepseek-metadata.json").read_text())
    assert sha(config.BUNDLE_PATH) == previous["bundle_sha256"], "Index changed"
    assert sha(OUT.parent / ".env") == previous["env_sha256"], "Configuration changed"
    for name, digest in previous["implementation_sha256"].items():
        assert sha(OUT.parent / name) == digest, f"Implementation changed: {name}"
    assert (config.CONTEXT_TOKENS, config.MAX_OUTPUT_TOKENS) == (previous["context_tokens"], previous["output_tokens"])
    tags_response = llm.httpx.get(config.OLLAMA_URL + "/api/tags", timeout=10, trust_env=False)
    tags_response.raise_for_status()
    tags = tags_response.json()
    for name in (MODEL, config.EMBEDDING_MODEL):
        old = next(m["digest"] for m in previous["tags"]["models"] if m["name"] == name)
        new = next(m["digest"] for m in tags["models"] if m["name"] == name)
        assert old == new, f"Model changed: {name}"
    repo = Repository.load(config.BUNDLE_PATH)
    metadata_path = OUT / "deepseek-continuation-metadata.json"
    if not metadata_path.exists():
        metadata_path.write_text(json.dumps({"time_utc": datetime.now(timezone.utc).isoformat(),
            "model": MODEL, "tags": tags, "original_metadata_sha256": sha(OUT / "deepseek-metadata.json"),
            "bundle_sha256": sha(config.BUNDLE_PATH), "original_results_sha256": sha(OUT / "deepseek-results.jsonl"),
            "implementation_and_env_match_original": True, "questions": QUESTIONS}, indent=2), encoding="utf-8")
    output_path = OUT / "deepseek-continuation-results.jsonl"
    done = {r["id"] for r in map(json.loads, output_path.read_text(encoding="utf-8").splitlines())} if output_path.exists() else set()
    original_post, original_retrieve, original_context = llm.httpx.post, rag.retrieve, rag.build_context
    record = {}

    def post(url, **kwargs):
        if url.endswith("/api/chat"):
            kwargs["json"] = {**kwargs["json"], "model": MODEL}
            record["chat_request"] = kwargs["json"]
        response = original_post(url, **kwargs)
        if url.endswith("/api/chat"):
            record["http_status"] = response.status_code
            record["raw_response"] = response.json()
            assert record["raw_response"].get("model") == MODEL, "Unexpected returned model"
        return response

    def retrieve(*args, **kwargs):
        chunks = original_retrieve(*args, **kwargs)
        record["retrieved"] = chunks
        return chunks

    def context(*args, **kwargs):
        excerpts = original_context(*args, **kwargs)
        record["excerpts"] = excerpts
        return excerpts

    llm.httpx.post, rag.retrieve, rag.build_context = post, retrieve, context
    try:
        with output_path.open("a", encoding="utf-8") as output:
            for number, question in QUESTIONS.items():
                if number in done:
                    continue
                record = {"id": number, "model": MODEL, "question": question,
                    "time_utc": datetime.now(timezone.utc).isoformat()}
                started = time.perf_counter()
                try:
                    record["result"] = rag.answer_question(repo, question, config.MAX_OUTPUT_TOKENS)
                except Exception as exc:
                    record["error"] = f"{type(exc).__name__}: {exc}"
                record["seconds"] = time.perf_counter() - started
                output.write(json.dumps(record, ensure_ascii=False) + "\n")
                output.flush()
                print(json.dumps({k: v for k, v in record.items() if k in ("id", "seconds", "error", "result")}), flush=True)
    finally:
        llm.httpx.post, rag.retrieve, rag.build_context = original_post, original_retrieve, original_context

if __name__ == "__main__":
    main()
