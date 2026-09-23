"""The only module that knows Ollama's HTTP interface."""

import json
import math

import httpx

from config import ANSWER_MODEL, CONTEXT_TOKENS, EMBEDDING_MODEL, OLLAMA_TIMEOUT, OLLAMA_URL


def model_digest(model):
    response = httpx.get(f"{OLLAMA_URL}/api/tags", timeout=10, trust_env=False)
    response.raise_for_status()
    for item in response.json()["models"]:
        if item["name"] == model:
            return item["digest"]
    raise ValueError(f"Required Ollama model is not installed: {model}")


def embed(texts, keep_alive=0):
    response = httpx.post(f"{OLLAMA_URL}/api/embed", json={
        "model": EMBEDDING_MODEL,
        "input": texts,
        "truncate": False,
        "keep_alive": keep_alive,
    }, timeout=OLLAMA_TIMEOUT, trust_env=False)
    response.raise_for_status()
    vectors = response.json()["embeddings"]
    if len(vectors) != len(texts):
        raise ValueError("Ollama returned an unexpected embedding count")
    for vector in vectors:
        if not vector or not all(isinstance(value, (int, float)) and math.isfinite(value) for value in vector):
            raise ValueError("Invalid embedding vector")
    return vectors


def generate(messages, max_output_tokens):
    schema = {
        "type": "object",
        "properties": {
            "answer": {"type": "string"},
            "citations": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["answer", "citations"],
        "additionalProperties": False,
    }
    response = httpx.post(f"{OLLAMA_URL}/api/chat", json={
        "model": ANSWER_MODEL,
        "messages": messages,
        "stream": False,
        "think": False,
        "format": schema,
        "keep_alive": 0,
        "options": {"num_ctx": CONTEXT_TOKENS, "num_predict": max_output_tokens, "temperature": 0},
    }, timeout=OLLAMA_TIMEOUT, trust_env=False)
    response.raise_for_status()
    data = response.json()
    if data.get("done_reason") == "length":
        raise ValueError("The answer exceeded the output limit; try a narrower question")
    return json.loads(data["message"]["content"])
