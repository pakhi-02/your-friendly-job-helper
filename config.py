"""Configuration for the local job-application assistant."""
import os
from dotenv import load_dotenv

load_dotenv()


def _env_bool(name: str, default: bool = False) -> bool:
    """Read a boolean environment variable."""
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}

CANDIDATE_PROFILE = {
    "name": os.getenv("CANDIDATE_NAME", "Job Seeker"),
    "email": os.getenv("CANDIDATE_EMAIL", ""),
    "phone": os.getenv("CANDIDATE_PHONE", ""),
    "location": os.getenv("CANDIDATE_LOCATION", ""),
    "linkedin": os.getenv("CANDIDATE_LINKEDIN", ""),
    "portfolio": os.getenv("CANDIDATE_PORTFOLIO", ""),
}

OUTPUT_DIR = os.getenv("OUTPUT_DIR", "application_docs")
TOP_KEYWORDS = int(os.getenv("TOP_KEYWORDS", "20"))
MIN_KEYWORD_LENGTH = int(os.getenv("MIN_KEYWORD_LENGTH", "3"))
MAX_INPUT_CHARS = int(os.getenv("MAX_INPUT_CHARS", "12000"))

# LLM settings (local by default via Ollama)
USE_LLM = _env_bool("USE_LLM", True)
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
LLM_TIMEOUT_SECONDS = int(os.getenv("LLM_TIMEOUT_SECONDS", "120"))
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.3"))
COVER_LETTER_TONE = os.getenv("COVER_LETTER_TONE", "formal")
COVER_LETTER_LENGTH = os.getenv("COVER_LETTER_LENGTH", "medium")

STOPWORDS = {
    "about",
    "after",
    "again",
    "also",
    "an",
    "and",
    "any",
    "are",
    "been",
    "but",
    "can",
    "for",
    "from",
    "has",
    "have",
    "into",
    "its",
    "our",
    "that",
    "the",
    "their",
    "them",
    "they",
    "this",
    "with",
    "will",
    "you",
    "your",
    "years",
    "year",
    "work",
    "team",
    "role",
    "job",
    "using",
    "strong",
    "experience",
    "skills",
    "required",
    "requirements",
    "must",
    "looking",
    "seeking",
    "ability",
    "responsibilities",
    "qualification",
    "qualifications",
}
