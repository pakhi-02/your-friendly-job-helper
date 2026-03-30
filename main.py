"""CLI for local resume tailoring and cover-letter drafting."""
from __future__ import annotations

import argparse
import json
import os
from dataclasses import asdict
from datetime import datetime

from config import (
    CANDIDATE_PROFILE,
    COVER_LETTER_LENGTH,
    COVER_LETTER_TONE,
    OUTPUT_DIR,
)
from cover_letter import (
    CoverLetterGenerator,
    SUPPORTED_LENGTHS,
    SUPPORTED_TONES,
    normalize_length,
    normalize_tone,
)
from document_loader import load_document_text
from llm_client import LocalLLMClient
from resume_tailor import ResumeTailor


def _write_text(path: str, content: str) -> None:
    """Write UTF-8 text file."""
    with open(path, "w", encoding="utf-8") as file:
        file.write(content)


def _safe_slug(value: str, fallback: str) -> str:
    """Build a filesystem-safe file label."""
    cleaned = "".join(ch.lower() if ch.isalnum() else "_" for ch in (value or fallback))
    return "_".join(part for part in cleaned.split("_") if part)[:45] or fallback


def generate_application_documents(
    resume_path: str,
    job_description_path: str,
    company: str,
    role: str,
    output_dir: str = OUTPUT_DIR,
    candidate_name: str | None = None,
    tone: str = COVER_LETTER_TONE,
    length: str = COVER_LETTER_LENGTH,
) -> dict[str, str]:
    """Generate tailored resume notes and a cover letter."""
    resume_text = load_document_text(resume_path)
    job_text = load_document_text(job_description_path)

    llm = LocalLLMClient()
    llm_ok, llm_status = llm.check_health()
    llm_client = llm if llm_ok else None
    selected_tone = normalize_tone(tone)
    selected_length = normalize_length(length)

    tailor = ResumeTailor(llm_client=llm_client)
    analysis = tailor.analyze(resume_text=resume_text, job_description=job_text)

    profile_name = candidate_name or CANDIDATE_PROFILE["name"]
    notes = tailor.build_tailored_resume_notes(
        analysis=analysis,
        candidate_name=profile_name,
        resume_text=resume_text,
        job_description=job_text,
    )

    letter = CoverLetterGenerator(llm_client=llm_client).generate(
        company_name=company,
        role_title=role,
        matched_keywords=analysis.matched_keywords,
        requirement_sentences=analysis.requirement_sentences,
        candidate_name=profile_name,
        resume_text=resume_text,
        job_description=job_text,
        tone=selected_tone,
        length=selected_length,
    )

    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    role_slug = _safe_slug(role, "role")
    company_slug = _safe_slug(company, "company")

    notes_path = os.path.join(output_dir, f"tailored_resume_notes_{role_slug}_{timestamp}.md")
    letter_path = os.path.join(output_dir, f"cover_letter_{company_slug}_{role_slug}_{timestamp}.md")
    analysis_path = os.path.join(output_dir, f"fit_analysis_{company_slug}_{role_slug}_{timestamp}.json")

    _write_text(notes_path, notes)
    _write_text(letter_path, letter)
    _write_text(analysis_path, json.dumps(asdict(analysis), indent=2))

    return {
        "notes_path": notes_path,
        "cover_letter_path": letter_path,
        "analysis_path": analysis_path,
        "match_score": str(analysis.match_score),
        "missing_keywords": ", ".join(analysis.missing_keywords),
        "generation_mode": "llm" if llm_client else "fallback",
        "llm_status": llm_status,
        "tone": selected_tone,
        "length": selected_length,
    }


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Generate tailored resume notes and cover letter from a job description."
    )
    parser.add_argument(
        "--resume-file",
        required=True,
        help="Path to resume (.txt, .md, .pdf, .docx)",
    )
    parser.add_argument(
        "--job-file",
        required=True,
        help="Path to job description (.txt, .md, .pdf, .docx)",
    )
    parser.add_argument("--company", required=True, help="Target company name")
    parser.add_argument("--role", required=True, help="Target role title")
    parser.add_argument("--name", default=None, help="Override candidate name for this run")
    parser.add_argument("--output-dir", default=OUTPUT_DIR, help="Output directory for generated files")
    parser.add_argument(
        "--tone",
        default=normalize_tone(COVER_LETTER_TONE),
        choices=SUPPORTED_TONES,
        help="Cover letter tone style",
    )
    parser.add_argument(
        "--length",
        default=normalize_length(COVER_LETTER_LENGTH),
        choices=SUPPORTED_LENGTHS,
        help="Cover letter length",
    )
    return parser.parse_args()


def main() -> None:
    """Run the local job application assistant."""
    args = parse_args()
    result = generate_application_documents(
        resume_path=args.resume_file,
        job_description_path=args.job_file,
        company=args.company,
        role=args.role,
        output_dir=args.output_dir,
        candidate_name=args.name,
        tone=args.tone,
        length=args.length,
    )

    print("\nApplication materials generated successfully.\n")
    print(f"Match score: {result['match_score']}/100")
    print(f"Resume notes: {result['notes_path']}")
    print(f"Cover letter: {result['cover_letter_path']}")
    print(f"Analysis JSON: {result['analysis_path']}")
    print(f"Missing keywords to add: {result['missing_keywords'] or 'None'}")
    print(f"Cover letter tone: {result['tone']}")
    print(f"Cover letter length: {result['length']}")
    print(f"Generation mode: {result['generation_mode']}")
    if result["generation_mode"] != "llm":
        print(f"LLM status: {result['llm_status']}")
        print("Tip: start Ollama and pull a model to enable LLM generation.")


if __name__ == "__main__":
    main()
