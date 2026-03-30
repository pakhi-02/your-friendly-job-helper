"""Small local NLP helpers for resume tailoring."""
from __future__ import annotations

import re
from collections import Counter
from typing import Iterable

from config import MIN_KEYWORD_LENGTH, STOPWORDS, TOP_KEYWORDS

REQUIREMENT_MARKERS = (
    "must",
    "required",
    "requirements",
    "responsibilities",
    "qualification",
    "qualifications",
    "need",
    "seeking",
    "looking for",
    "proficient",
    "familiar",
)


def clean_text(text: str) -> str:
    """Normalize whitespace and lowercase text."""
    return re.sub(r"\s+", " ", text or "").strip().lower()


def tokenize_words(text: str) -> list[str]:
    """Extract basic word tokens."""
    return re.findall(r"[a-zA-Z][a-zA-Z0-9\-\+]{1,}", text.lower())


def extract_keywords(
    text: str,
    top_n: int = TOP_KEYWORDS,
    min_length: int = MIN_KEYWORD_LENGTH,
    extra_stopwords: Iterable[str] | None = None,
) -> list[str]:
    """Return top keywords from text using frequency rules."""
    if not text:
        return []

    blocked = set(STOPWORDS)
    if extra_stopwords:
        blocked.update(w.lower() for w in extra_stopwords)

    tokens = [
        token
        for token in tokenize_words(text)
        if len(token) >= min_length and token not in blocked and not token.isdigit()
    ]
    if not tokens:
        return []

    counts = Counter(tokens)
    return [word for word, _ in counts.most_common(top_n)]


def extract_requirement_sentences(job_description: str, limit: int = 10) -> list[str]:
    """Pull requirement-focused sentences from a job description."""
    if not job_description:
        return []

    raw_sentences = re.split(r"(?<=[.!?])\s+|\n+", job_description.strip())
    selected = []
    for sentence in raw_sentences:
        sentence_clean = sentence.strip()
        if not sentence_clean:
            continue
        lowered = sentence_clean.lower()
        if any(marker in lowered for marker in REQUIREMENT_MARKERS):
            selected.append(sentence_clean)
        if len(selected) >= limit:
            break
    return selected


def keyword_overlap(source_text: str, keywords: list[str]) -> tuple[list[str], list[str]]:
    """Return matched and missing keywords from source text."""
    normalized = clean_text(source_text)
    matched = [word for word in keywords if word in normalized]
    missing = [word for word in keywords if word not in normalized]
    return matched, missing


def extract_resume_bullets(resume_text: str, limit: int = 12) -> list[str]:
    """Extract bullet-style lines from plain-text resume."""
    bullets = []
    for line in (resume_text or "").splitlines():
        line_clean = line.strip()
        if re.match(r"^(\-|\*|•|\d+\.)\s+", line_clean):
            bullets.append(line_clean)
        if len(bullets) >= limit:
            break
    return bullets
