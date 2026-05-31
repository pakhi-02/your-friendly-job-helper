"""Auto-apply: drive a job application form in the browser.

Strategy that works across many sites (not just one ATS): open the page,
introspect every visible form field, read each field's label, then fill it from
the candidate profile (known fields) or the local LLM (free-text / choice
questions). By default it fills + screenshots + STOPS for human review; set
AUTO_SUBMIT=true to also click the submit button.

Run:
    python auto_apply.py --url <application_url> \
        --resume-file resume.pdf \
        --cover-letter-file application_docs/cover_letter_*.md \
        --company "Acme Inc" --role "Software Engineer"
"""
from __future__ import annotations

import argparse
import os
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from config import (
    APPLY_DEFAULTS,
    APPLY_HEADLESS,
    APPLY_RESUME_FILE,
    APPLY_SCREENSHOT_DIR,
    APPLY_SLOW_MO_MS,
    AUTO_SUBMIT,
    CANDIDATE_PROFILE,
)
from document_loader import load_document_text
from llm_client import LLMUnavailableError, LocalLLMClient


# Keyword -> profile key. First match against a field's label wins.
PROFILE_FIELD_RULES: list[tuple[tuple[str, ...], str]] = [
    (("first name", "given name", "firstname"), "first_name"),
    (("last name", "surname", "family name", "lastname"), "last_name"),
    (("full name", "your name", "legal name", "name"), "name"),
    (("email",), "email"),
    (("phone", "mobile", "telephone", "cell"), "phone"),
    (("linkedin",), "linkedin"),
    (("github",), "github"),
    (("portfolio", "website", "personal site", "url"), "portfolio"),
    (("city", "location", "where are you", "current location"), "location"),
]

# Keyword -> APPLY_DEFAULTS key, for the common required questions.
DEFAULT_QUESTION_RULES: list[tuple[tuple[str, ...], str]] = [
    (("authorized to work", "work authorization", "legally authorized", "right to work"), "work_authorization"),
    (("sponsorship", "require visa", "need visa", "visa sponsor"), "require_sponsorship"),
    (("gender",), "gender"),
    (("race", "ethnicity"), "race"),
    (("veteran", "military"), "veteran"),
    (("disability",), "disability"),
    (("salary", "compensation expectation", "expected pay", "desired salary"), "salary"),
    (("start date", "available to start", "availability", "notice period"), "start_date"),
]


@dataclass
class ApplyResult:
    """Outcome of an auto-apply run."""

    url: str
    filled_fields: list[str] = field(default_factory=list)
    skipped_fields: list[str] = field(default_factory=list)
    llm_answered: list[str] = field(default_factory=list)
    screenshot_path: str = ""
    submitted: bool = False
    error: str = ""


def _profile_value(profile: dict, key: str) -> str:
    """Resolve a profile key, deriving first/last name from full name."""
    if key in ("first_name", "last_name"):
        parts = (profile.get("name") or "").split()
        if not parts:
            return ""
        return parts[0] if key == "first_name" else " ".join(parts[1:]) or parts[0]
    return profile.get(key, "")


def _match_rules(label: str, rules: list) -> str | None:
    """Return the mapped key for the first keyword set found in the label."""
    low = label.lower()
    for keywords, mapped_key in rules:
        if any(kw in low for kw in keywords):
            return mapped_key
    return None


class ApplicationFiller:
    """Fills and (optionally) submits a job application form."""

    def __init__(
        self,
        resume_path: str,
        cover_letter_text: str = "",
        company: str = "",
        role: str = "",
        resume_text: str = "",
        llm_client: LocalLLMClient | None = None,
        profile: dict | None = None,
        auto_submit: bool = AUTO_SUBMIT,
        headless: bool = APPLY_HEADLESS,
    ) -> None:
        self.resume_path = str(Path(resume_path).expanduser().resolve()) if resume_path else ""
        self.cover_letter_text = cover_letter_text
        self.company = company
        self.role = role
        self.resume_text = resume_text
        self.llm_client = llm_client
        self.profile = profile or CANDIDATE_PROFILE
        self.auto_submit = auto_submit
        self.headless = headless
        self.result = ApplyResult(url="")

    # --- public API -----------------------------------------------------
    def apply(self, url: str) -> ApplyResult:
        """Open the URL, fill the form, and screenshot / submit per config."""
        self.result = ApplyResult(url=url)
        try:
            from playwright.sync_api import sync_playwright  # lazy import
        except ImportError:
            self.result.error = (
                "Playwright is not installed. Run:\n"
                "  pip install -r requirements.txt\n"
                "  python -m playwright install chromium"
            )
            return self.result

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=self.headless, slow_mo=APPLY_SLOW_MO_MS)
            page = browser.new_page()
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=60_000)
                page.wait_for_timeout(2_000)  # let JS-rendered forms settle
                self._fill_all_fields(page)
                self.result.screenshot_path = self._screenshot(page)
                if self.auto_submit:
                    self._submit(page)
                else:
                    print(
                        "\nForm filled. AUTO_SUBMIT is off, so nothing was sent.\n"
                        "Review the browser window / screenshot, then submit manually."
                    )
                    if not self.headless:
                        page.wait_for_timeout(120_000)  # hold the window open ~2 min
            except Exception as exc:  # surface, don't crash the whole run
                self.result.error = f"{type(exc).__name__}: {exc}"
                self.result.screenshot_path = self._screenshot(page, suffix="_error")
            finally:
                browser.close()
        return self.result

    # --- field handling -------------------------------------------------
    def _fill_all_fields(self, page) -> None:
        """Iterate every visible form control and fill it."""
        controls = page.query_selector_all("input, textarea, select")
        for control in controls:
            try:
                self._fill_one(page, control)
            except Exception as exc:
                self.result.skipped_fields.append(f"(error: {exc})")

    def _fill_one(self, page, control) -> None:
        """Fill a single control based on its type and label."""
        if not control.is_visible() or not control.is_enabled():
            return
        tag = (control.evaluate("el => el.tagName") or "").lower()
        input_type = (control.get_attribute("type") or "text").lower()
        label = self._label_for(page, control)

        if input_type in ("hidden", "submit", "button", "image", "reset"):
            return

        if input_type == "file":
            self._handle_file(control, label)
            return
        if tag == "select":
            self._handle_choice(control, label, kind="select")
            return
        if input_type in ("radio", "checkbox"):
            self._handle_choice(control, label, kind=input_type)
            return

        # text-like inputs and textareas
        value = self._value_for_text(label, is_textarea=(tag == "textarea"))
        if value:
            control.fill(value)
            self.result.filled_fields.append(f"{label or input_type} = {value[:40]}")
        elif label:
            self.result.skipped_fields.append(label)

    def _value_for_text(self, label: str, is_textarea: bool) -> str:
        """Resolve a value for a text field or textarea."""
        if not label:
            return ""
        # Known profile fields first.
        profile_key = _match_rules(label, PROFILE_FIELD_RULES)
        if profile_key:
            return _profile_value(self.profile, profile_key)
        # Common canned-answer questions.
        default_key = _match_rules(label, DEFAULT_QUESTION_RULES)
        if default_key:
            return APPLY_DEFAULTS.get(default_key, "")
        # Cover letter textarea.
        if is_textarea and ("cover" in label.lower() or "why" in label.lower()):
            return self.cover_letter_text
        # Anything else free-text: ask the LLM.
        if is_textarea or len(label) > 25:
            return self._llm_answer(label)
        return ""

    def _handle_file(self, control, label: str) -> None:
        """Upload resume (or cover letter) to a file input."""
        low = label.lower()
        if "cover" in low:
            return  # cover letter usually pasted as text, not uploaded
        if self.resume_path and os.path.exists(self.resume_path):
            control.set_input_files(self.resume_path)
            self.result.filled_fields.append(f"resume upload -> {os.path.basename(self.resume_path)}")
        else:
            self.result.skipped_fields.append(f"file upload ({label}) - no resume path")

    def _handle_choice(self, control, label: str, kind: str) -> None:
        """Handle select dropdowns, radios, and checkboxes."""
        default_key = _match_rules(label, DEFAULT_QUESTION_RULES)
        desired = APPLY_DEFAULTS.get(default_key, "") if default_key else ""

        if kind == "select":
            options = control.evaluate(
                "el => Array.from(el.options).map(o => o.label || o.textContent.trim())"
            )
            options = [o for o in options if o and o.strip().lower() not in ("", "select", "select...")]
            choice = desired or (self._llm_choice(label, options) if options else "")
            picked = self._closest_option(choice, options)
            if picked:
                control.select_option(label=picked)
                self.result.filled_fields.append(f"{label} -> {picked}")
            else:
                self.result.skipped_fields.append(f"select: {label}")
            return

        # radio / checkbox: only click when our desired answer matches this option's label
        if desired and self._labels_match(label, desired):
            control.check()
            self.result.filled_fields.append(f"{kind}: {label} (checked)")

    # --- LLM helpers ----------------------------------------------------
    def _llm_answer(self, question: str) -> str:
        """Free-text answer to an application question, grounded in the resume."""
        if not self.llm_client:
            return ""
        system = (
            "You are the job applicant answering an application question. "
            "Answer in first person, truthfully, using only facts present in the resume. "
            "Be concise and specific. Do not invent employers, dates, or numbers."
        )
        prompt = (
            f"Company: {self.company}\nRole: {self.role}\n\n"
            f"Resume:\n{self.resume_text[:6000]}\n\n"
            f"Application question: {question}\n\n"
            "Answer (2-4 sentences, no preamble):"
        )
        try:
            answer = self.llm_client.generate(prompt=prompt, system_prompt=system).strip()
            self.result.llm_answered.append(question[:60])
            return answer
        except LLMUnavailableError:
            return ""

    def _llm_choice(self, question: str, options: list[str]) -> str:
        """Pick exactly one option for a dropdown using the LLM."""
        if not self.llm_client or not options:
            return ""
        system = "You select the single best application-form answer. Reply with ONLY the option text, nothing else."
        prompt = (
            f"Resume:\n{self.resume_text[:3000]}\n\n"
            f"Question: {question}\nOptions: {options}\n\n"
            "Reply with exactly one option from the list:"
        )
        try:
            return self.llm_client.generate(prompt=prompt, system_prompt=system).strip()
        except LLMUnavailableError:
            return ""

    # --- small utilities ------------------------------------------------
    def _label_for(self, page, control) -> str:
        """Best-effort human label for a control."""
        for attr in ("aria-label", "placeholder", "name"):
            val = control.get_attribute(attr)
            if val and len(val.strip()) > 1:
                return val.strip()
        control_id = control.get_attribute("id")
        if control_id:
            lbl = page.query_selector(f'label[for="{control_id}"]')
            if lbl:
                text = (lbl.text_content() or "").strip()
                if text:
                    return text
        # Fall back to an ancestor label/text.
        try:
            text = control.evaluate(
                "el => { const l = el.closest('label'); return l ? l.textContent.trim() : ''; }"
            )
            return (text or "").strip()
        except Exception:
            return ""

    @staticmethod
    def _labels_match(a: str, b: str) -> bool:
        norm = lambda s: re.sub(r"[^a-z0-9]", "", s.lower())
        return norm(a) == norm(b) or norm(b) in norm(a) or norm(a) in norm(b)

    @staticmethod
    def _closest_option(choice: str, options: list[str]) -> str:
        """Match an LLM/default answer to one of the real option strings."""
        if not choice or not options:
            return ""
        low = choice.lower().strip()
        for opt in options:
            if opt.lower().strip() == low:
                return opt
        for opt in options:
            if low in opt.lower() or opt.lower() in low:
                return opt
        return ""

    def _screenshot(self, page, suffix: str = "") -> str:
        """Save a full-page screenshot for review/audit."""
        os.makedirs(APPLY_SCREENSHOT_DIR, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        slug = re.sub(r"[^a-z0-9]+", "_", (self.company or "application").lower())[:30]
        path = os.path.join(APPLY_SCREENSHOT_DIR, f"{slug}_{stamp}{suffix}.png")
        try:
            page.screenshot(path=path, full_page=True)
        except Exception:
            return ""
        return path

    def _submit(self, page) -> None:
        """Click a submit button (best effort across common ATS markup)."""
        selectors = [
            "button[type=submit]",
            "input[type=submit]",
            "button:has-text('Submit Application')",
            "button:has-text('Submit application')",
            "button:has-text('Submit')",
            "button:has-text('Apply')",
        ]
        for selector in selectors:
            try:
                btn = page.query_selector(selector)
                if btn and btn.is_visible() and btn.is_enabled():
                    btn.click()
                    page.wait_for_timeout(4_000)
                    self.result.submitted = True
                    self.result.screenshot_path = self._screenshot(page, suffix="_submitted")
                    return
            except Exception:
                continue
        self.result.error = "Could not find a submit button to click."


def auto_apply(
    url: str,
    resume_path: str,
    cover_letter_path: str = "",
    company: str = "",
    role: str = "",
    auto_submit: bool | None = None,
) -> ApplyResult:
    """High-level helper: load inputs, then fill (and optionally submit) the form."""
    resume_text = load_document_text(resume_path) if resume_path else ""
    cover_letter_text = ""
    if cover_letter_path and os.path.exists(cover_letter_path):
        cover_letter_text = Path(cover_letter_path).read_text(encoding="utf-8", errors="ignore")

    llm = LocalLLMClient()
    llm_ok, _ = llm.check_health()

    filler = ApplicationFiller(
        resume_path=resume_path,
        cover_letter_text=cover_letter_text,
        company=company,
        role=role,
        resume_text=resume_text,
        llm_client=llm if llm_ok else None,
        auto_submit=AUTO_SUBMIT if auto_submit is None else auto_submit,
    )
    return filler.apply(url)


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments for the auto-apply tool."""
    parser = argparse.ArgumentParser(description="Auto-fill (and optionally submit) a job application.")
    parser.add_argument("--url", required=True, help="Application page URL")
    parser.add_argument("--resume-file", default=APPLY_RESUME_FILE, help="Resume to upload")
    parser.add_argument("--cover-letter-file", default="", help="Cover letter .md/.txt to paste")
    parser.add_argument("--company", default="", help="Company name (for LLM context)")
    parser.add_argument("--role", default="", help="Role title (for LLM context)")
    parser.add_argument(
        "--submit",
        action="store_true",
        help="Actually click submit (overrides AUTO_SUBMIT). Off = fill + screenshot only.",
    )
    return parser.parse_args()


def main() -> None:
    """Run the auto-apply tool from the command line."""
    args = parse_args()
    if not args.resume_file:
        raise SystemExit("No resume provided. Pass --resume-file or set APPLY_RESUME_FILE in .env.")

    result = auto_apply(
        url=args.url,
        resume_path=args.resume_file,
        cover_letter_path=args.cover_letter_file,
        company=args.company,
        role=args.role,
        auto_submit=True if args.submit else None,
    )

    print("\n=== Auto-apply summary ===")
    print(f"URL: {result.url}")
    print(f"Filled fields ({len(result.filled_fields)}):")
    for item in result.filled_fields:
        print(f"  - {item}")
    if result.skipped_fields:
        print(f"Skipped / needs attention ({len(result.skipped_fields)}):")
        for item in result.skipped_fields:
            print(f"  - {item}")
    if result.llm_answered:
        print(f"LLM-answered questions: {', '.join(result.llm_answered)}")
    if result.screenshot_path:
        print(f"Screenshot: {result.screenshot_path}")
    print(f"Submitted: {result.submitted}")
    if result.error:
        print(f"Error: {result.error}")
    if not result.submitted and not result.error:
        print("\nReview the screenshot above. Re-run with --submit (or set AUTO_SUBMIT=true) to send.")


if __name__ == "__main__":
    main()
