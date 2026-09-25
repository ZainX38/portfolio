"""Small generation/embedding adapter for OpenAI production and local Ollama."""

import json
import math

import httpx
from openai import OpenAI

from config import (
    AI_TIMEOUT, ANSWER_MODEL, CONTEXT_TOKENS, EMBEDDING_MODEL, OLLAMA_URL,
    OPENAI_API_KEY, PROVIDER,
)


ANSWER_SCHEMA = {
    "type": "object",
    "properties": {
        "answer": {"type": "string"},
        "citations": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["answer", "citations"],
    "additionalProperties": False,
}


def provider_configured():
    return PROVIDER != "openai" or bool(OPENAI_API_KEY)


def embedding_provider(index):
    # Bundles created before provider metadata existed are Ollama indexes.
    return index.get("provider", "ollama")


def index_matches_configuration(repository):
    return bool(
        repository.embeddings
        and embedding_provider(repository.embeddings) == PROVIDER
        and repository.embeddings["model"] == EMBEDDING_MODEL
    )


def _openai_client():
    if not OPENAI_API_KEY:
        raise ValueError("OpenAI is not configured")
    return OpenAI(api_key=OPENAI_API_KEY, timeout=AI_TIMEOUT, max_retries=0)


def model_digest(model):
    if PROVIDER == "openai":
        return f"openai:{model}"
    response = httpx.get(f"{OLLAMA_URL}/api/tags", timeout=10, trust_env=False)
    response.raise_for_status()
    for item in response.json()["models"]:
        if item["name"] == model:
            return item["digest"]
    raise ValueError(f"Required Ollama model is not installed: {model}")


def embed(texts, keep_alive=0):
    if PROVIDER == "openai":
        response = _openai_client().embeddings.create(
            model=EMBEDDING_MODEL,
            input=texts,
            encoding_format="float",
        )
        vectors = [item.embedding for item in response.data]
    else:
        response = httpx.post(f"{OLLAMA_URL}/api/embed", json={
            "model": EMBEDDING_MODEL,
            "input": texts,
            "truncate": False,
            "keep_alive": keep_alive,
        }, timeout=AI_TIMEOUT, trust_env=False)
        response.raise_for_status()
        vectors = response.json()["embeddings"]
    if len(vectors) != len(texts):
        raise ValueError("Embedding provider returned an unexpected embedding count")
    for vector in vectors:
        if not vector or not all(isinstance(value, (int, float)) and math.isfinite(value) for value in vector):
            raise ValueError("Invalid embedding vector")
    return vectors


def generate(messages, max_output_tokens):
    if PROVIDER == "openai":
        instructions = "\n".join(message["content"] for message in messages if message["role"] == "system")
        model_input = "\n".join(message["content"] for message in messages if message["role"] != "system")
        response = _openai_client().responses.create(
            model=ANSWER_MODEL,
            instructions=instructions,
            input=model_input,
            max_output_tokens=max_output_tokens,
            reasoning={"effort": "none"},
            text={
                "verbosity": "low",
                "format": {
                    "type": "json_schema",
                    "name": "repository_answer",
                    "strict": True,
                    "schema": ANSWER_SCHEMA,
                },
            },
            store=False,
        )
        if response.status == "incomplete":
            raise ValueError("The answer exceeded the output limit; try a narrower question")
        return json.loads(response.output_text)

    response = httpx.post(f"{OLLAMA_URL}/api/chat", json={
        "model": ANSWER_MODEL,
        "messages": messages,
        "stream": False,
        "think": False,
        "format": ANSWER_SCHEMA,
        "keep_alive": 0,
        "options": {"num_ctx": CONTEXT_TOKENS, "num_predict": max_output_tokens, "temperature": 0},
    }, timeout=AI_TIMEOUT, trust_env=False)
    response.raise_for_status()
    data = response.json()
    if data.get("done_reason") == "length":
        raise ValueError("The answer exceeded the output limit; try a narrower question")
    return json.loads(data["message"]["content"])
