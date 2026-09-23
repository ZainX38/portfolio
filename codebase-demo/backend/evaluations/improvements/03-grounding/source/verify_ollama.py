"""Explicit live smoke test using real snapshot excerpts; not a production index."""

import json
import argparse
from pathlib import Path

from config import BUNDLE_PATH, EMBEDDING_MODEL
from llm import embed, model_digest
from rag import answer_question
from repository import Repository
from evaluate_rag import DEFAULT_CASES, load_cases


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", type=Path, default=BUNDLE_PATH)
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES)
    args = parser.parse_args()
    bundle = json.loads(args.bundle.read_text(encoding="utf-8"))
    case = next(case for case in load_cases(args.cases, Repository(bundle)) if case["path"])
    bundle["chunks"] = [chunk for chunk in bundle["chunks"] if chunk["path"] == case["path"]]
    bundle.pop("coverage", None)
    if not bundle["chunks"]:
        raise ValueError("The smoke-test source file is missing from this snapshot")
    digest = model_digest(EMBEDDING_MODEL)
    vectors = embed([f"{chunk['path']}\n{chunk['text']}" for chunk in bundle["chunks"]])
    bundle["embeddings"] = {
        "model": EMBEDDING_MODEL, "digest": digest, "snapshot_id": bundle["snapshot_id"],
        "dimensions": len(vectors[0]), "chunk_ids": [chunk["id"] for chunk in bundle["chunks"]], "vectors": vectors,
    }
    repository = Repository(bundle)
    question = case["question"]
    result = answer_question(repository, question, 500)
    print(json.dumps(result, indent=2), flush=True)
    if not result["references"] or not all(word in result["answer"].lower() for word in case["expected"]):
        raise ValueError("Live answer did not cite the known source")
    print("Live smoke test passed; full-repository indexing is a separate step.", flush=True)


if __name__ == "__main__":
    main()
