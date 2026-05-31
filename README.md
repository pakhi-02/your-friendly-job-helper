# Local LLM Resume Tailor + Cover Letter Writer

This project is now LLM-based using local inference with Ollama.

Give it:
- your resume (`.txt`, `.md`, `.pdf`, or `.docx`)
- a job description (`.txt`, `.md`, `.pdf`, or `.docx`)

It generates:
- tailored resume notes (`.md`)
- a tailored cover letter draft (`.md`)
- fit analysis output (`.json`)

## Features

- LLM-first writing flow for resume tailoring and cover letters
- Local model support through Ollama (no paid API required)
- PDF and DOCX parsing support
- Heuristic fallback if Ollama is unavailable
- Tone control for cover letters (`formal`, `concise`, `startup`)
- Length control for cover letters (`short`, `medium`, `long`)
- Local web interface for browser-based use
- Dark-themed UI with recent-generation history panel
- CLI mode and interactive mode

## Quick Start

### 1) Install dependencies

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2) Install and run Ollama

Install Ollama: [https://ollama.com/download](https://ollama.com/download)

Run Ollama server:

```bash
ollama serve
```

Pull a model (in another terminal):

```bash
ollama pull llama3.2:3b
```

### 3) Configure environment

```bash
cp .env.example .env
```

Example `.env`:

```env
CANDIDATE_NAME=Your Name
CANDIDATE_EMAIL=you@example.com
CANDIDATE_PHONE=+1-000-000-0000
CANDIDATE_LOCATION=City, Country
CANDIDATE_LINKEDIN=https://linkedin.com/in/your-profile
CANDIDATE_PORTFOLIO=https://your-portfolio.dev

OUTPUT_DIR=application_docs
TOP_KEYWORDS=20
MIN_KEYWORD_LENGTH=3
MAX_INPUT_CHARS=12000

USE_LLM=true
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2:3b
LLM_TIMEOUT_SECONDS=120
LLM_TEMPERATURE=0.3
COVER_LETTER_TONE=formal
COVER_LETTER_LENGTH=medium
```

### 4) Run in CLI mode

```bash
python main.py \
  --resume-file resume.pdf \
  --job-file job_description.docx \
  --company "Acme Inc" \
  --role "Software Engineer" \
  --tone startup \
  --length short
```

### 5) Run in interactive mode

```bash
python main_simple.py
```

Tone options:
- `formal` (default)
- `concise`
- `startup`

Length options:
- `short`
- `medium` (default)
- `long`

### 6) Run web interface

```bash
python web_app.py
```

Then open [http://127.0.0.1:5000](http://127.0.0.1:5000).
After generation, use the in-page download links to save notes, cover letter, and analysis.

### 7) Auto-apply to a job (browser automation)

After generating your tailored resume + cover letter, the tool can open a job's
application page, fill the form, and (optionally) submit it for you.

Install the browser engine once:

```bash
python -m playwright install chromium
```

Fill the form and stop for review (safe default — nothing is submitted):

```bash
python auto_apply.py \
  --url "https://boards.greenhouse.io/acme/jobs/123456" \
  --resume-file resume.pdf \
  --cover-letter-file application_docs/cover_letter_acme_software_engineer_*.md \
  --company "Acme Inc" \
  --role "Software Engineer"
```

The browser opens, fields get filled from your `.env` profile, free-text and
multiple-choice questions are answered by the local LLM (grounded in your
resume), and a screenshot is saved under `application_docs/screenshots/`. It then
pauses so you can verify and click **Submit** yourself.

To submit automatically, either pass `--submit` or set `AUTO_SUBMIT=true` in `.env`.

**Generate and apply in one command** — add `--apply-url` to the normal generate command:

```bash
python main.py \
  --resume-file resume.pdf --job-file job_description.docx \
  --company "Acme Inc" --role "Software Engineer" \
  --apply-url "https://boards.greenhouse.io/acme/jobs/123456"
```

It generates the tailored docs, then auto-fills the application with the
just-generated cover letter. Add `--submit` to also send it.

**From the web app:** after generating documents, an **Auto-Apply** panel appears
in the result card. Paste the application URL and click Auto-Apply (tick the
checkbox to submit automatically). It reuses your uploaded resume and generated
cover letter.

**How it targets "everywhere":** instead of hard-coded selectors per site, it
introspects every visible form field, reads each field's label, and maps it to
your profile (name/email/phone/resume), canned answers (work authorization,
sponsorship, EEO), or the LLM (everything else). It works best on structured ATS
forms (Greenhouse, Lever, Ashby); arbitrary career pages are best-effort.

> ⚠️ **Read before enabling AUTO_SUBMIT.** A small local model can produce a
> wrong answer, and a submitted application can't be recalled. Keep
> `AUTO_SUBMIT=false` for your first runs and review each filled form. Also note
> that LinkedIn, Indeed, and similar sites prohibit automated applications in
> their Terms of Service and may suspend accounts — this tool is most appropriate
> on company/ATS application pages.

## Run with Docker

The stack runs as two containers: the web app (with Chromium baked in for
auto-apply) and a local Ollama model server.

```bash
# 1) Configure (optional but recommended)
cp .env.example .env   # edit your candidate profile + answers

# 2) Build and start
docker compose up --build -d

# 3) Pull a model into the Ollama container (one time)
docker compose exec ollama ollama pull llama3.2:3b

# 4) Open the app
open http://localhost:5000
```

Notes:
- The app reaches Ollama at `http://ollama:11434` inside the compose network —
  this is set automatically, so don't point `OLLAMA_BASE_URL` at `localhost` in `.env`.
- `APPLY_HEADLESS` is forced to `true` in the container (no display available).
- Generated docs and screenshots are persisted to `./application_docs` on the host.
- The web server runs under gunicorn bound to `0.0.0.0:5000`, ready to host.

Stop the stack with `docker compose down` (add `-v` to also drop the model volume).

### Hosting later

When you deploy this, **set `APP_PASSWORD`** in your `.env` to turn on the
built-in HTTP Basic Auth login (leave it empty only for localhost). The included
**Caddy** service gives you automatic HTTPS: set `DOMAIN` to your real domain
(DNS pointed at the host) and `ACME_EMAIL`, then `docker compose up -d` — Caddy
fetches a Let's Encrypt cert for you. Ollama is CPU-only in Docker unless the
host has a configured GPU runtime, so expect slower generation on a plain VM.

A GitHub Actions workflow (`.github/workflows/docker-publish.yml`) builds and
pushes the image to GitHub Container Registry on every push to `main` and on
version tags. See `commands.md` for the full command list.

## Output

Files are generated under `application_docs/` (or your `OUTPUT_DIR`):
- `tailored_resume_notes_*.md`
- `cover_letter_*.md`
- `fit_analysis_*.json`

The CLI also prints:
- `Generation mode: llm` when Ollama is reachable
- `Generation mode: fallback` when it is not
- Selected cover letter tone
- Selected cover letter length


## Notes

- Quality depends on the local model you use.
- Always review and personalize generated text before applying.
- If Ollama is down, fallback mode still produces usable drafts.


#vibe coding to save time
