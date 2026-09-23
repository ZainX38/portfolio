from contextlib import asynccontextmanager
import os
import logging
import sqlite3

import httpx
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from config import (
    BUNDLE_PATH, CONTEXT_TOKENS, DAILY_LIMIT, EMBEDDING_MODEL, IP_PER_MINUTE,
    MAX_CONCURRENT, MAX_OUTPUT_TOKENS, MAX_QUESTION_CHARS, USAGE_PATH,
)
from limits import UsageLimits
from rag import answer_question
from repository import Repository


@asynccontextmanager
async def lifespan(app):
    # Startup fails if the deployment artifact is missing or inconsistent.
    # Requests never fetch a newer repository or rebuild an index.
    app.state.repository = Repository.load(BUNDLE_PATH)
    app.state.limits = None
    if all(value > 0 for value in (DAILY_LIMIT, IP_PER_MINUTE, MAX_CONCURRENT, MAX_OUTPUT_TOKENS, MAX_QUESTION_CHARS)):
        if MAX_OUTPUT_TOKENS + 1536 >= CONTEXT_TOKENS:
            raise ValueError("Output limit must leave room for repository context")
        app.state.limits = UsageLimits(USAGE_PATH, DAILY_LIMIT, IP_PER_MINUTE, MAX_CONCURRENT)
    yield


app = FastAPI(title="Codebase AI portfolio demo", lifespan=lifespan)


@app.middleware("http")
async def bound_question_body(request: Request, call_next):
    if request.url.path == "/api/demo/ask":
        body = bytearray()
        async for block in request.stream():
            body.extend(block)
            if len(body) > 8192:
                return JSONResponse({"detail": "Question request is too large"}, status_code=413)
        request._body = bytes(body)
    return await call_next(request)


origins = [origin.strip() for origin in os.environ.get("DEMO_ALLOWED_ORIGINS", "").split(",") if origin.strip()]
if origins:
    app.add_middleware(CORSMiddleware, allow_origins=origins, allow_methods=["GET", "POST"], allow_headers=["Content-Type"])


def check_snapshot(snapshot_id):
    repository = app.state.repository
    if repository.id != snapshot_id:
        raise HTTPException(409, "The repository snapshot changed. Reload the demo.")
    return repository


@app.get("/api/demo/repository")
def get_repository():
    repository = app.state.repository
    ai_available = bool(getattr(app.state, "limits", None) and repository.embeddings and repository.embeddings["model"] == EMBEDDING_MODEL)
    ai_message = ""
    if not repository.embeddings:
        ai_message = "This repository snapshot needs a new AI index. File browsing is available."
    elif repository.embeddings["model"] != EMBEDDING_MODEL:
        ai_message = "This repository needs reindexing with the configured embedding model."
    elif not ai_available:
        ai_message = "AI questions are not enabled yet."
    return {
        "repository": repository.snapshot["repository"],
        "commit": repository.snapshot["commit"],
        "branch": repository.snapshot["branch"],
        "snapshot_id": repository.id,
        "ai_available": ai_available,
        "ai_message": ai_message,
        "max_question_chars": MAX_QUESTION_CHARS,
        "coverage": {
            "scope": repository.coverage["scope"] if repository.coverage else "none",
            "indexed_files": len(repository.indexed_paths) if repository.embeddings else 0,
            "total_files": len(repository.files),
        },
    }


@app.get("/api/demo/contents")
def get_contents(snapshot_id: str, path: str = Query(default="", max_length=1000)):
    repository = check_snapshot(snapshot_id)
    try:
        return repository.contents(path)
    except KeyError:
        raise HTTPException(404, "Repository path not found")
    except ValueError as error:
        raise HTTPException(415, str(error))


@app.get("/api/demo/coverage")
def get_coverage(snapshot_id: str):
    repository = check_snapshot(snapshot_id)
    return repository.coverage or {"scope": "none", "indexed_paths": [], "excluded": {path: "AI index is not ready" for path in repository.files}}


class Question(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    question: str = Field(min_length=1, max_length=MAX_QUESTION_CHARS or 1000)
    snapshot_id: str = Field(min_length=64, max_length=64)


@app.post("/api/demo/ask")
def ask_question(question: Question, request: Request):
    repository = check_snapshot(question.snapshot_id)
    limits = getattr(app.state, "limits", None)
    if not limits or not repository.embeddings:
        raise HTTPException(503, "AI questions are not enabled yet.")
    if len(question.question) > MAX_QUESTION_CHARS:
        raise HTTPException(422, "Question exceeds the configured length limit")
    try:
        with limits.reserve(request.client.host if request.client else "unknown"):
            return answer_question(repository, question.question, MAX_OUTPUT_TOKENS)
    except HTTPException:
        raise
    except (httpx.HTTPError, ValueError, KeyError, sqlite3.Error):
        logging.getLogger(__name__).warning("AI request failed", exc_info=True)
        raise HTTPException(503, "The AI service could not answer this question. Please try again later.")


# Optional single-service deployment: API routes take precedence over static files.
static_dir = os.environ.get("DEMO_STATIC_DIR")
if static_dir:
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="portfolio")
