"""Frozen-case live comparison; each stage has immutable inputs and append-only results."""
import argparse
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

ROOT = Path(__file__).parent
MODELS = ["deepseek-coder-v2:16b", "qwen3.5:4b"]
sha = lambda data: hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=["01-retrieval", "02-context", "03-grounding"])
    args = parser.parse_args()
    out = ROOT / "improvements" / args.stage
    out.mkdir(parents=True, exist_ok=True)
    baseline = json.loads((ROOT / "deepseek-metadata.json").read_text())
    questions = json.loads((ROOT / "deepseek-cases.json").read_text())["questions"]
    assert sha(config.BUNDLE_PATH.read_bytes()) == baseline["bundle_sha256"]
    assert sha((ROOT.parent / ".env").read_bytes()) == baseline["env_sha256"]
    assert (config.CONTEXT_TOKENS, config.MAX_OUTPUT_TOKENS) == (4096, 700)
    response = llm.httpx.get(config.OLLAMA_URL + "/api/tags", timeout=10, trust_env=False)
    response.raise_for_status()
    tags = response.json()
    for model in MODELS + [config.EMBEDDING_MODEL]:
        assert next(m["digest"] for m in tags["models"] if m["name"] == model) == next(m["digest"] for m in baseline["tags"]["models"] if m["name"] == model)
    sources = {p.name: p.read_text(encoding="utf-8") for p in ROOT.parent.glob("*.py")}
    hashes = {name: sha(text.encode()) for name, text in sources.items()}
    metadata = {"stage": args.stage, "time_utc": datetime.now(timezone.utc).isoformat(),
        "questions": questions, "models": MODELS, "tags": tags, "source_sha256": hashes,
        "bundle_sha256": baseline["bundle_sha256"], "env_sha256": baseline["env_sha256"],
        "system_prompt": rag.SYSTEM_PROMPT, "context_tokens": 4096, "output_tokens": 700}
    metadata_path = out / "metadata.json"
    if metadata_path.exists():
        previous = json.loads(metadata_path.read_text(encoding="utf-8"))
        assert previous["source_sha256"] == hashes, "Stage implementation changed; do not mix runs"
        assert previous["questions"] == questions
    else:
        metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
        (out / "source").mkdir(exist_ok=True)
        for name, text in sources.items():
            (out / "source" / name).write_text(text, encoding="utf-8")
    path = out / "results.jsonl"
    done = {(r["model"], r["id"]) for r in map(json.loads, path.read_text(encoding="utf-8").splitlines())} if path.exists() else set()
    repo = Repository.load(config.BUNDLE_PATH)
    original_post, original_retrieve, original_context = llm.httpx.post, rag.retrieve, rag.build_context
    record = {}
    selected = ""

    def post(url, **kwargs):
        if url.endswith("/api/chat"):
            kwargs["json"] = {**kwargs["json"], "model": selected}
            record["chat_request"] = kwargs["json"]
        start = time.perf_counter()
        response = original_post(url, **kwargs)
        if url.endswith("/api/chat"):
            record["chat_seconds"] = time.perf_counter() - start
            record["http_status"] = response.status_code
            record["raw_response"] = response.json()
            assert record["raw_response"].get("model") == selected
        return response

    def retrieve(*args, **kwargs):
        chunks = original_retrieve(*args, **kwargs)
        record["retrieved"] = chunks
        return chunks

    def context(*args, **kwargs):
        excerpts = original_context(*args, **kwargs)
        record["excerpts"] = excerpts
        for chunk in excerpts:
            lines = repo.files[chunk["path"]]["content"].splitlines(keepends=True)
            assert chunk["text"] == "".join(lines[chunk["start_line"]-1:chunk["end_line"]])
        return excerpts

    llm.httpx.post, rag.retrieve, rag.build_context = post, retrieve, context
    try:
        with path.open("a", encoding="utf-8") as output:
            for selected in MODELS:
                for number, question in enumerate(questions, 1):
                    if (selected, number) in done:
                        continue
                    record = {"model": selected, "id": number, "question": question,
                        "time_utc": datetime.now(timezone.utc).isoformat()}
                    start = time.perf_counter()
                    try:
                        record["result"] = rag.answer_question(repo, question, config.MAX_OUTPUT_TOKENS)
                    except Exception as exc:
                        record["error"] = f"{type(exc).__name__}: {exc}"
                    record["seconds"] = time.perf_counter() - start
                    output.write(json.dumps(record, ensure_ascii=False) + "\n")
                    output.flush()
                    print(json.dumps({k: v for k, v in record.items() if k in ("model", "id", "seconds", "error", "result")}), flush=True)
    finally:
        llm.httpx.post, rag.retrieve, rag.build_context = original_post, original_retrieve, original_context


if __name__ == "__main__":
    main()
