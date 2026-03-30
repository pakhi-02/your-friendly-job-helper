"""Resume tailoring logic with LLM-first generation."""
from __future__ import annotations

from dataclasses import dataclass

from config import MAX_INPUT_CHARS
from llm_client import LLMUnavailableError, LocalLLMClient
from local_nlp import (
    extract_keywords,
    extract_requirement_sentences,
    extract_resume_bullets,
    keyword_overlap,
)


@dataclass
class ResumeAnalysis:
    """Structured result from resume-vs-job analysis."""

    match_score: int
    top_job_keywords: list[str]
    matched_keywords: list[str]
    missing_keywords: list[str]
    requirement_sentences: list[str]
    original_bullets: list[str]
    bullet_suggestions: list[str]


class ResumeTailor:
    """Builds resume tailoring suggestions for a target job."""

    def __init__(self, llm_client: LocalLLMClient | None = None) -> None:
        self.llm_client = llm_client

    def analyze(self, resume_text: str, job_description: str) -> ResumeAnalysis:
        """Analyze resume fit against a given job description."""
        top_keywords = extract_keywords(job_description, top_n=25)
        matched, missing = keyword_overlap(resume_text, top_keywords)

        denominator = max(len(top_keywords), 1)
        match_score = int((len(matched) / denominator) * 100)

        requirements = extract_requirement_sentences(job_description, limit=8)
        bullets = extract_resume_bullets(resume_text, limit=8)
        suggestions = self._suggest_bullet_improvements(bullets, missing)

        return ResumeAnalysis(
            match_score=match_score,
            top_job_keywords=top_keywords,
            matched_keywords=matched,
            missing_keywords=missing[:12],
            requirement_sentences=requirements,
            original_bullets=bullets,
            bullet_suggestions=suggestions,
        )

    def _suggest_bullet_improvements(
        self, bullets: list[str], missing_keywords: list[str]
    ) -> list[str]:
        """Create concrete rewrite prompts for resume bullets."""
        if not bullets:
            return [
                "Add at least 4 quantified bullets in your experience section.",
                "Use action verbs + scope + measurable outcome in each bullet.",
            ]

        suggestions: list[str] = []
        for idx, bullet in enumerate(bullets[:5]):
            keyword = missing_keywords[idx] if idx < len(missing_keywords) else "impact"
            stripped = bullet.lstrip("-*• ").strip()
            suggestions.append(
                f'Original: "{stripped}"\n'
                f'Suggested rewrite: "Expanded {keyword}-related work by [action], resulting in [measurable result]."'
            )
        return suggestions

    def build_tailored_resume_notes(
        self,
        analysis: ResumeAnalysis,
        candidate_name: str = "Candidate",
        resume_text: str = "",
        job_description: str = "",
    ) -> str:
        """Create markdown notes to help tailor resume quickly."""
        if self.llm_client:
            try:
                return self._build_tailored_notes_with_llm(
                    analysis=analysis,
                    candidate_name=candidate_name,
                    resume_text=resume_text,
                    job_description=job_description,
                )
            except LLMUnavailableError:
                pass
        return self._build_tailored_notes_fallback(analysis, candidate_name)

    def _build_tailored_notes_fallback(
        self, analysis: ResumeAnalysis, candidate_name: str
    ) -> str:
        """Create deterministic markdown notes without LLM."""
        summary_keywords = ", ".join(analysis.top_job_keywords[:6]) or "relevant technologies"
        matched_text = ", ".join(analysis.matched_keywords[:12]) or "None yet"
        missing_text = ", ".join(analysis.missing_keywords) or "None"

        requirement_lines = "\n".join(
            f"- {line}" for line in analysis.requirement_sentences
        ) or "- No explicit requirement statements detected."

        bullet_lines = "\n\n".join(f"{idx+1}. {item}" for idx, item in enumerate(analysis.bullet_suggestions))

        return f"""# Tailored Resume Notes

## Candidate
{candidate_name}

## Fit Snapshot
- Match score (heuristic): **{analysis.match_score}/100**
- Matched keywords: {matched_text}
- Missing keywords to include: {missing_text}

## Suggested Professional Summary
`Results-focused professional with hands-on experience in {summary_keywords}. Proven ability to deliver measurable business impact, collaborate cross-functionally, and adapt quickly to new tools and requirements.`

## Job Requirements To Mirror
{requirement_lines}

## Experience Bullet Rewrite Ideas
{bullet_lines}

## Final Resume Checklist
- Add 6-10 keywords from the job description naturally in summary, skills, and bullets.
- Keep bullet format: action verb + technical detail + measurable outcome.
- Prioritize recent projects that match the role's top requirements.
- Keep resume to one page if early-career, two pages if experienced.
"""

    def _build_tailored_notes_with_llm(
        self,
        analysis: ResumeAnalysis,
        candidate_name: str,
        resume_text: str,
        job_description: str,
    ) -> str:
        """Generate tailored resume guidance with local LLM."""
        system_prompt = (
            "You are an expert resume coach. Produce concise, ATS-friendly, practical guidance in markdown."
        )
        prompt = f"""
Candidate name: {candidate_name}

Heuristic fit summary:
- match_score: {analysis.match_score}
- matched_keywords: {", ".join(analysis.matched_keywords[:15]) or "none"}
- missing_keywords: {", ".join(analysis.missing_keywords[:15]) or "none"}
- requirement_sentences: {analysis.requirement_sentences[:6]}

Resume text:
{resume_text[:MAX_INPUT_CHARS]}

Job description:
{job_description[:MAX_INPUT_CHARS]}

Write markdown using exactly these sections:
1) # Tailored Resume Notes
2) ## Fit Snapshot
3) ## ATS Keywords To Add Naturally
4) ## Professional Summary Rewrite
5) ## Experience Bullet Rewrites
6) ## Project Section Improvements
7) ## Final Checklist

Requirements:
- Keep it concrete and actionable.
- In bullet rewrites, provide 5 before/after style rewrites where possible.
- Do not invent employer names not present in the resume.
- Keep total length under 700 words.
"""
        text = self.llm_client.generate(prompt=prompt, system_prompt=system_prompt)
        return text.strip()
