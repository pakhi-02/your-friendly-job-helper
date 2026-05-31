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

# --- Web server settings (used by `python web_app.py`) ---
FLASK_HOST = os.getenv("FLASK_HOST", "127.0.0.1")
FLASK_PORT = int(os.getenv("FLASK_PORT", "5000"))
FLASK_DEBUG = _env_bool("FLASK_DEBUG", False)

# HTTP Basic Auth for the web app. Leave APP_PASSWORD empty to disable auth
# (fine for localhost); set it before hosting so the app isn't open to the world.
APP_USERNAME = os.getenv("APP_USERNAME", "admin")
APP_PASSWORD = os.getenv("APP_PASSWORD", "")

# --- Auto-apply (browser automation) settings ---
# AUTO_SUBMIT=false (default) -> fill the form, screenshot it, and STOP so you can
# review and click submit yourself. Flip to true only once you trust the output.
AUTO_SUBMIT = _env_bool("AUTO_SUBMIT", False)
# HEADLESS=false shows the browser so you can watch / take over. true runs hidden.
APPLY_HEADLESS = _env_bool("APPLY_HEADLESS", False)
# Default resume file used when applying (can be overridden per run on the CLI).
APPLY_RESUME_FILE = os.getenv("APPLY_RESUME_FILE", "")
APPLY_SCREENSHOT_DIR = os.getenv("APPLY_SCREENSHOT_DIR", "application_docs/screenshots")
# Slow down each action (ms) so pages with JS validation keep up. 0 = full speed.
APPLY_SLOW_MO_MS = int(os.getenv("APPLY_SLOW_MO_MS", "150"))

# Canned answers for the common required questions ATS forms ask. These are used
# verbatim so a small local model never has to guess on legally meaningful fields.
APPLY_DEFAULTS = {
    "work_authorization": os.getenv("APPLY_WORK_AUTHORIZED", "Yes"),
    "require_sponsorship": os.getenv("APPLY_NEEDS_SPONSORSHIP", "No"),
    "gender": os.getenv("APPLY_GENDER", "Decline To Self Identify"),
    "race": os.getenv("APPLY_RACE", "Decline To Self Identify"),
    "veteran": os.getenv("APPLY_VETERAN", "I don't wish to answer"),
    "disability": os.getenv("APPLY_DISABILITY", "I don't wish to answer"),
    "salary": os.getenv("APPLY_SALARY_EXPECTATION", ""),
    "start_date": os.getenv("APPLY_START_DATE", "Immediately"),
}

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
