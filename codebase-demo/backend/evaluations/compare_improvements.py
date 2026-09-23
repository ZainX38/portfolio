"""Describe evidence coverage and timings; never score answer meaning automatically."""
import json
import statistics
from pathlib import Path

root = Path(__file__).parent
targets = json.loads((root / "improvements/source-targets.json").read_text())["cases"]
paths = {"baseline": root / "deepseek-results.jsonl"}
paths.update({p.parent.name: p for p in sorted((root / "improvements").glob("*/results.jsonl"))})
summary = {}
for stage, path in paths.items():
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    summary[stage] = {}
    for model in sorted({r["model"] for r in rows}):
        group = [r for r in rows if r["model"] == model]
        cases = {}
        for row in group:
            expected = {(f"src/requests/{path}", line) for path, first, last in targets.get(str(row["id"]), []) for line in range(first, last + 1)}
            if not expected:
                continue
            coverage = {}
            for field in ("retrieved", "excerpts"):
                actual = {(c["path"], line) for c in row.get(field, []) for line in range(c["start_line"], c["end_line"] + 1)}
                coverage[field] = {"covered": len(expected & actual), "total": len(expected),
                    "missing": [f"{p}:{line}" for p, line in sorted(expected - actual)]}
            cases[str(row["id"])] = coverage
        summary[stage][model] = {"n": len(group), "errors": sum("error" in r for r in group),
            "mean_seconds": statistics.mean(r["seconds"] for r in group),
            "median_seconds": statistics.median(r["seconds"] for r in group),
            "fully_visible_target_cases": {field: sum(c[field]["covered"] == c[field]["total"] for c in cases.values()) for field in ("retrieved", "excerpts")},
            "target_line_coverage": {field: [sum(c[field]["covered"] for c in cases.values()), sum(c[field]["total"] for c in cases.values())] for field in ("retrieved", "excerpts")},
            "cases": cases}
(root / "improvements/coverage.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
print(json.dumps({stage: {model: {k: v for k, v in stats.items() if k != "cases"} for model, stats in models.items()} for stage, models in summary.items()}, indent=2))
