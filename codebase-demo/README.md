# Codebase AI portfolio demo

Standalone React/Vite page at `/codebase-demo/`, with a small FastAPI API. Explorer components are adapted from the original AI-Codebase project; that project is not a runtime dependency and is not modified.

## Current stage

- Working repository tree, nested folders, cached file viewing and error states.
- Public repository configured by `DEMO_REPOSITORY` (GitHub HTTPS URL or `owner/repo`), defaulting to `psf/requests`. Optional `DEMO_REPOSITORY_COMMIT` pins a full SHA for both preparation and serving.
- Offline downloader resolves the default branch to one commit, saves supported text files and creates line-based chunks.
- Browser and API use the same snapshot ID; stale clients receive 409 and must reload.
- Ollama integration uses `qwen3.5:4b` for answers and `qwen3-embedding:0.6b` for repository/query embeddings. Defaults to `http://localhost:11434` and a configurable 4096-token context. Generation disables thinking, bounds output and sends `keep_alive: 0`.
- **Public AI remains disabled at the owner's request.** Usage limits stay at zero. `/api/demo/ask` returns 503 and the question form is disabled; offline evaluation can still use the local models.
- Embeddings, cosine retrieval, bounded context, structured answers and validated file references are implemented without a RAG framework. Switching answer models requires only configuration. Switching embedding models requires reindexing.
- Python symbol lookup now prioritizes explicitly named implementations and direct helpers within indexed source. Context assembly supplies exact implementation-body spans, skips leading docstrings, and labels oversized bodies as partial. Other queries retain vector retrieval. Controlled comparison details are in `backend/evaluations/improvements/report.md`.
- Initial AI coverage includes all supported text files. Optional `--scope selected --include "src/*"` filters coverage using repeatable path globs. The explorer retains every snapshot file. The UI states partial coverage, file responses include their indexing status, and `/api/demo/coverage?snapshot_id=...` lists indexed paths and every exclusion reason.

## Folder structure

```text
codebase-demo/
  index.html
  frontend/           # Demo page and adapted explorer
  backend/            # Configured-repository API, downloader, chunking and tests
  data/<owner>--<repo>/<commit-or-default>/  # Ignored snapshots, indexes, cache
  Dockerfile          # Optional single-service production image
```

## Local setup

From the portfolio root:

```sh
npm ci
```

From `codebase-demo/backend`:

```sh
uv sync --frozen
uv run python index_repository.py
uv run uvicorn main:app --host 127.0.0.1 --port 8001
```

Run `npm run dev` from the portfolio root in another terminal. Open `http://localhost:5173/codebase-demo/`. Vite forwards `/api/demo` to port 8001. The Codebase AI Preview button also opens the demo.

For AI, start a local Ollama service, install the models and pre-index the saved snapshot:

```sh
ollama pull qwen3.5:4b
ollama pull qwen3-embedding:0.6b
uv run python embed_repository.py
```

The result is `data/psf--requests/default/bundle-indexed.json` with the default configuration. Point `DEMO_BUNDLE_PATH` to its absolute path and restart the API. Keep limits at zero while public AI is disabled. The server does not index on startup. The separate `embedding-cache.sqlite` saves completed batches; rerunning the command resumes through cache hits. Do not ship this cache to production.

All supported text is indexed by default, including reStructuredText (`.rst`). An empty text file or an oversized line may have no chunks. For a larger preset, select paths explicitly, then expand from the same saved source:

```sh
uv run python embed_repository.py --scope selected --include "src/*" --include "README*" --output ../data/selected.json
uv run python embed_repository.py --input ../data/selected.json --scope all --output ../data/expanded.json
```

The cache key includes the complete snapshot ID, model digest and exact path/text. Batches can resume or be reused during scope expansion only within the same snapshot. Changing repository, commit or source contents requires fresh embeddings, even when chunk text is identical. Legacy cache entries are not reused. No partial index is published.

The snapshot and embedding commands refuse to overwrite existing outputs. To prepare an update:

```sh
uv run python index_repository.py --output ../data/bundle-next.json
uv run python embed_repository.py --input ../data/bundle-next.json --output ../data/bundle-next-indexed.json
```

Use `DEMO_BUNDLE_PATH` to run the API against that candidate. After verification, pass the chosen indexed candidate as the Docker `DEMO_BUNDLE` build argument for the next image build. Keep the prior release/image for rollback. The running process does not reload files in place.

Optional local configuration is documented in `backend/.env.example`. If using a `.env`, pass `--env-file .env` to `uv run`; it is not loaded implicitly. `GITHUB_TOKEN` is optional for GitHub metadata rate limits and is used only during offline preparation. Never put credentials in frontend variables.

## Snapshot and embeddings

`bundle.json` is one versioned artifact containing:

- Repository name, resolved default branch and full commit SHA.
- A checksum of the snapshot and its source contents.
- Supported file contents plus reasons for excluded files.
- Chunks with paths, exact line ranges and text matching those source files.
- Chunking version/settings and initially `embeddings: null`.
- After indexing: vectors, ordered chunk IDs, embedding model name/digest, dimensions and snapshot ID.
- A coverage manifest containing indexed paths and excluded paths/reasons. The model is instructed that it has not analysed the entire repository.

The API validates the checksum and each chunk against the snapshot at startup. It fails startup for missing or inconsistent artifacts. All contents requests carry the snapshot ID. There is no live GitHub fetch, visitor-supplied repository, symlink traversal or repository code execution.

The download is capped at 60 MB compressed, 30 MB supported source, 200 KB per file, 10,000 files and 20,000 chunks. Unsupported formats, credential filenames, binaries, generated files and dependencies appear as unavailable. Lines longer than 3,000 characters remain viewable but are omitted from chunks; this avoids oversized embedding inputs while preserving source line numbers.

The embedding command consumes this saved bundle **without resolving the branch again** and writes a new complete bundle. Startup rejects mismatched snapshot IDs, chunk IDs, vector counts/dimensions and source excerpts. Incoming questions use the same embedding model; the API checks its installed digest before embedding to prevent a changed model tag being mixed with old vectors. Explorer and retrieval share one loaded `Repository` object.

The Requests snapshot prepared on 22 September 2026 is pinned to `611c6162cbc4ac2020a2f91c7cfa4f3abf9bbb60`: 97 supported text files, 33 excluded files and 288 chunks from 96 non-empty files. Runtime normalizes vectors into compact float arrays and performs a linear cosine scan. Measure memory use on the deployment machine.

To change the preset again, set `DEMO_REPOSITORY` consistently for the snapshot command, embedding command and API. Optionally set `DEMO_REPOSITORY_COMMIT` to the intended full SHA; without it, the downloader resolves the default branch once and the API serves that immutable artifact without checking GitHub for branch movement. Paths default to `data/<owner>--<repo>/<commit-or-default>/`. An explicit `DEMO_BUNDLE_PATH` must point to an artifact matching that configuration: repository or configured-commit mismatches fail startup with instructions to create a new snapshot and index. Updating a snapshot also invalidates old embeddings through its checksum, and old browser requests receive 409. Explorer, RAG and citation links all use the same loaded snapshot and SHA. Restart the API after changing configuration or publishing an artifact.

Previous artifacts are retained for rollback and are never selected automatically. The old top-level snapshot/cache are not used by the Requests preset.

For the 4096-token answer context, prompt construction uses conservative UTF-8 byte bounds and reserves output/template space. Context allocation leaves room for a second retrieved excerpt so a large first chunk cannot hide adjacent implementation code. Retrieved chunks can be shortened at line boundaries, with citation line ranges shortened accordingly. This intentionally favors a small amount of code over silently truncating the model prompt. No approximate character-to-token conversion is treated as an exact tokenizer. The model can still make mistakes; valid references establish source provenance, not proof of every claim.

For named Python symbols, implementation context replaces prefix truncation: complete bodies and direct helpers are preferred, and oversized bodies use a query-focused contiguous span bounded by AST statements. Every included line must already be covered by the index. Source text is never rewritten, and citation ranges match the exact excerpt. This improves evidence visibility but does not guarantee that a model interprets conditions correctly.

## Production artifact and deployment

No hosting provider has been selected. A host supporting a long-running Docker container is the simplest complete deployment: one service serves both the portfolio build and `/api/demo`, avoiding cross-origin configuration.

1. Generate and verify `codebase-demo/data/psf--requests/default/bundle-indexed.json` in the release workspace.
2. In CI, download the already-generated bundle from your release artifact storage into that exact path. Git checkout alone is insufficient because the file is ignored. Do not regenerate or embed on each container startup.
3. Build from the portfolio root:

   ```sh
   docker build -f codebase-demo/Dockerfile -t portfolio-demo .
   docker run --rm -p 8000:8000 --env-file codebase-demo/backend/.env -v demo-usage:/app/usage portfolio-demo
   ```

4. Open `http://localhost:8000/codebase-demo/`. The Dockerfile explicitly copies the ignored indexed bundle into `/app/data/bundle.json`. Its build context allowlist excludes local secrets, the Python environment and other artifacts. A missing bundle fails the build. For an explorer-only image, use `--build-arg DEMO_BUNDLE=codebase-demo/data/psf--requests/default/bundle.json`.
5. Deploy the image to the chosen host, configure HTTPS and port 8000, and use `/api/demo/repository` as the readiness endpoint. Allocate memory after measuring the final embedding bundle. Retain the image digest and source SHA for rollback.

Production loads the packaged bundle into memory exactly once. Neither the snapshot nor embeddings need writable production storage. The daily usage counter needs a persistent writable volume at `/app/usage`; do not put it on an ephemeral filesystem. Keep a single worker/replica for the in-memory throttles. Proxy-header trust must be configured for the actual host before relying on per-IP limits; the image currently disables forwarded headers. Configure request timeouts/body limits at the ingress too.

Ollama must run on the server's loopback interface or a private container network, never a public port. The browser contacts only FastAPI. Inside a container, `localhost:11434` refers to that container; set `OLLAMA_URL` to the private Ollama service address or a supported host gateway. Only publish the portfolio/API port. The host needs sufficient CPU/GPU/RAM for the models; static hosting alone cannot run Ollama. Model weights are provisioned separately on that private service and are not included in the portfolio image. Do not expose or proxy `/api/chat`, `/api/embed` or the whole Ollama API to visitors.

Alternative: host `dist/` on a static host and run the API separately. Prefer a same-origin `/api/demo` reverse proxy. If unavailable, set the **public** `VITE_DEMO_API_ORIGIN` at frontend build time and `DEMO_ALLOWED_ORIGINS` on the API. `npm run preview` is only a frontend preview and does not reproduce the API deployment. No host-specific deployment has been performed.

## AI limits — replacement values pending

The earlier proposal of 25 attempts/day, 3/minute/IP, one concurrent request, 1,000-character questions and 500 output tokens was not approved. Defaults are zero, which disables public AI. Set `DEMO_DAILY_LIMIT`, `DEMO_IP_PER_MINUTE`, `DEMO_MAX_CONCURRENT`, `DEMO_MAX_QUESTION_CHARS` and `DEMO_MAX_OUTPUT_TOKENS` to the owner's chosen positive values. Request bodies have an additional 8 KB ceiling. There are no automatic model retries.

One small SQLite daily counter reserves attempts atomically before model calls, including failed attempts. Short-lived IP/concurrency limits stay in memory. This avoids Redis while retaining the daily cap across restarts. An unwritable counter prevents inference. Limits apply to compute usage with local Ollama; hosting cost is separate. Offline indexing is an administrator command, not a public endpoint. The daily cap is shared by all visitors and can be exhausted deliberately; this MVP has no account-level abuse prevention.

## Checks

```sh
# Portfolio root
npm run lint
npm run build

# codebase-demo/backend
uv run python -m unittest discover -s tests -v

# Explicit real-model smoke test, using a tiny in-memory subset of the same SHA:
uv run python verify_ollama.py

# After the complete index exists:
uv run python evaluate_rag.py
```

The incremental experiments preserve all original results and archive source per stage. From `backend`, run `uv run --env-file .env python evaluations/audit_improvements.py` to audit provenance and citation ranges, and `uv run python evaluations/compare_improvements.py` for evidence coverage and timings. Neither script judges semantic answer quality; authored case reviews are in `evaluations/improvements/manual-review.json`. `run_improvement.py` resumes missing cases without retrying recorded failures and rejects changed stage source, questions, index or environment. Do not rerun `run_deepseek.py` over the original evaluation because that older script overwrites its outputs.

The three-stage comparison is complete (108 live attempts). The retained Stage 2 configuration combines symbol retrieval, implementation context and the original prompt with Qwen: 7/18 fully supported answers versus 3/18 before context assembly. The Stage 3 grounding prompt reduced success and caused citation-format rejections, so it was restored to the Stage 2 prompt. Thirty backend tests pass. See `backend/evaluations/improvements/report.md` for semantic errors, format errors, partial answers and limitations; the result is the best measured MVP candidate, not a claim of reliable answers across repositories. Current backend source matches the archived Stage 2 implementation. No further experiment or deployment was performed.

Tests cover chunk boundaries, archive filtering, path traversal, snapshot mismatch, contents endpoints, oversized requests, citations and persistent/IP/concurrency limits. Unit tests mock the model; the explicit live smoke test uses real Ollama embeddings and generation and does not publish a partial index. Evaluation cases are in `backend/evaluations/requests.json`. For another preset, pass a matching JSON fixture using `--cases` to both evaluation scripts; repository mismatches are rejected. Full-index retrieval and browser AI checks must be completed against the final artifact and approved limits.

Validation on 22 September 2026: 22 backend tests, frontend lint and production build pass. Fresh Requests indexing completed: 288 vectors from 96 files, a 5.36 MB indexed bundle, approximately 25 minutes on the local CPU. All three real-model evaluation cases pass the automated content/citation checks. Manual review found that the authentication answer ended in an incomplete code expression despite identifying the correct operation and citing the implementation; answer wording needs refinement before public release. API checks through the Vite proxy verified matching source/index SHA, indexed file contents, stale-snapshot rejection and disabled public questions. No browser was connected for visual verification. Docker execution and production deployment remain unverified.

The local ignored `backend/.env` selects the completed Requests index and keeps all public AI limits at zero, as requested. Restart the local API with:

```sh
uv run --env-file .env uvicorn main:app --host 127.0.0.1 --port 8001
```

Run `npm run dev` from the portfolio root and open `http://127.0.0.1:5173/codebase-demo/`. The source-only setup above still works without `.env`; it intentionally loads the unembedded source bundle.
