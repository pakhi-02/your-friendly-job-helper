"""Interactive mode for generating application docs without CLI flags."""
from __future__ import annotations

from config import (
    CANDIDATE_PROFILE,
    COVER_LETTER_LENGTH,
    COVER_LETTER_TONE,
    OUTPUT_DIR,
)
from cover_letter import (
    SUPPORTED_LENGTHS,
    SUPPORTED_TONES,
    normalize_length,
    normalize_tone,
)
from main import generate_application_documents


def _prompt(label: str, default: str = "") -> str:
    """Prompt with optional default value."""
    suffix = f" [{default}]" if default else ""
    value = input(f"{label}{suffix}: ").strip()
    return value or default


def main() -> None:
    """Run prompt-driven workflow."""
    print("\nLocal Job Application Assistant (LLM + fallback)\n")
    resume_path = _prompt("Resume file path (.txt/.md/.pdf/.docx)")
    job_path = _prompt("Job description file path (.txt/.md/.pdf/.docx)")
    company = _prompt("Company name")
    role = _prompt("Role title")
    name = _prompt("Candidate name", CANDIDATE_PROFILE["name"])
    tone = _prompt(
        f"Cover letter tone ({'/'.join(SUPPORTED_TONES)})",
        normalize_tone(COVER_LETTER_TONE),
    )
    length = _prompt(
        f"Cover letter length ({'/'.join(SUPPORTED_LENGTHS)})",
        normalize_length(COVER_LETTER_LENGTH),
    )
    output_dir = _prompt("Output directory", OUTPUT_DIR)

    result = generate_application_documents(
        resume_path=resume_path,
        job_description_path=job_path,
        company=company,
        role=role,
        output_dir=output_dir,
        candidate_name=name,
        tone=tone,
        length=length,
    )

    print("\nDone.")
    print(f"Match score: {result['match_score']}/100")
    print(f"Resume notes: {result['notes_path']}")
    print(f"Cover letter: {result['cover_letter_path']}")
    print(f"Analysis JSON: {result['analysis_path']}")
    print(f"Cover letter tone: {result['tone']}")
    print(f"Cover letter length: {result['length']}")
    print(f"Generation mode: {result['generation_mode']}")


if __name__ == "__main__":
    main()
