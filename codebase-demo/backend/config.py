import os
import re
from pathlib import Path


def parse_repository(value):
    value = value.strip().removeprefix("https://github.com/").rstrip("/").removesuffix(".git")
    if not re.fullmatch(r"[A-Za-z0-9-]+/[A-Za-z0-9_.-]+", value) or value.split("/")[1] in {".", ".."}:
        raise ValueError("DEMO_REPOSITORY must be a public GitHub HTTPS URL or owner/repository")
    return value.lower()


REPOSITORY = parse_repository(os.environ.get("DEMO_REPOSITORY", "https://github.com/psf/requests"))
REPOSITORY_COMMIT = os.environ.get("DEMO_REPOSITORY_COMMIT", "").strip().lower()
if REPOSITORY_COMMIT and not re.fullmatch(r"[0-9a-f]{40}", REPOSITORY_COMMIT):
    raise ValueError("DEMO_REPOSITORY_COMMIT must be a full 40-character commit SHA")
DATA_DIR = Path(__file__).resolve().parents[1] / "data"
PRESET_DIR = DATA_DIR / REPOSITORY.replace("/", "--") / (REPOSITORY_COMMIT or "default")
BUNDLE_PATH = Path(os.environ.get("DEMO_BUNDLE_PATH", PRESET_DIR / "bundle.json"))
MAX_FILE_BYTES = 200_000
MAX_SOURCE_BYTES = 30_000_000
MAX_ARCHIVE_BYTES = 60_000_000
MAX_FILES = 10_000
MAX_CHUNKS = 20_000

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434").rstrip("/")
ANSWER_MODEL = os.environ.get("OLLAMA_ANSWER_MODEL", "qwen3.5:4b")
EMBEDDING_MODEL = os.environ.get("OLLAMA_EMBEDDING_MODEL", "qwen3-embedding:0.6b")
CONTEXT_TOKENS = int(os.environ.get("OLLAMA_CONTEXT_TOKENS", "4096"))
OLLAMA_TIMEOUT = float(os.environ.get("OLLAMA_TIMEOUT_SECONDS", "180"))
# Public AI stays off until the owner supplies approved resource limits.
DAILY_LIMIT = int(os.environ.get("DEMO_DAILY_LIMIT", "0"))
IP_PER_MINUTE = int(os.environ.get("DEMO_IP_PER_MINUTE", "0"))
MAX_OUTPUT_TOKENS = int(os.environ.get("DEMO_MAX_OUTPUT_TOKENS", "0"))
MAX_QUESTION_CHARS = int(os.environ.get("DEMO_MAX_QUESTION_CHARS", "0"))
MAX_CONCURRENT = int(os.environ.get("DEMO_MAX_CONCURRENT", "0"))
USAGE_PATH = Path(os.environ.get("DEMO_USAGE_PATH", DATA_DIR / "usage.sqlite"))
