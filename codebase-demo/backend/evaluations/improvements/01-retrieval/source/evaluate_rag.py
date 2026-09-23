"""Run repository-specific evaluation fixtures against a completed index."""

import argparse
import json
from pathlib import Path

from config import PRESET_DIR
from rag import answer_question
from repository import Repository


DEFAULT_CASES = Path(__file__).parent / "evaluations" / "requests.json"


def load_cases(path, repository):
    fixture = json.loads(path.read_text(encoding="utf-8"))
    if fixture["repository"].lower() != repository.snapshot["repository"].lower():
        raise ValueError("Evaluation fixture belongs to another repository; supply --cases")
    for case in fixture["cases"]:
        if case["path"] and case["path"] not in repository.files:
            raise ValueError(f"Evaluation source is missing: {case['path']}")
    return fixture["cases"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", type=Path, default=PRESET_DIR / "bundle-indexed.json")
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES)
    args = parser.parse_args()
    repository = Repository.load(args.bundle)
    if not repository.embeddings or not repository.coverage:
        raise ValueError("Evaluation requires a completed index with coverage metadata")
    failures = 0
    for case in load_cases(args.cases, repository):
        result = answer_question(repository, case["question"], 500)
        cited_paths = {reference["path"] for reference in result["references"]}
        passed = all(word in result["answer"].lower() for word in case["expected"])
        passed = passed and (case["path"] in cited_paths if case["path"] else not cited_paths)
        failures += not passed
        print(json.dumps({"question": case["question"], "passed": passed, **result}, indent=2), flush=True)
    if failures:
        raise SystemExit(f"{failures} evaluation cases failed; inspect retrieval and answers before release")
    print("RAG evaluation passed. Also manually review answer meaning and citations.")


if __name__ == "__main__":
    main()
