# Requests RAG: DeepSeek evaluation

Completed 23 September 2026. The original 36-case live run is preserved, all answers have been reviewed against the pinned repository source, and three additional real DeepSeek diagnostic calls have completed. No RAG implementation or model configuration was changed.

DeepSeek is not a demonstrated quality upgrade for this pipeline. It fully answered only 2 of 15 source-answerable questions; Qwen also fully answered 2. DeepSeek correctly abstained on 2 of 3 unanswerable questions, but made substantially more unsupported claims on the harder source questions. The three legacy fixtures passed for both models and substantially overstate useful answer quality.

## Completion and preservation

At resumption, all 18 DeepSeek and 18 Qwen calls were already recorded. The source review covered DeepSeek 1-14 only; Qwen review and the report were incomplete. No original case was rerun. Completed work: remaining DeepSeek review, all Qwen review, exact snapshot/excerpt verification, aggregate results, and three new question-specificity probes (19-21) using real `deepseek-coder-v2:16b` through the unchanged pipeline.

The earlier task's full conversation is unavailable in this resumed thread. Scope is reconstructed from the saved 18 questions, harness, partial report and review; completeness against additional unstored requirements cannot be certified. All saved-scope cases are now accounted for, including the failed answer in case 4; it is a measured failure, not a missing test.

The original `deepseek-results.jsonl`, `deepseek-metadata.json`, cases, source evidence, harness and partial `deepseek-review.json` remain unchanged. The earlier report is preserved as `deepseek-report-in-progress.md`. Completed judgments are in `deepseek-review-completed.json`; new calls and provenance are in `deepseek-continuation-results.jsonl` and `deepseek-continuation-metadata.json`. Unrelated tracked and untracked project changes were left intact. Recorded implementation and `.env` hashes match the original metadata; bundle SHA-256 also matches. Original results SHA-256: `a51256f68dccaccd1a6dc0852878a522702a155a6698b442a09c676168454cff`.

## Results and scoring

Manual source review evaluates factual correctness, completeness, and whether the actual supplied excerpts support the claims. A strict success requires a complete supported answer, or an appropriate abstention on an unanswerable question with no citations. An abstention caused by missing retrieval on an answerable question is safe behavior but not a successful repository answer. Partial answers receive no full-success credit. This is an assistant-authored qualitative review, not an independent blinded assessment.

| Original 18-question run | DeepSeek coder v2 16B | Qwen 3.5 4B |
|---|---:|---:|
| Complete answers to source-answerable questions | 2/15 | 2/15 |
| Semantically correct abstentions on unanswerable questions | 2/3 | 2/3 |
| Complete semantic successes overall | 4/18 (22.2%) | 4/18 (22.2%) |
| Strict successes including citation/abstention contract | 4/18 (22.2%) | 3/18 (16.7%) |
| Original legacy keyword/path fixtures | 3/3 | 3/3 |
| Rejected answers | 1/18 | 0/18 |
| Output-limit stops | 0 | 0 |
| Mean end-to-end latency | 45.75 s | 40.95 s |
| Median end-to-end latency | 45.16 s | 39.75 s |
| Observed latency range | 40.38-54.80 s | 34.11-48.77 s |

Qwen's strict score loses case 17 because its correct abstention includes irrelevant citations, contrary to the prompt. This small scoring difference is not evidence that DeepSeek is better: DeepSeek has ten inaccurate, unsupported or misleading delivered answers (5, 6, 8, 10, 12-16, 18), three partial answers (7, 9, 11), and one rejection (4). Qwen has four problematic answers (7, 9, 14, 18), four partial/imprecise answers (5, 6, 10, 11), and six safe but unsuccessful insufficient-context answers (4, 8, 12, 13, 15, 16). These categories are qualitative, with reasons recorded per case.

Every original pair received identical chat messages and generation options except the selected model. All 36 responses identify the expected real model and returned HTTP 200; the DeepSeek case 4 failure occurred in citation validation after generation. All delivered reference ranges map to the actual supplied source text, but that does not establish claim support. The integrity audit additionally checks retrieved text and the 950 saved line-numbered evidence lines against the bundle's actual source contents.

Latency includes embedding, model load/unload and pipeline overhead with `keep_alive: 0`; it is not steady-state token generation speed or production p99. Original calls ran sequentially in model blocks, not randomized trials. DeepSeek's mean was about 12% higher in this run; no significance claim is justified.

## Per-question source review

Paths below refer to the exact Requests commit recorded under configuration, not a current upstream checkout. Full answer text, raw JSON, retrieved chunks and supplied excerpts remain in the result logs. Detailed correctness/support/completeness notes for every model/case are in `deepseek-review-completed.json`.

| ID / subject | DeepSeek | Qwen | Actual source finding |
|---|---|---|---|
| 1 License | Correct | Correct | `__version__.py:12`: Apache-2.0. |
| 2 BasicAuth header | Correct | Correct | `auth.py:111-113` assigns `_basic_auth_str(username, password)` to Authorization. |
| 3 Historical password | Correct abstention | Correct abstention | Requested production secret is not established by supplied repository code. |
| 4 Basic-auth encoding | Rejected citation labels; raw answer partly wrong | Safe abstention | `auth.py:44-75`: legacy conversion for non-string/bytes, Latin-1 for strings, colon-joined bytes then Base64. Sent prefix stops at 41. |
| 5 Digest challenge | Incorrect unbounded retry/challenge story | Partial | `auth.py:293-319` bounds retries, parses server challenge, consumes/closes response, copies request, applies cookies, sends and attaches history. |
| 6 get/request/Session chain | Partly incorrect | Partial/imprecise | `api.py:70-87`: get delegates to request, which creates/closes Session; `sessions.py:622-653` prepares and sends. |
| 7 Session preparation | Partial | Incorrect method/class claims | `sessions.py:524-553` merges session then request cookies; merges headers/auth, conditionally uses netrc, then calls PreparedRequest.prepare. |
| 8 Environment settings | Incorrect | Safe abstention; unnecessary citations | `sessions.py:641-651,845-868`: separate environment merge handles proxies, trust_env, CA bundles and session defaults before send. |
| 9 Session.send | Partial | Incorrect 307/308-to-GET claim | `sessions.py:777-829`: adapter send, hooks, cookies, redirects/history, non-stream content consumption. |
| 10 Redirect auth | Reverses upgrade exception | Partial | `sessions.py:158-184`: changed host strips; same-host standard-port HTTP-to-HTTPS retains; default-port equivalence retained; otherwise changed scheme/port strips. |
| 11 Redirect method | Partial: only 301 | Partial: narrow test observation | `sessions.py:378-392`: 302/303 non-HEAD becomes GET; 301 POST becomes GET; HEAD retained. |
| 12 307/308 body/cookies | False absence claim | Safe abstention; unnecessary citations | `sessions.py:249-284` preserves body/body headers for these statuses, rebuilds cookies and conditionally rewinds. |
| 13 Body serialization | Incorrect tell()-based classifier | Safe insufficient-context answer | `models.py:588-650`: JSON when no data and json supplied; streaming uses iterable/type predicate; tell records position; otherwise multipart/form/raw handling. |
| 14 Response.json | Wrong decoding/error behavior | Wrong decoding/error behavior | `models.py:1101-1124`: UTF guess when eligible, text fallback, JSONDecodeError wrapping. Supplied prefix instead ends inside Response.text. |
| 15 raise_for_status | Incorrectly includes 3xx | Safe abstention | `models.py:1160-1171` raises only for 400 <= status < 600, otherwise no HTTPError. |
| 16 Adapter timeout/errors | Misleading negative claim then qualified abstention | Safe abstention | `adapters.py:681-746` converts tuple/scalar timeouts, preserves TimeoutSauce, maps urllib3 exceptions. Body absent from top five. |
| 17 Live traffic/p99 | Correct abstention | Correct abstention with citation-contract violation | Source cannot establish live application metrics. |
| 18 OAuth2 refresh | Unsupported implementation/endpoint claims | Unsupported categorical absence/refresh claim | `docs/user/authentication.rst:90-99` refers to external requests-oauthlib OAuth2 flows; it does not establish requested refresh implementation or endpoint. |

For case 18, even a plausible statement about an external library is not a supported answer from these excerpts. Neither model should infer an implementation, endpoint or repository-wide absence from the limited context.

## Additional live DeepSeek probes

These three new prompts test whether explicit filenames and narrower symbol questions resolve observed failures. They are exploratory follow-ups selected after review, excluded from the original 18-question comparison, and are not independent benchmark samples. They use the same bundle, embedding digest, DeepSeek digest, system prompt, 4,096 context setting and 700 output cap. No source was manually injected into their prompts.

| ID | Probe | Outcome checked against source | End-to-end time |
|---|---|---|---:|
| 19 | Exact raise_for_status conditions; does 302 raise? | Broad conclusion now correct, but citations show bool/nonzero documentation and status-code mapping, not the actual exception predicate. Direct grounding remains incomplete. | 44.12 s |
| 20 | Response.json with guess_json_utf and RequestsJSONDecodeError named | Still wrong: claims LookupError/TypeError become RequestsJSONDecodeError. Context again truncates inside text. | 232.08 s |
| 21 | Same-host HTTP:80 to HTTPS:443 auth predicate | Wrong and self-contradictory: returns True but says not to strip. Actual method returns False. | 48.11 s |

All three returned real DeepSeek responses with HTTP 200 and completed without a recorded exception. Case 20's much larger wall time is retained as observed; the continuation log does not isolate all phase timings, so no cause is asserted. None of the three demonstrates a fully supported complete recovery. Filename-specific phrasing alone is not a reliable remedy.

## Root causes and proposed improvements

These are proposals only; no production changes were made.

1. **Recover the actual symbol implementation.** Add symbol/path-aware or hybrid lexical/semantic retrieval and assess reranking. Cases 7, 8, 9, 12, 13, 15 and 16 miss key implementation regions. Evaluate recall of answer-bearing lines, not merely file-path hits.
2. **Preserve answer-bearing context.** Use function-aware chunks, adjacent-chunk expansion or query-focused spans, and a measured token budget. Cases 4, 5, 10 and 14 retrieve relevant code that never reaches the model. Keep source ranges exact when selecting spans. Any context/model-setting experiments should be a separately authorized evaluation.
3. **Strengthen grounding and abstention.** Require claim-to-source support, detect contradictions and unsupported absence claims, and distinguish insufficient context from a complete answer. Enforce citation-free abstentions consistently. The JSON schema and recognized IDs currently validate structure only.
4. **Improve evaluation coverage and scoring.** Retain these regression questions with source-grounded expected behaviors, partial-credit criteria and boundary cases. Keep all three legacy fixtures, but report them separately from semantic accuracy. Include prompt wording variants, evidence-recall metrics and unsupported-claim counts.
5. **Run controlled future comparisons.** After retrieval/context experiments are approved, compare on multiple repositories, repeated and randomized model order, recorded hardware/runtime versions, and separate warm/cold latency. An oracle-context experiment could isolate generation from retrieval failures, but was not performed because this task preserves the production pipeline and configuration.

## Remaining limitations and unresolved issues

- Evaluation work in the saved scope is complete; the implementation defects above remain unresolved by design.
- One repository/commit, 18 original questions per model, one sample per question, and three selectively chosen DeepSeek diagnostics are insufficient for general model rankings. Qwen's cautious behavior is preferable on several cases but does not solve missing context.
- Model quality and retrieval/context failures are entangled. Source inspection identifies missing evidence and contradicted claims; without controlled oracle evidence, it cannot quantify their independent contributions.
- Manual judgments were made by the evaluating assistant, not an independent human or blinded reviewer. The full logs and line-based evidence are retained for audit.
- The historical password and live metrics are not source-answerable. OAuth2 refresh is not established by these excerpts. These cases test abstention, not recovery of external information.
- The exact original task prompt is unavailable here. Deployed backend configuration, remote GitHub link availability, multi-user load, UI behavior and production traffic were not verified. No claims of passing those checks are made.
- The configured model remains Qwen. Real DeepSeek selection occurs only in the evaluation HTTP wrapper; no installation/configuration switch was made.
- The original `run_deepseek.py` opens its results file in write mode and overwrites metadata. Do not rerun it against these artifacts. The new `continue_deepseek.py` preserves old results and skips already-recorded diagnostic IDs, including failures; deliberate new trials should use new artifacts.

To reproduce the offline integrity check, run `uv run --env-file .env python evaluations/audit_deepseek.py` from `backend`. `deepseek-integrity.json` records its checks and descriptive statistics; it is not a semantic pass/fail judge. `complete_deepseek_review.py` persists the explicitly authored manual judgments, while `continue_deepseek.py` runs only missing diagnostic cases.

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
