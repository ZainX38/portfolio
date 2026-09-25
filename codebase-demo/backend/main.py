from contextlib import asynccontextmanager
import os
import logging
import sqlite3
from uuid import UUID, uuid4

import httpx
from fastapi import FastAPI, HTTPException, Query, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field
from openai import OpenAIError

from config import (
    ANONYMOUS_DAILY_QUESTION_LIMIT, BUNDLE_PATH, CONTEXT_TOKENS, COOKIE_SECURE,
    DAILY_LIMIT, IP_PER_MINUTE, MAX_CONCURRENT, MAX_OUTPUT_TOKENS,
    MAX_QUESTION_CHARS, USAGE_PATH,
)
from llm import index_matches_configuration, provider_configured
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
        app.state.limits = UsageLimits(
            USAGE_PATH, DAILY_LIMIT, IP_PER_MINUTE, MAX_CONCURRENT,
            ANONYMOUS_DAILY_QUESTION_LIMIT,
        )
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
    app.add_middleware(
        CORSMiddleware, allow_origins=origins, allow_credentials=True,
        allow_methods=["GET", "POST"], allow_headers=["Content-Type"],
    )


VISITOR_COOKIE = "codebase_demo_visitor"


def visitor_id(request, response):
    value = request.cookies.get(VISITOR_COOKIE, "")
    try:
        if str(UUID(value, version=4)) != value:
            raise ValueError()
    except (ValueError, AttributeError):
        value = str(uuid4())
    response.set_cookie(
        VISITOR_COOKIE, value, max_age=365 * 24 * 60 * 60, httponly=True,
        secure=COOKIE_SECURE, samesite="none" if COOKIE_SECURE else "lax", path="/",
    )
    return value


def check_snapshot(snapshot_id):
    repository = app.state.repository
    if repository.id != snapshot_id:
        raise HTTPException(409, "The repository snapshot changed. Reload the demo.")
    return repository


@app.get("/api/demo/repository")
def get_repository(request: Request, response: Response):
    repository = app.state.repository
    limits = getattr(app.state, "limits", None)
    visitor = visitor_id(request, response)
    remaining = limits.remaining(visitor) if limits else 0
    ai_available = bool(limits and provider_configured() and index_matches_configuration(repository) and remaining > 0)
    ai_message = ""
    if not repository.embeddings:
        ai_message = "This repository snapshot needs a new AI index. File browsing is available."
    elif not index_matches_configuration(repository):
        ai_message = "This repository needs reindexing with the configured embedding model."
    elif not provider_configured():
        ai_message = "AI questions are not configured on the server."
    elif remaining == 0:
        ai_message = "You have used all three AI questions available today."
    elif not ai_available:
        ai_message = "AI questions are not enabled yet."
    return {
        "repository": repository.snapshot["repository"],
        "commit": repository.snapshot["commit"],
        "branch": repository.snapshot["branch"],
        "snapshot_id": repository.id,
        "ai_available": ai_available,
        "ai_message": ai_message,
        "questions_remaining": remaining,
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
def ask_question(question: Question, request: Request, response: Response):
    repository = check_snapshot(question.snapshot_id)
    limits = getattr(app.state, "limits", None)
    if not limits or not repository.embeddings or not provider_configured():
        raise HTTPException(503, "AI questions are not enabled yet.")
    if not index_matches_configuration(repository):
        raise HTTPException(503, "The repository needs reindexing with the configured embedding model.")
    if len(question.question) > MAX_QUESTION_CHARS:
        raise HTTPException(422, "Question exceeds the configured length limit")
    visitor = visitor_id(request, response)
    remaining = None
    try:
        with limits.reserve(request.client.host if request.client else "unknown", visitor) as reservation:
            def accept_question():
                nonlocal remaining
                remaining = reservation.accept()

            result = answer_question(
                repository, question.question, MAX_OUTPUT_TOKENS,
                before_generation=accept_question,
            )
            if remaining is None:
                remaining = limits.remaining(visitor)
            return {**result, "questions_remaining": remaining}
    except HTTPException:
        raise
    except (httpx.HTTPError, OpenAIError, ValueError, KeyError, sqlite3.Error) as error:
        logging.getLogger(__name__).warning("AI request failed (%s)", type(error).__name__)
        detail = {"message": "The AI service could not answer this question. Please try again later."}
        if remaining is not None:
            detail["questions_remaining"] = remaining
        raise HTTPException(503, detail)


# Optional single-service deployment: API routes take precedence over static files.
static_dir = os.environ.get("DEMO_STATIC_DIR")
if static_dir:
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="portfolio")
