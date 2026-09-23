"""Offline source-span inspection using stage 1's actual retrieved chunks."""
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config
from rag import build_context
from repository import Repository
from source_context import header

root = Path(__file__).parent
repo = Repository.load(config.BUNDLE_PATH)
rows = [json.loads(line) for line in (root / "improvements/01-retrieval/results.jsonl").read_text(encoding="utf-8").splitlines()]
preview = []
for row in rows[:18]:
    spans = build_context(row["retrieved"], row["question"], config.MAX_OUTPUT_TOKENS, repository=repo)
    preview.append({"id": row["id"], "excerpts": spans})
    print(row["id"], [(s["path"], s["start_line"], s["end_line"], s.get("scope")) for s in spans], sum(len((header(s) + s["text"] + "\n\n").encode()) for s in spans))
(root / "improvements/context-preview.json").write_text(json.dumps(preview, indent=2), encoding="utf-8")
