"""Inspect named implementation sizes without model calls or index changes."""
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config
from repository import Repository
from symbol_retrieval import ranked_symbols

root = Path(__file__).parent
repo = Repository.load(config.BUNDLE_PATH)
questions = json.loads((root / "deepseek-cases.json").read_text())["questions"]
result = []
for number, question in enumerate(questions, 1):
    matches = []
    for score, symbol in ranked_symbols(repo, question)[:4]:
        lines = repo.files[symbol["path"]]["content"].splitlines(keepends=True)
        matches.append({"name": f'{symbol["owner"]}.{symbol["name"]}', "path": symbol["path"],
            "score": score, "start": symbol["start"], "body_start": symbol["body_start"], "end": symbol["end"],
            "body_bytes": len("".join(lines[symbol["body_start"]-1:symbol["end"]]).encode()),
            "whole_bytes": len("".join(lines[symbol["start"]-1:symbol["end"]]).encode())})
    result.append({"id": number, "matches": matches})
(root / "improvements/symbol-diagnostics.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
print(json.dumps(result, indent=2))
