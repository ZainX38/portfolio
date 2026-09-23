"""Offline integrity checks and descriptive statistics, not a quality judge."""
import hashlib
import json
import re
import statistics
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config
from repository import Repository

out = Path(__file__).parent
meta = json.loads((out / "deepseek-metadata.json").read_text())
repo = Repository.load(config.BUNDLE_PATH)
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(config.BUNDLE_PATH) == meta["bundle_sha256"]
assert sha(out.parent / ".env") == meta["env_sha256"]
for name, digest in meta["implementation_sha256"].items():
    assert sha(out.parent / name) == digest, name
rows = [json.loads(line) for line in (out / "deepseek-results.jsonl").read_text(encoding="utf-8").splitlines()]
assert len(rows) == 36
assert len({(r["model"], r["id"]) for r in rows}) == 36
for model in ("deepseek-coder-v2:16b", "qwen3.5:4b"):
    assert {r["id"] for r in rows if r["model"] == model} == set(range(1, 19))
extra = out / "deepseek-continuation-results.jsonl"
diagnostics = [json.loads(line) for line in extra.read_text(encoding="utf-8").splitlines()] if extra.exists() else []
continuation = out / "deepseek-continuation-metadata.json"
if continuation.exists():
    baseline = json.loads(continuation.read_text(encoding="utf-8"))
    assert sha(out / "deepseek-results.jsonl") == baseline["original_results_sha256"]
    assert sha(out / "deepseek-metadata.json") == baseline["original_metadata_sha256"]
counts = {"retrieved_chunks": 0, "excerpts": 0, "references": 0, "evidence_lines": 0}
for r in rows + diagnostics:
    assert r["raw_response"]["model"] == r["model"]
    assert r["http_status"] == 200
    assert r["chat_request"]["options"] == {"num_ctx": 4096, "num_predict": 700, "temperature": 0}
    for key, counter in (("retrieved", "retrieved_chunks"), ("excerpts", "excerpts")):
        for chunk in r[key]:
            lines = repo.files[chunk["path"]]["content"].splitlines(keepends=True)
            assert chunk["text"] == "".join(lines[chunk["start_line"] - 1:chunk["end_line"]])
            counts[counter] += 1
    for ref in r.get("result", {}).get("references", []):
        assert any(all(ref[k] == c[k] for k in ("path", "start_line", "end_line")) for c in r["excerpts"])
        assert f'/blob/{repo.snapshot["commit"]}/' in ref["url"]
        counts["references"] += 1
current = None
for line in (out / "deepseek-source-evidence.txt").read_text(encoding="utf-8").splitlines():
    if line.startswith("FILE "):
        current = repo.files[line[5:]]["content"].splitlines()
    elif match := re.match(r"^(\d+): (.*)$", line):
        assert current[int(match[1])-1] == match[2], line
        counts["evidence_lines"] += 1
stats = {}
for model in sorted({r["model"] for r in rows}):
    group = [r for r in rows if r["model"] == model]
    seconds = [r["seconds"] for r in group]
    stats[model] = {"n": len(group), "errors": sum("error" in r for r in group),
        "legacy_passes": sum(r.get("legacy_heuristic_pass", False) for r in group),
        "mean_seconds": statistics.mean(seconds), "median_seconds": statistics.median(seconds),
        "min_seconds": min(seconds), "max_seconds": max(seconds),
        "length_stops": sum(r["raw_response"].get("done_reason") == "length" for r in group)}
paired = []
for number in range(1, 19):
    a, b = [r for r in rows if r["id"] == number]
    paired.append(a["chat_request"]["messages"] == b["chat_request"]["messages"])
result = {"implementation_and_env_unchanged": True, "snapshot_and_text_checks_passed": counts,
    "original_results_sha256": sha(out / "deepseek-results.jsonl"),
    "identical_paired_prompts": sum(paired), "original_statistics": stats,
    "diagnostic_records": len(diagnostics)}
result["core_oauth_refresh_text_matches"] = [
    {"path": path, "line": number, "text": line}
    for path, file in repo.files.items() if path.startswith("src/requests/")
    for number, line in enumerate(file.get("content", "").splitlines(), 1)
    if re.search(r"oauth|refresh", line, re.IGNORECASE)
]
(out / "deepseek-integrity.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
print(json.dumps(result, indent=2))
