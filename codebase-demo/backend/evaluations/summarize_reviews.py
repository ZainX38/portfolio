"""Count authored manual judgments; never assign semantic grades automatically."""
import json
from collections import Counter
from pathlib import Path

root = Path(__file__).parent / "improvements"
review = json.loads((root / "manual-review.json").read_text(encoding="utf-8"))
summary = {}
previous = None
for stage in sorted(key for key in review if key != "rubric"):
    rows = [json.loads(line) for line in (root / stage / "results.jsonl").read_text(encoding="utf-8").splitlines()]
    summary[stage] = {}
    for model, cases in review[stage].items():
        recorded = {str(row["id"]) for row in rows if row["model"] == model}
        assert set(cases) <= recorded, (stage, model)
        assert all(grade in "CUPIAE" and note for grade, note in cases.values())
        counts = Counter(value[0] for value in cases.values())
        stats = {"recorded": len(recorded), "reviewed": len(cases),
                 "strict_successes": counts["C"], "grades": dict(sorted(counts.items())),
                 "unreviewed_ids": sorted(recorded - set(cases), key=int)}
        if previous:
            before = review[previous].get(model, {})
            stats["changes_from_previous_stage"] = {
                case: {"before": before[case][0], "after": grade[0]}
                for case, grade in cases.items()
                if case in before and grade[0] != before[case][0]
            }
        summary[stage][model] = stats
    previous = stage
(root / "review-summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
print(json.dumps(summary, indent=2))
