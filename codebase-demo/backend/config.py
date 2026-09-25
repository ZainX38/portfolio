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
PROVIDER = os.environ.get("DEMO_AI_PROVIDER", "openai").strip().lower()
if PROVIDER not in {"openai", "ollama"}:
    raise ValueError("DEMO_AI_PROVIDER must be openai or ollama")

# This is the only environment variable from which the server reads an OpenAI key.
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "").strip()
OPENAI_GENERATION_MODEL = os.environ.get("OPENAI_GENERATION_MODEL", "gpt-6-luna").strip()
OPENAI_EMBEDDING_MODEL = os.environ.get("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small").strip()
OLLAMA_ANSWER_MODEL = os.environ.get("OLLAMA_ANSWER_MODEL", "qwen3.5:4b").strip()
OLLAMA_EMBEDDING_MODEL = os.environ.get("OLLAMA_EMBEDDING_MODEL", "qwen3-embedding:0.6b").strip()

ANSWER_MODEL = OPENAI_GENERATION_MODEL if PROVIDER == "openai" else OLLAMA_ANSWER_MODEL
EMBEDDING_MODEL = OPENAI_EMBEDDING_MODEL if PROVIDER == "openai" else OLLAMA_EMBEDDING_MODEL
CONTEXT_TOKENS = int(os.environ.get("DEMO_CONTEXT_TOKENS", os.environ.get("OLLAMA_CONTEXT_TOKENS", "4096")))
AI_TIMEOUT = float(os.environ.get("DEMO_AI_TIMEOUT_SECONDS", os.environ.get("OLLAMA_TIMEOUT_SECONDS", "180")))

# Small, predictable public-demo defaults. The anonymous allowance is deliberately
# fixed at three per UTC day; authentication would be required for a stronger identity guarantee.
ANONYMOUS_DAILY_QUESTION_LIMIT = 3
DAILY_LIMIT = int(os.environ.get("DEMO_DAILY_LIMIT", "100"))
IP_PER_MINUTE = int(os.environ.get("DEMO_IP_PER_MINUTE", "3"))
MAX_OUTPUT_TOKENS = int(os.environ.get("DEMO_MAX_OUTPUT_TOKENS", "400"))
MAX_QUESTION_CHARS = int(os.environ.get("DEMO_MAX_QUESTION_CHARS", "500"))
MAX_CONCURRENT = int(os.environ.get("DEMO_MAX_CONCURRENT", "2"))
RETRIEVAL_COUNT = int(os.environ.get("DEMO_RETRIEVAL_COUNT", "5"))
COOKIE_SECURE = os.environ.get("DEMO_COOKIE_SECURE", "false").strip().lower() in {"1", "true", "yes"}
USAGE_PATH = Path(os.environ.get("DEMO_USAGE_PATH", DATA_DIR / "usage.sqlite"))
