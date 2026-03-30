"""Cover letter generator based on job description and resume analysis."""
from __future__ import annotations

from datetime import datetime

from config import CANDIDATE_PROFILE, MAX_INPUT_CHARS
from llm_client import LLMUnavailableError, LocalLLMClient

SUPPORTED_TONES = ("formal", "concise", "startup")
SUPPORTED_LENGTHS = ("short", "medium", "long")


def normalize_tone(tone: str | None) -> str:
    """Normalize tone values to supported options."""
    normalized = (tone or "").strip().lower()
    if normalized in SUPPORTED_TONES:
        return normalized
    return "formal"


def normalize_length(length: str | None) -> str:
    """Normalize length values to supported options."""
    normalized = (length or "").strip().lower()
    if normalized in SUPPORTED_LENGTHS:
        return normalized
    return "medium"


class CoverLetterGenerator:
    """Build a reusable cover letter draft."""

    def __init__(self, llm_client: LocalLLMClient | None = None) -> None:
        self.llm_client = llm_client

    def generate(
        self,
        company_name: str,
        role_title: str,
        matched_keywords: list[str],
        requirement_sentences: list[str],
        candidate_name: str | None = None,
        resume_text: str = "",
        job_description: str = "",
        tone: str = "formal",
        length: str = "medium",
    ) -> str:
        """Return a markdown cover letter draft."""
        selected_tone = normalize_tone(tone)
        selected_length = normalize_length(length)
        if self.llm_client:
            try:
                return self._generate_with_llm(
                    company_name=company_name,
                    role_title=role_title,
                    matched_keywords=matched_keywords,
                    requirement_sentences=requirement_sentences,
                    candidate_name=candidate_name,
                    resume_text=resume_text,
                    job_description=job_description,
                    tone=selected_tone,
                    length=selected_length,
                )
            except LLMUnavailableError:
                pass

        return self._generate_fallback(
            company_name=company_name,
            role_title=role_title,
            matched_keywords=matched_keywords,
            requirement_sentences=requirement_sentences,
            candidate_name=candidate_name,
            tone=selected_tone,
            length=selected_length,
        )

    def _generate_fallback(
        self,
        company_name: str,
        role_title: str,
        matched_keywords: list[str],
        requirement_sentences: list[str],
        candidate_name: str | None = None,
        tone: str = "formal",
        length: str = "medium",
    ) -> str:
        """Template-driven fallback when LLM is unavailable."""
        name = candidate_name or CANDIDATE_PROFILE["name"]
        today = datetime.now().strftime("%B %d, %Y")
        keyword_text = ", ".join(matched_keywords[:6]) or "relevant technical and collaboration skills"
        requirement_text = requirement_sentences[0] if requirement_sentences else (
            "the role's requirements and expected impact"
        )
        tone_intro, tone_body, tone_close = self._fallback_tone_snippets(tone)
        detail_paragraph = self._fallback_length_paragraph(length, company_name, role_title)

        contact_lines = [
            name,
            CANDIDATE_PROFILE.get("email", ""),
            CANDIDATE_PROFILE.get("phone", ""),
            CANDIDATE_PROFILE.get("location", ""),
            CANDIDATE_PROFILE.get("linkedin", ""),
            CANDIDATE_PROFILE.get("portfolio", ""),
        ]
        contact_block = "\n".join(line for line in contact_lines if line)

        return f"""# Cover Letter Draft

{contact_block}

{today}

Hiring Manager  
{company_name}

Dear Hiring Manager,

I am excited to apply for the {role_title} position at {company_name}. {tone_intro} My background aligns closely with your needs in {keyword_text}.

In my recent work, I have delivered projects that required technical ownership, cross-functional collaboration, and measurable business results. I noticed your job description emphasizes "{requirement_text}" and {tone_body}

{detail_paragraph}

{tone_close} Thank you for your time and consideration.

Sincerely,  
{name}
"""

    def _generate_with_llm(
        self,
        company_name: str,
        role_title: str,
        matched_keywords: list[str],
        requirement_sentences: list[str],
        candidate_name: str | None,
        resume_text: str,
        job_description: str,
        tone: str,
        length: str,
    ) -> str:
        """Generate a role-specific cover letter using local LLM."""
        name = candidate_name or CANDIDATE_PROFILE["name"]
        min_words, max_words = self._length_word_range(length)
        contact_lines = [
            name,
            CANDIDATE_PROFILE.get("email", ""),
            CANDIDATE_PROFILE.get("phone", ""),
            CANDIDATE_PROFILE.get("location", ""),
            CANDIDATE_PROFILE.get("linkedin", ""),
            CANDIDATE_PROFILE.get("portfolio", ""),
        ]
        contact_block = "\n".join(line for line in contact_lines if line)
        system_prompt = (
            "You are an expert career writer creating tailored, truthful cover letters."
        )
        prompt = f"""
Write a tailored cover letter in markdown for:
- Candidate: {name}
- Company: {company_name}
- Role: {role_title}
- Matched keywords: {", ".join(matched_keywords[:10]) or "none"}
- Requirement hints: {requirement_sentences[:5]}

Candidate profile block:
{contact_block}

Resume text:
{resume_text[:MAX_INPUT_CHARS]}

Job description:
{job_description[:MAX_INPUT_CHARS]}

Constraints:
- Output only markdown cover letter text.
- Start with '# Cover Letter Draft'
- Keep {min_words}-{max_words} words.
- Use a {tone} tone.
- Keep language confident and human, not generic.
- Avoid fake claims; only use evidence hinted in resume text.
- End with Sincerely and candidate name.
"""
        return self.llm_client.generate(prompt=prompt, system_prompt=system_prompt).strip()

    def _fallback_tone_snippets(self, tone: str) -> tuple[str, str, str]:
        """Return tone-specific snippets for fallback template."""
        if tone == "concise":
            return (
                "I value clear ownership, fast execution, and measurable outcomes.",
                "I can bring immediate impact in that area.",
                "I would welcome a brief conversation about how I can help your team deliver results.",
            )
        if tone == "startup":
            return (
                "I am motivated by high-velocity teams building meaningful products.",
                "I can quickly ramp up, collaborate tightly, and ship practical improvements early.",
                "I would love to discuss how I can contribute hands-on from day one.",
            )
        return (
            "I am particularly interested in contributing to a team with strong execution standards.",
            "I am confident I can contribute effectively in that area.",
            "I would welcome the opportunity to discuss how my background and execution style can support your goals.",
        )

    def _fallback_length_paragraph(
        self, length: str, company_name: str, role_title: str
    ) -> str:
        """Return a length-specific supporting paragraph."""
        if length == "short":
            return "I am excited to contribute quickly and effectively in this role."
        if length == "long":
            return (
                f"I am particularly interested in how {company_name} approaches delivery and impact in the {role_title} function. "
                "I bring a practical, outcomes-focused approach: understanding priorities quickly, partnering with stakeholders, "
                "and translating requirements into reliable execution. I am motivated by environments where ownership, collaboration, "
                "and measurable outcomes are equally important."
            )
        return (
            "I am motivated by teams that value ownership, thoughtful execution, and measurable outcomes, "
            "and I am eager to bring that mindset to this opportunity."
        )

    def _length_word_range(self, length: str) -> tuple[int, int]:
        """Return target word range for LLM generation."""
        if length == "short":
            return (140, 210)
        if length == "long":
            return (320, 450)
        return (230, 330)
