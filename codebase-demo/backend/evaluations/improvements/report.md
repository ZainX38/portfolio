# Incremental RAG quality improvements

Status: complete. All three stages contain 36 recorded live attempts (18 questions per model), with all 108 attempts manually reviewed. The Stage 3 prompt was rejected and the Stage 2 prompt restored. Retrieval and implementation-context improvements are retained. No further experimental stage was started.

Original evaluation artifacts and report are preserved in the parent directory. The baseline source is archived in `baseline/`; each measured stage archives all backend Python source, model digests, unchanged questions, settings, exact requests, retrieved code, final excerpts, raw responses and answers.

## Final results and decision

Strict success requires a complete, correct, source-supported delivered answer, or appropriate citation-free abstention on an unanswerable question. Partial answers are not counted as successes. Semantic errors below count **delivered** answers with incorrect or unsupported claims; rejected responses are separate and may also contain semantic defects in their raw text.

| Stage | Model | Strict successes / 18 | Delivered semantic errors | Partial answers | Safe but unanswered | Support/protocol issues | Rejected citations |
|---|---|---:|---:|---:|---:|---:|---:|
| 1: retrieval | DeepSeek | 3 | 11 | 2 | 0 | 1 | 1 |
| 1: retrieval | Qwen | 3 | 7 | 3 | 4 | 1 | 0 |
| 2: context | DeepSeek | 4 | 8 | 6 | 0 | 0 | 0 |
| 2: context | Qwen | **7** | **4** | 6 | 0 | 1 | **0** |
| 3: grounding prompt | DeepSeek | 3 | 10 | 3 | 0 | 1 | 1 |
| 3: grounding prompt | Qwen | 1 | 2 | 0 | 0 | 0 | 15 |

The apparent fall in Qwen's delivered semantic-error count in Stage 3 is **not an accuracy improvement**: 15 answers were rejected before delivery. The three delivered answers were one supported auth-stripping explanation and two semantic failures. Per-case reasons, including raw-content observations for rejected answers, are in `manual-review.json`; `review-summary.json` is a mechanical count of those authored judgments, not an automated quality judge.

| Evidence metric | Original baseline | Stage 1 | Stage 2 | Stage 3 |
|---|---:|---:|---:|---:|
| Complete target regions in top five | 6/15 | 14/15 | 14/15 | 14/15 |
| Target lines in top five | 154/458 | 436/458 | 436/458 | 436/458 |
| Complete target regions in final prompt | 2/15 | 3/15 | 11/15 | 11/15 |
| Target lines in final prompt | 29/458 | 134/458 | 390/458 | 390/458 |

Retrieval alone improved evidence recall without improving strict answer success. Implementation context converted that recall into substantially more visible evidence and raised Qwen's strict success from 3/18 to 7/18. DeepSeek returned to its original baseline 4/18; it did not exceed it. These are reasons to retain retrieval **together with** context assembly, not evidence that either model is generally reliable.

Observed mean end-to-end seconds (DeepSeek / Qwen): Stage 1 **44.37 / 39.52**, Stage 2 **39.93 / 38.16**, Stage 3 **42.12 / 44.46**. These include failures, loading and query embedding; fixed sequential order and one sample per case do not support controlled speed rankings.

## Semantic failures versus output-format failures

- Stage 3 had **16 citation-format rejections**: DeepSeek case 7 and Qwen cases 1-6, 8-9, 12-18. Every rejected citation becomes a valid supplied ID after removing its surrounding square brackets. For example, the model returned `"[source-1]"` where the API requires `"source-1"`. The unchanged validator correctly rejected it. The prompt's request for inline `[excerpt-ID]` markers did not reliably distinguish prose markers from citation-array values.
- All 36 Stage 3 HTTP responses were 200 and their answer content was parseable JSON. There were **no JSON parse failures or output-limit stops**. These were not network/model-service failures.
- Format failure does not imply factual failure. Qwen's rejected license answer and case-15 status-code answer had correct core facts; its rejected live-metrics answer appropriately declined to infer metrics. They still failed the delivered-answer contract.
- Conversely, repairing brackets alone would not fix answer quality. Qwen's rejected case 12 falsely says 307/308 cannot rewind and the Cookie header is not removed; case 13 invents a `tell()` requirement for streaming. DeepSeek's accepted answers continue to misread redirect guards, JSON exception flow and the 3xx status predicate.
- Qwen case 11 was accepted as valid JSON with a valid citation but contained a false claim that 303 behavior was unspecified and ended mid-expression. It is a semantic error plus incomplete prose, **not** a JSON/citation validator failure or a recorded token-limit stop.
- The same content/support rubric is used across stages. Missing the newly requested inline prose markers is noted separately and does not by itself change an otherwise supported answer's grade. Existing citation-free abstention requirements remain part of the contract.

## Best recorded MVP configuration

Recommend **Stage 2 with `qwen3.5:4b`**, the original 599-byte system prompt, retained Python-symbol retrieval and exact implementation-body context, and the existing `qwen3-embedding:0.6b` index. Preserve the measured 4,096 context setting, 700 output-token cap, temperature zero, top-five retrieval and `keep_alive: 0`. Keep the JSON schema and strict citation validator as measured. These settings were held fixed, so this evaluation does not establish that alternative limits/models/indexes would be better.

This is the best **tested candidate for this Requests MVP**, with 7/18 strict successes, six useful partial answers, four semantic failures and one abstention-protocol issue. It is not evidence of release-ready answer accuracy. Errors remain in precedence, redirect cookies/body handling, stream classification and unsupported OAuth claims. One repository, one frozen question set, single samples and assistant-authored manual judgments limit generalisation. Quality and latency do not justify switching to DeepSeek on these recorded results.

The original Stage 2 prompt has been restored in `rag.py`. All backend source hashes match the Stage 2 archive; `symbol_retrieval.py` and `source_context.py` are retained unchanged. The local environment matches its frozen evaluation checksum and still selects Qwen. No model, quota, embedding, index, schema or deployment settings were changed for this decision. All experimental archives remain intact, including the rejected Stage 3 prompt.

Final checks: 30 backend tests pass; frontend lint and production build passed during this continuation. `integrity.json` confirms all three stages are complete, all 18 paired prompts per stage match across models, and all 36 Stage 2/3 comparisons have identical excerpts and user messages. `final-state.json` records restoration checks and the format-failure breakdown. Work stops here pending the owner's next instruction.

## Baseline failure localisation

All locations refer to Requests commit `611c6162cbc4ac2020a2f91c7cfa4f3abf9bbb60` in the existing bundle. `source-targets.json` freezes the line regions used to compare evidence visibility. This diagnostic counts even comments/blank lines in those regions; it is deliberately distinct from manual semantic review.

| Case | Missing implementation | Where evidence was lost |
|---|---|---|
| 4 | `auth.py:65-73`, Latin-1 and Base64 | Full first chunk contains implementation; final excerpt ends at 41 in comments. |
| 5 | `auth.py:293-319`, challenge processing and bounded resend | Retrieved chunk starts at 255; prompt stops at 286, before challenge processing. |
| 6 | `sessions.py:622-653`, create/prepare/environment/send | Session.request body absent from top five; api.py call chain was supplied but not correctly explained. |
| 7 | `sessions.py:524-553` and `84-105`, preparation and precedence | Correct Session method absent from top five; PreparedRequest auth method retrieved instead. |
| 8 | `sessions.py:641-651,845-868`, environment merge | Implementation absent from top five; related documentation also truncated before the relevant passage. |
| 9 | `sessions.py:777-829`, send sequencing | Core method absent from top five; only its tail is retrieved at rank five and dropped. |
| 10 | `sessions.py:158-184`, auth stripping predicate | Relevant function at lower retrieval ranks is dropped; prompt contains downgrade test and rebuild_auth caller. |
| 11 | `sessions.py:378-392`, status-specific method rewrite | Method body absent; test prefix only shows 301 behavior, other statuses cut away. |
| 12 | `sessions.py:249-284`, preserve/rebuild/rewind | Body absent from top five; unrelated redirect tests dominate. |
| 13 | `models.py:588-650`, body selection | JSON/stream classifier not retrieved; form handling in retrieved chunk cut away. |
| 14 | `models.py:1101-1124`, JSON decode and exceptions | Correct chunk retrieved, but prefix ends at 1085 in Response.text. |
| 15 | `models.py:1160-1171`, status predicate | raise_for_status body not retrieved; bool docs and a 200 example dominate. |
| 16 | `adapters.py:681-746`, timeouts/exceptions | HTTPAdapter.send body not retrieved; tests/docs and module imports dominate. |
| 18 | Requested OAuth refresh implementation/endpoint | Not established by supplied code. External-library documentation does not support invented behavior or repository-wide absence. |

## Experiment controls

Same 18 questions and both installed models (`deepseek-coder-v2:16b`, `qwen3.5:4b`), same repository/index and embedding model, 4,096 context setting, 700 output cap, temperature zero, and keep_alive zero. No reindexing or configuration edits. Stages run sequentially: retrieval only, then context assembly, then grounding. Changes are measured before the next stage is applied. Errors remain recorded; completed cases are not silently retried.

Stage 1 uses Python's standard-library AST to find explicitly named functions and direct local/self helpers, prioritises their existing chunks, and falls back to original vector order. It does not execute repository code or search excluded files. Non-Python and unparseable files keep vector retrieval. No third-party framework or extra service is introduced.

## Stage 1: retrieval only (complete)

All 36 live answers completed before context assembly was changed. 26 unit tests passed. Full target regions in top five rose from 6/15 to 14/15 (154/458 to 436/458 target lines). Final-prompt full coverage rose only from 2/15 to 3/15 (29/458 to 134/458 lines). The remaining retrieval miss is `merge_setting` in case 7; generic symbol matches consume positions ahead of it.

Strict fully supported successes: DeepSeek 3/18 versus baseline 4/18; Qwen 3/18 versus baseline 3/18. DeepSeek case 2 remains factually correct but adds a Base64 claim unsupported by its cited helper-call excerpt, losing strict grounding credit. Its three strict successes are 1, 3, 17. Qwen's are 1, 2, 3. The citation-ID rejection in DeepSeek 4 persists; no Qwen runtime errors occurred.

There are useful partial improvements (session preparation, environment method identification, adapter mappings), but no new complete supported success. DeepSeek 9 and 11 regress from partial to incorrect. Qwen 5, 10 and 11 regress from partial to incorrect; 12 and 16 regress from safe abstention to incorrect. Qwen 9 improves from an incorrect claim to safe abstention. Thus retrieval alone is not a release-quality improvement: it exposes more implementation but prefix truncation and incorrect reading of conditions still dominate. These intermediate regressions are retained rather than hidden.

## Stage 2: context assembly (complete)

Retrieval ranking and the original system prompt remain unchanged. Context uses the already discovered Python symbols to expand indexed source into exact implementation-body spans, skipping leading docstrings. Highest-confidence named functions and direct helpers get priority; package-qualified convenience functions already present in retrieved chunks are also retained. All added lines must belong to the existing index. Complete bodies are packed where possible; oversized methods use a query-relevant contiguous window bounded by AST statement locations and explicitly labelled partial. No source is rewritten or assembled into a fictitious contiguous citation.

The conservative UTF-8 byte budget and 512 reserve remain. A 600-byte minimum system-prompt allowance stabilises the source budget for the later prompt-only experiment. The local preview recovers complete bodies for encoding, digest handling, request flow, session merging, environment settings, auth stripping, method rewriting, JSON parsing and status errors. The oversized send/body/adapter methods remain explicitly partial. All 30 unit tests pass, including new source-fidelity, budget, docstring and excluded-line checks; the existing reference test was updated for the new exact body span (original test archived in baseline).

Resumed on 23 September after correcting a stray `@` in the local output-token value; the corrected environment exactly matches the frozen SHA-256. Ollama was stopped and was restarted on localhost. Existing four records were preserved, with no retries. Backend tests (30), frontend lint and production build pass. `audit_improvements.py` audits archived source hashes, question identity, model settings, exact source spans and references; partial runs are explicitly labelled incomplete.

All 36 context-stage answers completed without runtime errors. DeepSeek has 4/18 strict successes (1, 2, 3, 17), Qwen 7/18 (1, 2, 3, 4, 10, 11, 15). Full target visibility reaches 11/15 cases and 390/458 lines, versus 3/15 and 134/458 after retrieval alone. Case 2's DeepSeek helper citation is now supported, and case 4 no longer fails citation validation. Qwen recovers encoding, auth-stripping exceptions, method rewriting and status errors. Its merge-setting precedence regresses from partial to incorrect. DeepSeek still misreads redirect guards, JSON error flow, and the 3xx predicate despite complete evidence. Both models invent unsupported OAuth refresh claims. All per-case judgments, including useful partial improvements, are retained in `manual-review.json`.

## Stage 3: grounding prompt (complete; not retained)

Only the system prompt changes. It asks for each question part, precise conditions/exceptions/order, a source ID on each factual sentence, explicit limits for partial evidence, and citation-free abstention when no answer is established. It forbids inferring helper behavior, omitted code or repository-wide absence. This is a prompting experiment, not a semantic verification guarantee. The JSON schema and production citation validator remain unchanged.

The new prompt is 575 UTF-8 bytes versus 599 previously; both remain inside the existing 600-byte allowance, preserving the source budget. The audit checks identical excerpts and user messages between stages 2 and 3, as well as identical prompts across the two models. Same cases, index, models, output limit and context limit; no reindexing or model/configuration changes.

All 36 attempts completed. DeepSeek strict successes fell from 4/18 to 3/18; Qwen fell from 7/18 to 1/18. There were 16 bracketed-citation rejections, alongside the semantic failures described above. The Stage 3 source remains archived for reproducibility, while the live source has been restored exactly to Stage 2. No fourth stage was run.
