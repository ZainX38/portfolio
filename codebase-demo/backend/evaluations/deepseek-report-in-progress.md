# Requests RAG: DeepSeek evaluation

Evaluation in progress. This file is not a completed quality assessment yet.

## Scope and method

18 questions include the three existing `requests.json` fixtures, individual methods, cross-file request flow, authentication, session merging, redirects, serialization, error handling, and three questions whose requested facts are not established by the index. Both installed models are called through real Ollama HTTP requests. No synthetic answers or external LLM judge are used. Source review uses the exact source stored in the indexed snapshot, not a newer checkout.

`run_deepseek.py` calls the existing `rag.answer_question`, instruments retrieval and context construction, and wraps the real HTTP POST to select the comparison model and retain raw responses. It does not modify configuration files or production modules. Every query is embedded by the configured real embedding model; no reindexing takes place. The outgoing chat model is the only experimental variable. The production output cap (700) is used for both models; the old standalone evaluator instead hardcodes 500.

`deepseek-results.jsonl` records full retrieved chunks and cosine scores, final excerpts, exact chat requests, raw Ollama responses, postprocessed answers/errors, and wall-clock latency. `deepseek-metadata.json` records model digests, index identity, coverage, settings and implementation hashes. `deepseek-source-evidence.txt` contains line-numbered primary implementation excerpts inspected during review. Citation validity refers to the pinned snapshot's paths, ranges and exact text, not merely accepted citation IDs. Remote GitHub availability is not tested.

## Configuration findings

DeepSeek is installed as `deepseek-coder-v2:16b` (15.7B, Q4_0), but the checked `.env` and `config.py` default both select `qwen3.5:4b`. Installation alone has not switched this workspace's configured answer model. No running Python/uvicorn process was found in the process inspection; an independently launched/deployed backend's effective environment is unverified. The evaluation explicitly selects DeepSeek and checks the returned model identity.

The existing bundle is Requests commit `611c6162cbc4ac2020a2f91c7cfa4f3abf9bbb60`, snapshot `2418794218e1223cdbc1a8a33882c345ea06d67f2fae5f8097211557c4822471`: 288 chunks from 96 indexed files out of 130 snapshot files, scope `all`. “All” means all eligible chunks, not every file. Embeddings use `qwen3-embedding:0.6b`, 1,024 dimensions. The repository loader validates snapshot/chunk consistency; each question checks the installed embedding digest against the saved index.

Chunking uses at most 3,000 characters with five lines of overlap, without function boundaries. Index input is path plus chunk text. Retrieval is brute-force cosine similarity on normalized vectors, top five, without score threshold, reranking or lexical/symbol search. Context construction subtracts output allowance, system/question UTF-8 bytes and a 512 reserve from 4,096; each excerpt is capped at half the initial remaining budget. Whole lines are retained from each chunk's beginning. Long chunks can therefore lose their actual implementation; often only two of five results fit. Final prompt headers use the shortened line ranges.

Generation uses `/api/chat`, schema-constrained JSON (`answer`, `citations`), `think: false`, temperature 0, `num_ctx: 4096`, `num_predict: 700`, timeout 180 seconds, and `keep_alive: 0`. The system prompt requires answers solely from excerpts, treats excerpts as untrusted data, forbids claims of execution, requires abstention without citations when evidence is insufficient, and warns against inferring absence from unseen files. It requests a concise answer but no claim-to-citation mapping.

Postprocessing rejects unknown excerpt IDs and malformed answers. An empty citation list overwrites the model's text with a generic abstention. It checks neither the truth of a claim nor whether a recognized citation supports it. `done_reason: length` raises an error; the API would expose a generic 503 rather than the partial answer.

## Existing automated evaluation

`evaluate_rag.py` has three keyword/expected-path fixtures. It does not check claim support, completeness, latency or retrieval scores. `verify_ollama.py` rebuilds a tiny index around the first fixture, so it is a smoke test rather than evidence about full-index quality; it was not used here. `tests/test_rag.py` and `tests/test_llm.py` use mocked answers/HTTP for unit contracts and are not evidence of live answer quality. No mocked tests are counted as quality results in this report.
