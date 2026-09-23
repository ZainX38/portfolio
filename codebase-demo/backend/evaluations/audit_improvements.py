"""Audit saved stage provenance and exact citations; does not judge answer quality."""
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config
from repository import Repository


def main():
    root = Path(__file__).parent / "improvements"
    repo = Repository.load(config.BUNDLE_PATH)
    bundle_hash = hashlib.sha256(config.BUNDLE_PATH.read_bytes()).hexdigest()
    report, stages = {}, {}
    for path in sorted(root.glob("*/results.jsonl")):
        meta = json.loads(path.with_name("metadata.json").read_text(encoding="utf-8"))
        assert meta["bundle_sha256"] == bundle_hash, path
        for name, expected in meta["source_sha256"].items():
            source = (path.parent / "source" / name).read_text(encoding="utf-8")
            assert hashlib.sha256(source.encode()).hexdigest() == expected, (path, name)
        rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
        seen, by_case = set(), {}
        for row in rows:
            key = row["model"], row["id"]
            assert key not in seen, (path, key)
            seen.add(key)
            by_case[key] = row
            assert row["model"] in meta["models"]
            assert 1 <= row["id"] <= len(meta["questions"])
            assert row["question"] == meta["questions"][row["id"] - 1]
            for field in ("retrieved", "excerpts"):
                for span in row.get(field, []):
                    lines = repo.files[span["path"]]["content"].splitlines(keepends=True)
                    assert 1 <= span["start_line"] <= span["end_line"] <= len(lines)
                    assert span["text"] == "".join(lines[span["start_line"]-1:span["end_line"]])
            if "chat_request" in row:
                request = row["chat_request"]
                assert request["model"] == row["model"]
                assert request["messages"][0]["content"] == meta["system_prompt"]
                assert request["options"] == {"num_ctx": meta["context_tokens"],
                                               "num_predict": meta["output_tokens"], "temperature": 0}
            if "raw_response" in row:
                assert row["raw_response"]["model"] == row["model"]
            result = row.get("result")
            if result:
                assert result["snapshot_id"] == repo.id
                assert result["commit"] == repo.snapshot["commit"]
                for ref in result["references"]:
                    assert any(all(ref[k] == span[k] for k in ("path", "start_line", "end_line"))
                               for span in row["excerpts"])
                    assert f'/blob/{repo.snapshot["commit"]}/' in ref["url"]
        expected = {(model, number) for model in meta["models"]
                    for number in range(1, len(meta["questions"]) + 1)}
        report[path.parent.name] = {"records": len(rows), "expected": len(expected),
                                  "complete": seen == expected,
                                  "errors": sum("error" in row for row in rows),
                                  "provenance_and_source_checks": "passed"}
        paired = 0
        for number in range(1, len(meta["questions"]) + 1):
            pair = [by_case.get((model, number)) for model in meta["models"]]
            if all(row and "chat_request" in row for row in pair):
                assert pair[0]["chat_request"]["messages"] == pair[1]["chat_request"]["messages"]
                paired += 1
        report[path.parent.name]["identical_model_prompt_pairs"] = paired
        stages[path.parent.name] = by_case
    if "03-grounding" in stages and "02-context" in stages:
        compared = 0
        for key, row in stages["03-grounding"].items():
            before = stages["02-context"].get(key)
            if before and "chat_request" in before and "chat_request" in row:
                assert before["excerpts"] == row["excerpts"], key
                assert before["chat_request"]["messages"][1:] == row["chat_request"]["messages"][1:], key
                compared += 1
        report["03-grounding"]["unchanged_context_comparisons"] = compared
    (root / "integrity.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
